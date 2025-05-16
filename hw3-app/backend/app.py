import os
from datetime import datetime, timedelta

import requests
from authlib.common.security import generate_token
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
from flask import (
    Flask, jsonify, redirect, send_from_directory,
    session, url_for
)
from flask_cors import CORS

load_dotenv()                                      
app = Flask(__name__,
            static_folder="static",           
            template_folder="templates")          
app.secret_key = os.getenv("FLASK_SECRET",
                            os.urandom(24))       

CORS(app, resources={r"/*": {"origins": [
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]}})

oauth = OAuth(app)
OAUTH_CLIENT_NAME = os.getenv("OIDC_CLIENT_NAME", "dex")

oauth.register(
    name=OAUTH_CLIENT_NAME,
    client_id=os.getenv("OIDC_CLIENT_ID"),
    client_secret=os.getenv("OIDC_CLIENT_SECRET"),
    authorization_endpoint=os.getenv(
        "OIDC_AUTHORIZATION_ENDPOINT", "http://localhost:5556/auth"),
    token_endpoint=os.getenv(
        "OIDC_TOKEN_ENDPOINT", "http://dex:5556/token"),
    jwks_uri=os.getenv(
        "OIDC_JWKS_URI", "http://dex:5556/keys"),
    userinfo_endpoint=os.getenv(
        "OIDC_USERINFO_ENDPOINT", "http://dex:5556/userinfo"),
    device_authorization_endpoint=os.getenv(
        "OIDC_DEVICE_ENDPOINT", "http://dex:5556/device/code"),
    client_kwargs={"scope": "openid email profile"},
)

_nonce = generate_token()

def _client():
    """Return the configured OAuth client."""
    return getattr(oauth, OAUTH_CLIENT_NAME)

@app.route("/api/key")
def get_key():
    """Provide the NYT key to the front end (dev convenience)."""
    return jsonify({"apiKey": os.getenv("NYT_API_KEY")})

@app.route("/api/local-news")
def get_local_news():
    """Proxy NYT Article Search API for Davis/Sacramento stories."""
    api_key = os.getenv("NYT_API_KEY")
    if not api_key:
        return jsonify({"error": "API key not found"}), 500

    end_date = datetime.now().strftime("%Y%m%d")
    begin_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")

    params = {
        "q": "Sacramento (Calif) OR Davis (Calif)",
        "api-key": api_key,
        "begin_date": begin_date,
        "end_date": end_date,
    }

    try:
        resp = requests.get(
            "https://api.nytimes.com/svc/search/v2/articlesearch.json",
            params=params,
            timeout=10,
        )
        resp.raise_for_status()
        return jsonify(resp.json())
    except requests.RequestException as exc:
        return jsonify({"error": str(exc)}), 500

@app.route("/login")
def login():
    """Start Dex login and redirect back to /authorize."""
    session["nonce"] = _nonce
    redirect_uri = url_for("authorize", _external=True)
    return _client().authorize_redirect(redirect_uri, nonce=_nonce)

@app.route("/authorize")
def authorize():
    """OAuth2 callback – store user info in session."""
    token = _client().authorize_access_token()
    user_info = _client().parse_id_token(token, nonce=session.get("nonce"))
    session["user"] = user_info
    return redirect("/") 

@app.route("/logout")
def logout():
    """Clear session and return to SPA."""
    session.clear()
    return redirect("/")

@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str):
    """
    In prod: serve compiled Svelte assets.

    In dev: this route is rarely hit because the SPA is on Vite’s
    http://localhost:5173, but keeping it here lets prod work with one command
    (`docker-compose.prod.yml up`).
    """
    if path and os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)

    return send_from_directory(app.template_folder, "index.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0",
            port=int(os.environ.get("PORT", 8000)),
            debug=bool(os.environ.get("FLASK_DEBUG", "1")))
