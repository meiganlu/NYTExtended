from flask import Flask, redirect, url_for, session, jsonify, send_from_directory
from authlib.integrations.flask_client import OAuth
from authlib.common.security import generate_token
import os
import requests
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = os.urandom(24)

oauth = OAuth(app)

nonce = generate_token()

load_dotenv() 

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app, resources={r"/*": {"origins": ["http://localhost:5173", "http://127.0.0.1:5173"]}})

oauth.register(
    name=os.getenv('OIDC_CLIENT_NAME'),
    client_id=os.getenv('OIDC_CLIENT_ID'),
    client_secret=os.getenv('OIDC_CLIENT_SECRET'),
    #server_metadata_url='http://dex:5556/.well-known/openid-configuration',
    authorization_endpoint="http://localhost:5556/auth",
    token_endpoint="http://dex:5556/token",
    jwks_uri="http://dex:5556/keys",
    userinfo_endpoint="http://dex:5556/userinfo",
    device_authorization_endpoint="http://dex:5556/device/code",
    client_kwargs={'scope': 'openid email profile'}
)

@app.route("/api/key")
def get_key():
    return jsonify({"apiKey": os.getenv("NYT_API_KEY")})

@app.route("/api/local-news")
def get_local_news():
    api_key = os.getenv("NYT_API_KEY")
    if not api_key:
        return jsonify({"error": "API key not found"}), 500

    end_date = datetime.now().strftime('%Y%m%d')
    begin_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')  # Date up to 1 yr ago

    url = "https://api.nytimes.com/svc/search/v2/articlesearch.json"
    params = {
        "q": "Sacramento (Calif) OR Davis (Calif)",
        "api-key": api_key,
        "begin_date": begin_date,
        "end_date": end_date,
    }

    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return jsonify(response.json())
    except requests.RequestException as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def home():
    user = session.get('user')
    if user:
        return f"<h2>Logged in as {user['email']}</h2><a href='/logout'>Logout</a>"
    return '<a href="/login">Login with Dex</a>'

@app.route('/login')
def login():
    session['nonce'] = nonce
    redirect_uri = 'http://localhost:8000/authorize'
    return oauth.flask_app.authorize_redirect(redirect_uri, nonce=nonce)

@app.route('/authorize')
def authorize():
    token = oauth.flask_app.authorize_access_token()
    nonce = session.get('nonce')

    user_info = oauth.flask_app.parse_id_token(token, nonce=nonce)  # or use .get('userinfo').json()
    session['user'] = user_info
    return redirect('/')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

@app.route("/<path:path>")
def serve_frontend(path=""):
    if path != "" and os.path.exists(f"static/{path}"):
        return send_from_directory("static", path)
    return send_from_directory("templates", "index.html")


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
