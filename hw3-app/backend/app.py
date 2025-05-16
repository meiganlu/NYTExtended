"""
backend/app.py  – Flask + Dex OIDC + NYT + comments
---------------------------------------------------
* NY Times endpoint SAME AS BEFORE; nothing that could break article loading
* Dex host split:
      BROWSER  →  http://localhost:5556
      BACKEND  →  http://dex:5556   (Docker service name)
Docker-compose must expose “dex:5556:5556”.
"""

import os, datetime, requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request, redirect, session, send_from_directory
from flask_cors import CORS
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
from pymongo import MongoClient
from bson.objectid import ObjectId

load_dotenv()

# ─────────── Flask / CORS ───────────────────────────────────────────────
app = Flask(__name__, static_folder="static", template_folder="templates")
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret")
CORS(app, supports_credentials=True,
     resources={r"/*": {"origins": [
         "http://localhost:5173", "http://127.0.0.1:5173"]}})

# ─────────── Mongo (comments) ───────────────────────────────────────────
mongo      = MongoClient(os.getenv("MONGO_URL", "mongodb://mongo:27017"))
comments   = mongo.hw3.comments

# ─────────── OAuth / Dex (split hosts) ─────────────────────────────────
oauth = OAuth(app)

DEX_INTERNAL = "http://dex:5556"        # used by backend inside containers
DEX_BROWSER  = "http://localhost:5556"  # used by browser

oauth.register(
    name="dex",
    client_id="flask-app",
    client_secret="flask-secret",
    authorize_url      = f"{DEX_BROWSER}/auth",     # browser
    access_token_url   = f"{DEX_INTERNAL}/token",   # backend
    userinfo_endpoint  = f"{DEX_INTERNAL}/userinfo",
    jwks_uri           = f"{DEX_INTERNAL}/keys",
    api_base_url       = DEX_INTERNAL,
    client_kwargs      = {"scope": "openid email profile"},
)

nonce = generate_token()

# ─────────── NY Times article-search API (unchanged) ───────────────────
@app.get("/api/local-news")
def local_news():
    api_key = os.getenv("NYT_API_KEY")
    if not api_key:
        return jsonify({"error": "NYT_API_KEY missing"}), 500

    end   = datetime.datetime.now()
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
        return jsonify({"error": str(exc)}), 502

# ─────────── Comment API (same as before) ──────────────────────────────
def tree(flat):
    lookup = {str(c["_id"]): {**c, "id": str(c["_id"]), "children": []} for c in flat}
    root   = []
    for c in lookup.values():
        pid = c.get("parent_id")
        (lookup[pid]["children"] if pid in lookup else root).append(c)
    return root

@app.get("/api/comments/<path:aid>")
def get_comments(aid):
    return jsonify(tree(list(comments.find({"article_id": aid}))))

@app.post("/api/comments/<path:aid>")
def post_comment(aid):
    if "user" not in session:
        return "", 401
    body = request.get_json(force=True) or {}
    txt  = body.get("content", "").strip()
    if not txt:
        return "", 400
    comments.insert_one({
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
    comments.delete_one({
        "_id": ObjectId(cid),
        "user_name": session["user"]["email"]
    })
    return "", 204

# ─────────── OIDC flow ────────────────────────────────────────────────
@app.get("/login")
def login():
    session["nonce"] = nonce
    return oauth.dex.authorize_redirect(
        redirect_uri="http://localhost:8000/authorize",
        nonce=nonce
    )

@app.get("/authorize")
def authorize():
    token = oauth.dex.authorize_access_token()
    info  = oauth.dex.parse_id_token(token, nonce=session.pop("nonce"))
    session["user"] = info
    # hand e-mail back to SPA
    return redirect(f"http://localhost:5173?user={info['email']}")

@app.get("/logout")
def logout():
    session.clear()
    return redirect("http://localhost:5173")

# ─────────── SPA static files (for production) ────────────────────────
@app.get("/")
@app.get("/<path:path>")
def spa(path=""):
    if path and os.path.exists(f"static/{path}"):
        return send_from_directory("static", path)
    return send_from_directory("templates", "index.html")

# ─────────── run ──────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 8000)), debug=True)
