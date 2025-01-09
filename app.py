from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from forms import RegistrationForm, LoginForm, ContentForm
from models import db, User, Content
import os
from flask_migrate import Migrate
from config import Config
import secrets
from PIL import Image

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

migrate = Migrate(app, db)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route("/")
@app.route("/index")
def index():
    contents = Content.query.order_by(Content.id.desc()).limit(4).all()
    return render_template('index.html', contents=contents)

@app.route("/math")
def math():
    math_contents = Content.query.filter_by(category='Math').all()
    return render_template('math.html', math_contents=math_contents)

@app.route("/physics")
def physics():
    physics_contents = Content.query.filter_by(category='Physics').all()
    return render_template('physics.html', physics_contents=physics_contents)

@app.route("/about")
def about():
    return render_template('about.html')

@app.route("/contact")
def contact():
    return render_template('contact.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            flash('You have been logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', form=form)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route("/add_content", methods=['GET', 'POST'])
@login_required
def add_content():
    form = ContentForm()
    if form.validate_on_submit():
        if form.image.data:
            picture_file = save_picture(form.image.data)
        else:
            picture_file = 'default.jpg'
        content = Content(
            title=form.title.data,
            body=form.body.data,
            category=form.category.data,
            image_file=picture_file,
            author=current_user
        )
        db.session.add(content)
        db.session.commit()
        flash('Content added successfully!', 'success')
        return redirect(url_for(form.category.data.lower()))
    return render_template('add_content.html', form=form)

@app.route("/content/<int:content_id>")
def content_detail(content_id):
    content = Content.query.get_or_404(content_id)
    return render_template('content_detail.html', content=content)

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/content_pics', picture_fn)
    
    output_size = (500, 500)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    
    return picture_fn

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)