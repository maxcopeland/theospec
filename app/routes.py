import os
import random
from flask import render_template, url_for, flash, redirect, request
from app import app, db, bcrypt
from app.models import User, Post, Material, NKValues
from app.forms import RegistrationForm, LoginForm, PostForm, UploadForm
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
        flash(f'your account has been created! You are now about the log in', 'success')
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
            flash(f'Welcome!', 'success')
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



from bokeh.embed import server_document
from bokeh.layouts import column
from bokeh.models import ColumnDataSource, Slider
from bokeh.plotting import figure
from bokeh.server.server import Server
from bokeh.themes import Theme
from tornado.ioloop import IOLoop
from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature
from scipy.interpolate import interp1d
from tmm.color import calc_reflectances
import numpy as np



def get_nkvals(mat_name):
    mat_id = Material.query.filter_by(name=mat_name).first().id
    nk_vals = NKValues.query.filter_by(material_id=mat_id).all()
    df = pd.DataFrame([(d.wavelength, d.n_value, d.k_value) for d in nk_vals], 
                  columns=['wavelength', 'n', 'k'])
    df['nk'] = df['n'] + (1j * df['k'])
    ### lazy hack, needs more robust solution
    if df.wavelength.min() > 1000:
        df['wavelength'] = df.wavelength /10
    return df


def modify_doc(doc):
    starting_thk = 2000
    sio_df = get_nkvals('SiO2') ## change to make film passable
    sio_fn = interp1d(sio_df.wavelength, sio_df.nk, kind='linear')
    water_fn = lambda wavelength: 1.333333
    si_df = get_nkvals('Si') ## change to make film passable
    si_fn = interp1d(si_df.wavelength, si_df.nk, kind='linear')
    reflectance = calc_reflectances(n_fn_list=[water_fn, sio_fn, si_fn], 
                                    d_list=[np.inf, starting_thk, np.inf], 
                                    th_0=0, 
                                    spectral_range='wide')
    r_df = pd.DataFrame(reflectance, columns=['wavelength', 'reflectance'])
    source = ColumnDataSource(data=r_df)

    plot = figure(x_axis_type='auto', y_range=(0, 1), 
                  y_axis_label='reflectance', title="Spectra from SiO on Si")
    plot.line('wavelength', 'reflectance', source=source)

    def callback(attr, old, new):
        if new == starting_thk:
            data = r_df
        else:
            reflectance = calc_reflectances([water_fn, sio_fn, si_fn], [np.inf, new, np.inf], 0, spectral_range='wide')
            data = pd.DataFrame(reflectance, columns=['wavelength', 'reflectance'])
        source.data = ColumnDataSource(data=data).data

    slider = Slider(start=0, end=starting_thk, value=starting_thk, step=starting_thk/20, title="SiO Thickness")
    slider.on_change('value', callback)

    doc.add_root(column(slider, plot))

    doc.theme = Theme(filename="theme.yaml")


@app.route('/data', methods=['GET'])
def bkapp_page():
    script = server_document('http://localhost:5006/bkapp')
    return render_template("embed.html", script=script, template="Flask")


def bk_worker():
    # Can't pass num_procs > 1 in this configuration. If you need to run multiple
    # processes, see e.g. flask_gunicorn_embed.py
    server = Server({'/bkapp': modify_doc}, io_loop=IOLoop(), allow_websocket_origin=["localhost:8000"])
    server.start()
    server.io_loop.start()
