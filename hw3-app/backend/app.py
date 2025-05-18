"""
backend/app.py  –  Dex OIDC • Mongo comments • NYT cache
────────────────────────────────────────────────────────
Changes in this version
───────────────────────
✓ Uses authenticated Mongo connection (reads MONGO_* env-vars)
✓ Still returns the same JSON and keeps every route & Dex flow
✓ 30-minute NY Times in-memory cache unchanged
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

load_dotenv()

# ─────────────── Flask / CORS ───────────────
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret")
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
    lookup = {str(c["_id"]): {**c, "id": str(c["_id"]), "children": []} for c in flat}
    root = []
    for c in lookup.values():
        pid = c.get("parent_id")
        (lookup[pid]["children"] if pid in lookup else root).append(c)
    return root


@app.get("/api/comments/<path:aid>")
def get_comments(aid):
    return jsonify(build_tree(list(comments_col.find({"article_id": aid}))))


@app.post("/api/comments/<path:aid>")
def post_comment(aid):
    if "user" not in session:
        return "", 401
    body = request.get_json(force=True) or {}
    txt  = body.get("content", "").strip()
    if not txt:
        return "", 400
    comments_col.insert_one({
        "article_id": aid,
        "content":    txt,
        "parent_id":  body.get("parent_id"),
        "user_name":  session["user"]["email"],
        "created_at": datetime.datetime.utcnow()
    })
    return "", 201


@app.delete("/api/comments/<cid>")
def delete_comment(cid):
    if "user" not in session:
        return "", 401
    comments_col.delete_one({
        "_id": ObjectId(cid),
        "user_name": session["user"]["email"]
    })
    return "", 204


# ----- OIDC flow -----
@app.get("/login")
def login():
    session["nonce"] = generate_token()
    return oauth.dex.authorize_redirect(
        redirect_uri="http://localhost:8000/authorize",
        nonce=session["nonce"]
    )


@app.get("/authorize")
def authorize():
    token = oauth.dex.authorize_access_token()
    info  = oauth.dex.parse_id_token(token, nonce=session.pop("nonce"))
    session["user"] = info
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
