import os
import random
from flask import render_template, url_for, flash, redirect, request, session
from app import app, db, bcrypt
from app.models import User, Post, Material, NKValues
from app.forms import RegistrationForm, LoginForm, PostForm, UploadForm, SimulatorForm
from flask_login import login_user, current_user, logout_user, login_required
from werkzeug.utils import secure_filename
import pandas as pd


@app.route("/")
@app.route("/home")
# @login_required
def home():
    posts = Post.query.all()
    return render_template('home.html', posts=posts)

@app.route("/about")
@login_required
def about():
    return render_template('about.html')

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'your theospec profile has been created! You are now logged in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            flash(f'Welcome! Check out the Simulator dashboard.', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
def logout():
    logout_user()
    flash(f"You've beeen logged out.", 'success')
    return redirect(url_for('home'))

@app.route("/account")
@login_required
def account():
    return render_template('account.html', title='Account')

@app.route("/post/new", methods=['GET', 'POST'])
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('Your post has been created!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form)


@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    form = UploadForm()
    if form.validate_on_submit():
        material = Material(name=form.material.data)
        db.session.add(material)
        db.session.commit()
        file = form.file.data
        filename = secure_filename(file.filename)
        file.save(os.path.join('uploads', filename))
        df = pd.read_csv(os.path.join('uploads', filename), 
                        sep="\t", names=['wavelength', 'n_value', 'k_value'])
        df.to_csv('uploads/test.csv')
        for row in df.iterrows():
            data = row[1]
            nk_values = NKValues(wavelength=data.wavelength, 
                                n_value=data.n_value, 
                                k_value=data.k_value, 
                                material_id = material.id)
            db.session.add(nk_values)
        db.session.commit()
        flash("Upload successful!", "success")
        return redirect(url_for('home'))
    return render_template('upload.html', form=form)

@app.route("/simulator", methods=['GET', 'POST'])
@login_required
def simulator():
    # form = SimulatorForm()
    # if form.validate_on_submit():
    #     # store input data in cookie
    #     session['medium'] = form.medium.data
    #     session['active_layers'] = form.active_layers.data
    #     session['trench_layers'] = form.trench_layers.data
    #     # decimal cant serialize, thus changing to string
    #     session['pattern_density'] = str(form.pattern_density.data)
    return redirect(url_for('/data/'))
    # return render_template('simulator.html', form=form)

@app.route('/simulator/dashboard', methods=['GET', 'POST'])
def test():
    medium = session['medium']
    active_layers = session['active_layers']
    trench_layers = session['trench_layers']
    pattern_density = float(session['pattern_density'])
    return str([medium, active_layers, trench_layers, pattern_density])
