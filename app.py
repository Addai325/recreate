import secrets
import os
from PIL import Image
from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from forms import AddUser, RegisterForm, LoginForm
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from flask_migrate import Migrate

app = Flask(__name__)

# Configuration
app.config['SECRET_KEY'] = 'mysecretkey'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'

app.config['SQLALCHEMY_DATABASE_URI'] = 'amysql+pymysql://Addai325:Extra111??!!@Addai325.mysql.pythonanywhere-services.com/Addai325$omniblogs'


# Initialize extensions
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'  # Redirect unauthenticated users to the login page
migrate = Migrate(app, db)

# Load user callback function for Flask-Login
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))  # Ensures user_id is an integer

# User Model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    image_file = db.Column(db.String(100), nullable=False, default='default.jpg')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, p_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + p_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    output_size = (150, 150)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

@app.route("/")
def home():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=2)
    return render_template('home.html', users=users)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('You have been registered successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('Login successful!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('home'))
        else:
            flash('Incorrect login credentials. Please check email and password.', 'danger')
    return render_template('login.html', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()  # End the session for the current user
    session.clear()  # Explicitly clear the session data from the client-side
    flash('You have been logged out.', 'info')
    return redirect(url_for('home'))

# Protected route example
@app.route("/add_user", methods=['GET', 'POST'])
@login_required
def add_user():
    form = AddUser()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            main_picture = picture_file
        else:
            main_picture = 'default.jpg'
        user = User(username=form.username.data, email=form.email.data, image_file=main_picture)
        db.session.add(user)
        db.session.commit()
        flash('You have been added', 'success')
        return redirect(url_for('home'))
    return render_template('add_user.html', title='Add User', form=form)

@app.route("/update_user/<int:user_id>", methods=['GET', 'POST'])
@login_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    form = AddUser()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            main_picture = picture_file
        else:
            main_picture = 'default.jpg'
        user.username = form.username.data
        user.email = form.email.data
        user.image_file = main_picture
        db.session.commit()
        flash('Your updates have been made', 'success')
        return redirect(url_for('home', user_id=user.id))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
    return render_template('add_user.html', title='Update User', form=form)

@app.route("/delete_user/<int:user_id>", methods=['POST'])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully', 'success')
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=True)
