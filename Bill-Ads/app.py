from flask import Flask, render_template, redirect, url_for, flash, session
from flask_mail import Mail, Message
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User
from forms import RegistrationForm, LoginForm, OTPForm
import random

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.before_request
def create_tables():
    db.create_all()

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        new_user = User(full_name=form.full_name.data, email=form.email.data,
                        password=hashed_password, business_name=form.business_name.data)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            # Generate OTP
            otp = random.randint(100000, 999999)
            session['otp'] = otp
            session['email'] = user.email
            
            # Send OTP via email
            msg = Message('Your OTP Code', sender=app.config['MAIL_USERNAME'], recipients=[user.email])
            msg.body = f'Your OTP code is {otp}'
            mail.send(msg)
            
            return redirect(url_for('verify'))
        
        flash('Invalid email or password!')
    return render_template('login.html', form=form)

@app.route('/verify', methods=['GET', 'POST'])
def verify():
    form = OTPForm()
    if form.validate_on_submit():
        if session.get('otp') and session['otp'] == int(form.otp.data):
            user = User.query.filter_by(email=session['email']).first()
            login_user(user)
            flash('Login successful!')
            return redirect(url_for('welcome'))
        
        flash('Invalid OTP!')
    return render_template('verify.html', form=form)

@app.route('/welcome')
@login_required
def welcome():
    return f'Welcome, {current_user.full_name}!'

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
