"""
backend/app.py  –  Dex OIDC • Mongo comments • NYT cache
────────────────────────────────────────────────────────
Changes in this version
───────────────────────
✓ Uses authenticated Mongo connection (reads MONGO_* env-vars)
✓ Still returns the same JSON and keeps every route & Dex flow
✓ 30-minute NY Times in-memory cache unchanged
✓ Handles ObjectId serialization for comment retrieval
✓ Added moderator capabilities for comment deletion
✓ Improved error handling for comment operations
"""

import os, datetime, requests, time
from functools import wraps
from dotenv import load_dotenv
from flask import Flask, jsonify, request, redirect, session, send_from_directory
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import timedelta

load_dotenv()

# ─────────────── Flask / CORS ───────────────
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret")
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(days=7)  # Session lasts 7 days

CORS(app, supports_credentials=True,
     resources={r"/*": {"origins": ["http://localhost:5173",
                                   "http://127.0.0.1:5173"]}})

# ─────────────── Mongo (auth on) ─────────────
mongo_client = MongoClient(
    "mongodb://mongo:27017",
    username=os.getenv("MONGO_USER", "hw3user"),
    password=os.getenv("MONGO_PASS", "hw3pass"),
    authSource=os.getenv("MONGO_AUTH_DB", "hw3"),
)
comments_col = mongo_client.hw3.comments  # same collection name

# ─────────────── Dex / OAuth2  ──────────────
DEX_BROWSER  = "http://localhost:5556"
DEX_INTERNAL = "http://dex:5556"

oauth = OAuth(app)
oauth.register(
    name="dex",
    client_id="flask-app",
    client_secret="flask-secret",
    authorize_url     = f"{DEX_BROWSER}/auth",
    access_token_url  = f"{DEX_INTERNAL}/token",
    userinfo_endpoint = f"{DEX_INTERNAL}/userinfo",
    jwks_uri          = f"{DEX_INTERNAL}/keys",
    api_base_url      = DEX_INTERNAL,
    client_kwargs     = {"scope": "openid email profile"},
)

# ─────────────── NY Times 30-min cache ───────
_cached_nyt = {"data": None, "ts": 0}
CACHE_TTL   = 60 * 30            # seconds


def nyt_cached(fn):
    @wraps(fn)
    def _wrapper():
        now = time.time()
        if _cached_nyt["data"] and now - _cached_nyt["ts"] < CACHE_TTL:
            return jsonify(_cached_nyt["data"])
        resp = fn()
        if resp.status_code == 200:
            _cached_nyt["data"] = resp.get_json()
            _cached_nyt["ts"]   = now
        return resp
    return _wrapper


# ─────────────── Routes ──────────────────────
@app.get("/api/local-news")
@nyt_cached
def local_news():
    api_key = os.getenv("NYT_API_KEY")
    if not api_key:
        return jsonify({"error": "NYT_API_KEY missing"}), 500

    end   = datetime.datetime.utcnow()
    begin = end - datetime.timedelta(days=365)
    params = {
        "q": "Sacramento (Calif) OR Davis (Calif)",
        "api-key": api_key,
        "begin_date": begin.strftime("%Y%m%d"),
        "end_date":   end.strftime("%Y%m%d"),
    }
    try:
        r = requests.get(
            "https://api.nytimes.com/svc/search/v2/articlesearch.json",
            params=params, timeout=10)
        r.raise_for_status()
        return jsonify(r.json())
    except requests.RequestException as exc:
        app.logger.error("NYT fetch failed: %s", exc, exc_info=True)
        return jsonify({"error": "NYT upstream error"}), 502


# ----- comment helpers -----
def build_tree(flat):
    """Build a tree structure from flat comment list with proper ID handling"""
    try:
        # Convert ObjectId to string for JSON serialization
        for c in flat:
            if '_id' in c:
                c['_id'] = str(c['_id'])
        
        # Create lookup dictionary with string IDs
        lookup = {str(c["_id"]): {**c, "id": str(c["_id"]), "children": []} for c in flat}
        root = []
        
        # Build the tree structure
        for c in lookup.values():
            pid = c.get("parent_id")
            if pid and pid in lookup:
                lookup[pid]["children"].append(c)
            else:
                root.append(c)
        
        return root
    except Exception as e:
        app.logger.error(f"Error building comment tree: {e}")
        return []  # Return empty array in case of errors


@app.get("/api/comments/<path:aid>")
def get_comments(aid):
    """Get comments for an article with error handling"""
    try:
        comments = list(comments_col.find({"article_id": aid}))
        return jsonify(build_tree(comments))
    except Exception as e:
        app.logger.error(f"Error retrieving comments for {aid}: {e}")
        return jsonify([]), 200  # Return empty array but don't fail


@app.post("/api/comments/<path:aid>")
def post_comment(aid):
    """Add a new comment to an article"""
    if "user" not in session:
        return "", 401
    
    body = request.get_json(force=True) or {}
    txt  = body.get("content", "").strip()
    if not txt:
        return "", 400
    
    try:
        comments_col.insert_one({
            "article_id": aid,
            "content":    txt,
            "parent_id":  body.get("parent_id"),
            "user_name":  session["user"]["email"],
            "created_at": datetime.datetime.utcnow()
        })
        return "", 201
    except Exception as e:
        app.logger.error(f"Error posting comment: {e}")
        return "", 500


@app.delete("/api/comments/<cid>")
def delete_comment(cid):
    """
    Soft-delete a comment.
    • Only accounts in MODERATORS may do it.
    • The document stays in Mongo so the UI can still render the thread.
    """
    if "user" not in session:
        return "", 401

    MODERATORS = {"moderator@hw3.com"}          # ← extend as you like
    email = session["user"]["email"]

    if email not in MODERATORS:
        return "", 403                           # not allowed

    try:
        result = comments_col.update_one(
            {"_id": ObjectId(cid)},
            {
                "$set": {
                    "content": "comment was removed by moderator",
                    "deleted": True,
                    "deleted_at": datetime.datetime.utcnow(),
                    "deleted_by": email,
                }
            }
        )

        if result.matched_count == 0:            # CID not found
            return "", 404

        return "", 204                           # success, no body
    except Exception as err:
        app.logger.exception("moderator-delete failed")
        return "", 500



# ----- OIDC flow -----
@app.get("/login")
def login():
    session["nonce"] = generate_token()
    session.permanent = True  # Make the session last longer
    return oauth.dex.authorize_redirect(
        redirect_uri="http://localhost:8000/authorize",
        nonce=session["nonce"]
    )


@app.get("/authorize")
def authorize():
    token = oauth.dex.authorize_access_token()
    info  = oauth.dex.parse_id_token(token, nonce=session.pop("nonce"))
    session["user"] = info
    session.permanent = True  # Make the session last longer
    return redirect(f"http://localhost:5173?user={info['email']}")


@app.get("/logout")
def logout():
    session.clear()
    return redirect("http://localhost:5173")


# ----- SPA fall-through (prod build) -----
@app.get("/")
@app.get("/<path:path>")
def spa(path=""):
    if path and os.path.exists(f"static/{path}"):
        return send_from_directory("static", path)
    return send_from_directory("templates", "index.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=True)