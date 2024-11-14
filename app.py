import secrets
import os
from PIL import Image
from flask import Flask, render_template, redirect, request, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from forms import AddUser, RegisterForm, LoginForm
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin , login_user, current_user ,logout_user
from flask_migrate import Migrate
from flask_session import Session

app=Flask(__name__)

app.config['SECRET_KEY']= 'mysecretkey'
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Omni3255??!!@localhost/thedb'
# app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://root:pSdtXdRTeLmfeHpJohajWCRAEWEHskmc@mysql.railway.internal:3306/railway"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT']= True
app.config['PERMANENT_SESSION_LIFETIME']= 1800


app.app_context().push()
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view='login'
migrate = Migrate(app, db)

app_session = Session(app)



@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

    

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False, unique=True)
    email = db.Column(db.String(120), nullable=False, unique=True)
    password = db.Column(db.String(100), nullable=False)
    image_file = db.Column(db.String(100), nullable=False, default='default.jpg')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"




@app.before_request
def before_request():
    # Ensure the session user_id is used to manage session state
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user and not current_user.is_authenticated:
            login_user(user)




# @app.route("/")
# def home():
#     page = request.args.get('page', 1, type=int)
#     users = User.query.paginate(page=page, per_page=2)
#     return render_template('home.html', users=users)

@app.route("/")
def home():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=2)
    current_user = None
    if 'user_id' in session:
        current_user = User.query.get(session['user_id'])
    return render_template('home.html', users=users, current_user=current_user)




def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _,p_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + p_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    output_size = (150,150)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


@app.route("/add_user", methods=['GET', 'POST'])
def add_user():
    form=AddUser()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            main_picture=picture_file
        else:
            main_picture='default.jpg'
        user = User(username=form.username.data, email=form.email.data, image_file=main_picture)
        db.session.add(user)
        db.session.commit()
        flash('You have been added', 'success')
        return redirect(url_for('home'))
    return render_template('add_user.html', title='Add user', form=form)

@app.route("/update_user/<int:user_id>", methods=['GET', 'POST'])
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    form = AddUser()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            main_picture=picture_file
        else:
            main_picture= 'default.jpg'
        user.username = form.username.data
        user.email=form.email.data
        user.image_file=main_picture
        db.session.commit()
        flash('Your updates have been made')
        return redirect(url_for('home', user_id=user.id))
        
    elif request.method=='GET':
        form.username.data = user.username
        form.email.data = user.email
    return render_template('add_user.html', title='Update User', form=form)



@app.route("/delete_user/<int:user_id>", methods=['POST'])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    return redirect(url_for('home', user_id=user.id))



# @app.route("/register", methods=['GET', 'POST'])
# def register():
#     if current_user.is_authenticated:
#         return redirect(url_for('home'))
#     form=RegisterForm()
#     if form.validate_on_submit():
#         hashed_password = bcrpt.generate_password_hash(form.password.data).decode('utf-8')
#         user = User(username=form.username.data, email=form.email.data, password=hashed_password)
#         db.session.add(user)
#         db.session.commit()
#         flash('You have been registered successfully')
#         return redirect(url_for('login'))
#     return render_template('register.html', form=form)



@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('You have been registered successfully!')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


# @app.route("/login", methods=['GET', 'POST'])
# def login():
#     if current_user.is_authenticated:
#         return redirect(url_for('home'))
#     form=LoginForm()
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#         if user and bcrpt.check_password_hash(user.password, form.password.data):
#             login_user(user)
#             session.permanent = True
#             session.modified = True
#             # session['username'] = user.username
#             return redirect(url_for('home'))
#         else:
#             flash('Incorrect login credentials please check email and password')
#     return render_template('login.html', title='Login', form=form)



@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            session['user_id'] = user.id  # Set user ID in session
            session.modified = True  # Ensure session saves the modification
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Incorrect login credentials. Please check email and password.')
    return render_template('login.html', form=form)



@app.route("/logout", methods=['GET', 'POST'])
def logout():
    session.pop('user_id', None)
    logout_user()
    # session.clear()
    return redirect(url_for('home'))




if __name__=="__main__":
    app.run(debug=True)