from flask import Flask, render_template, redirect, url_for, flash, session, request
from models import db, User, SocialCredential, SocialLink
from config import Config
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from utils import follow_all
from flask_migrate import Migrate
from oauthlib.oauth2 import WebApplicationClient
import requests

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

client = WebApplicationClient(app.config['GOOGLE_CLIENT_ID'])

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login():
    google_provider_cfg = requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()
    authorization_endpoint = google_provider_cfg["authorization_endpoint"]
    request_uri = client.prepare_request_uri(
        authorization_endpoint,
        redirect_uri=request.base_url + "/callback",
        scope=["openid", "email", "profile"],
    )
    return redirect(request_uri)

@app.route('/login/callback')
def callback():
    code = request.args.get("code")
    google_provider_cfg = requests.get(app.config['GOOGLE_DISCOVERY_URL']).json()
    token_endpoint = google_provider_cfg["token_endpoint"]
    token_url, headers, body = client.prepare_token_request(
        token_endpoint,
        authorization_response=request.url,
        redirect_url=request.base_url,
        code=code
    )
    token_response = requests.post(
        token_url,
        headers=headers,
        data=body,
        auth=(app.config['GOOGLE_CLIENT_ID'], app.config['GOOGLE_CLIENT_SECRET']),
    )
    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg["userinfo_endpoint"]
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get("email_verified"):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        users_name = userinfo_response.json()["name"]
    else:
        return "User email not available or not verified by Google.", 400

    user = User.query.filter_by(email=users_email).first()
    if not user:
        user = User(
            username=users_name, email=users_email, social_id=unique_id
        )
        db.session.add(user)
        db.session.commit()

    login_user(user)
    return redirect(url_for("dashboard"))

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    credentials = SocialCredential.query.filter_by(user_id=current_user.id).all()
    links = SocialLink.query.filter_by(user_id=current_user.id).all()
    return render_template('dashboard.html', credentials=credentials, links=links)

@app.route('/add_credential', methods=['POST'])
@login_required
def add_credential():
    platform = request.form['platform']
    username = request.form['username']
    password = request.form['password']
    credential = SocialCredential(
        user_id=current_user.id, platform=platform, username=username, password=password
    )
    db.session.add(credential)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_link', methods=['POST'])
@login_required
def add_link():
    platform = request.form['platform']
    link = request.form['link']
    social_link = SocialLink(
        user_id=current_user.id, platform=platform, link=link
    )
    db.session.add(social_link)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/follow_all')
@login_required
def follow_all_accounts():
    credentials = SocialCredential.query.filter_by(user_id=current_user.id).all()
    links = SocialLink.query.filter_by(user_id=current_user.id).all()
    follow_all(credentials, links)
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
