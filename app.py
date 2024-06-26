#Web Backend for SuperLink



from flask import Flask, render_template, redirect, url_for, flash, session, request
from models import db, User, Business, SocialCredential, SocialLink
from config import Config
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from utils import trigger_zap
from flask_migrate import Migrate
from oauthlib.oauth2 import WebApplicationClient
import requests
import json

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
    businesses = Business.query.all()
    return render_template('dashboard.html', businesses=businesses)

@app.route('/business/<int:business_id>', methods=['GET', 'POST'])
@login_required
def business(business_id):
    business = Business.query.get_or_404(business_id)
    credentials = SocialCredential.query.filter_by(business_id=business.id).all()
    links = SocialLink.query.filter_by(business_id=business.id).all()
    return render_template('business.html', business=business, credentials=credentials, links=links)

@app.route('/add_business', methods=['POST'])
@login_required
def add_business():
    name = request.form['name']
    superlink = request.form['superlink']
    business = Business(
        name=name, superlink=superlink
    )
    db.session.add(business)
    db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/add_credential', methods=['POST'])
@login_required
def add_credential():
    business_id = request.form['business_id']
    platform = request.form['platform']
    username = request.form['username']
    password = request.form['password']
    credential = SocialCredential(
        business_id=business_id, platform=platform, username=username, password=password
    )
    db.session.add(credential)
    db.session.commit()
    return redirect(url_for('business', business_id=business_id))

@app.route('/add_link', methods=['POST'])
@login_required
def add_link():
    business_id = request.form['business_id']
    platform = request.form['platform']
    link = request.form['link']
    social_link = SocialLink(
        business_id=business_id, platform=platform, link=link
    )
    db.session.add(social_link)
    db.session.commit()

    payload = {
        "platform": platform,
        "link": link,
        "business_name": Business.query.get(business_id).name
    }
    status_code, response = trigger_zap(payload)
    if status_code != 200:
        flash('Failed to trigger Zapier automation.', 'danger')

    return redirect(url_for('business', business_id=business_id))

@app.route('/follow/<string:superlink>')
def follow_superlink(superlink):
    business = Business.query.filter_by(superlink=superlink).first_or_404()
    credentials = SocialCredential.query.filter_by(business_id=business.id).all()
    links = SocialLink.query.filter_by(business_id=business.id).all()

    payload = {
        "credentials": [{"platform": c.platform, "username": c.username, "password": c.password} for c in credentials],
        "links": [{"platform": l.platform, "link": l.link} for l in links],
        "user_id": current_user.id
    }
    status_code, response = trigger_zap(payload)
    if status_code != 200:
        flash('Failed to follow all social media accounts.', 'danger')

    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
