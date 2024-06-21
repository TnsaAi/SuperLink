from flask import Flask, render_template, redirect, url_for, flash, session, request
from models import db, User, Profile
from config import Config
from werkzeug.security import generate_password_hash, check_password_hash
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import time

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        hashed_password = generate_password_hash(password, method='sha256')
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('You have successfully registered!', 'success')
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('You have successfully logged in!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        social_media_name = request.form['social_media_name']
        social_media_url = request.form['social_media_url']
        new_profile = Profile(user_id=user.id, social_media_name=social_media_name, social_media_url=social_media_url)
        db.session.add(new_profile)
        db.session.commit()
        flash('Social media link added!', 'success')
    
    profiles = Profile.query.filter_by(user_id=user.id).all()
    return render_template('dashboard.html', profiles=profiles, user=user)

@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return 'User not found', 404
    profiles = Profile.query.filter_by(user_id=user.id).all()
    return render_template('profile.html', profiles=profiles, user=user)

@app.route('/follow/<username>')
def follow(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return 'User not found', 404

    profiles = Profile.query.filter_by(user_id=user.id).all()

    # Set up Selenium
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Ensure GUI is off
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)

    try:
        for profile in profiles:
            driver.get(profile.social_media_url)
            time.sleep(5)  # Adjust sleep time as needed to allow page to load
            
            # This part needs to be customized based on the social media page's structure
            if profile.social_media_name.lower() == 'twitter':
                follow_button = driver.find_element(By.XPATH, '//div[@data-testid="follow"]')
                follow_button.click()
            elif profile.social_media_name.lower() == 'facebook':
                follow_button = driver.find_element(By.XPATH, '//button[contains(text(), "Follow")]')
                follow_button.click()
            # Add more social media platforms as needed
            time.sleep(2)
        
        flash('Successfully followed all social media profiles!', 'success')
    except Exception as e:
        flash(f'Failed to follow social media profiles: {str(e)}', 'danger')
    finally:
        driver.quit()

    return redirect(url_for('profile', username=username))

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have successfully logged out!', 'success')
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
