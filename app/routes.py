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

@app.route("/simulator", methods=['GET', 'POST'])
@login_required
def simulator():
    form = SimulatorForm()
    if form.validate_on_submit():
        # store input data in cookie
        session['medium'] = form.medium.data
        session['active_layers'] = form.active_layers.data
        session['trench_layers'] = form.trench_layers.data
        # decimal cant serialize, thus changing to string
        session['pattern_density'] = str(form.pattern_density.data)
        return redirect(url_for('test'))
    return render_template('simulator.html', form=form)

@app.route('/simulator/dashboard', methods=['GET', 'POST'])
def test():
    medium = session['medium']
    active_layers = session['active_layers']
    trench_layers = session['trench_layers']
    pattern_density = float(session['pattern_density'])
    return str([medium, active_layers, trench_layers, pattern_density])


import dash
import dash_core_components as dcc  
import dash_html_components as html
import plotly.graph_objs as go
from scipy.interpolate import interp1d
from tmm.color import calc_reflectances
import numpy as np


external_scripts = [
    {
        'src':"https://code.jquery.com/jquery-3.3.1.slim.min.js", 
        'integrity':"sha384-q8i/X+965DzO0rT7abK41JStQIAqVgRVzpbzo5smXKp4YfRvH+8abtTE1Pi6jizo",
        'crossorigin':"anonymous"
    },
    {
        'src':"https://cdnjs.cloudflare.com/ajax/libs/popper.js/1.14.3/umd/popper.min.js",
        'integrity':"sha384-ZMP7rVo3mIykV+2+9J3UJ46jBk0WLaUAdn689aCwoqbBJiSnjAK/l8WvCWPIPm49", 
        'crossorigin':"anonymous"
    },
    {
        'src':"https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/js/bootstrap.min.js",
        'integrity':"sha384-ChfqqxuZUCnJSK3+MXmPNIyE6ZbWh2IMqE241rYiqJxyMiZ6OW/JmZQ5stwEULTy", 
        'crossorigin':"anonymous"
    }
]

external_stylesheets = [
    {
        'rel':'stylesheet',
        'href': "https://stackpath.bootstrapcdn.com/bootstrap/4.1.3/css/bootstrap.min.css",
        'integrity': "sha384-MCw98/SFnGE8fJT3GXwEOngsV7Zt27NXFoaoApmYm81iuXoPkFOJwJ8ERdknLPMO",
        'crossorigin':'anonymous'
    },
    {
        'rel':'stylesheet',
        'type': 'text/css',
        'href': 'static/main.css'
    }
]

data_app = dash.Dash(__name__, server=app, external_scripts=external_scripts,
                     external_stylesheets=external_stylesheets, url_base_pathname='/data/')

max_thk = 1000  # Global setpoints for testing
mat_name = 'SiO2' # Global setpoints for testing

data_app.layout = html.Div([
    html.H1('theospec', className='col-xl-12', style={'align': 'center'}),
    html.Div([
        dcc.Dropdown(
            id='active-dropdown',
            options=[{'label': i.name, 'value': i.name} for i in Material.query.all()],
            value='SiO2' 
            )], className='col-md-2'),
    html.Div([
        dcc.Input(
            id='active-thickness',
            placeholder='Enter thickness (A)',
            type='numeric',
            value=1000,
            min=0,
            max=10000
            ),
        html.Button('Enter', id='active-button')
        ], className='col-md-2'),
    html.Div([
        dcc.Graph(id='graph-with-slider'),
        dcc.Slider(
            id='thickness-slider',
            min=0,
            max=max_thk,
            step=10,
            value=max_thk,

            )], className='col-md-6')],
className='row')

def get_nkvals(mat_name):
    mat_id = Material.query.filter_by(name=mat_name).first().id
    nk_vals = NKValues.query.filter_by(material_id=mat_id).all()
    df = pd.DataFrame([(d.wavelength, d.n_value, d.k_value) for d in nk_vals], 
                  columns=['wavelength', 'n', 'k'])
    df['nk'] = df['n'] + (1j * df['k'])
    ### Handle nm from data instead of Angstrom
    if df.wavelength.min() > 1000:
        df['wavelength'] = df.wavelength /10
    return df

def compute_reflectance(mat_name, thickness):
    starting_thk = thickness
    mat_df = get_nkvals(mat_name) ## change to make film passable
    mat_fn = interp1d(mat_df.wavelength, mat_df.nk, kind='linear')
    water_fn = lambda wavelength: 1.333333
    si_df = get_nkvals('Si') ## change to make film passable
    si_fn = interp1d(si_df.wavelength, si_df.nk, kind='linear')
    reflectance = calc_reflectances(n_fn_list=[water_fn, mat_fn, si_fn], 
                                    d_list=[np.inf, starting_thk, np.inf], 
                                    th_0=0, 
                                    spectral_range='wide')
    r_df = pd.DataFrame(reflectance, columns=['wavelength', 'reflectance'])
    return r_df


@data_app.callback(dash.dependencies.Output('graph-with-slider', 'figure'), 
                   [dash.dependencies.Input('active-dropdown', 'value'),
                    dash.dependencies.Input('active-button', 'n_clicks')],
                   [dash.dependencies.State('active-thickness', 'value'),
                    dash.dependencies.State('thickness-slider', 'value')])
@app.route('/data/')
def data(selected_material, n_clicks, starting_thickness, selected_thickness):
    df = compute_reflectance(selected_material, starting_thickness)
    return {
        'data': [go.Scatter(
            x=df['wavelength'],
            y=df['reflectance'],
            mode= 'lines',
            name= 'lines'
        )],
        'layout': go.Layout(
            title='Spectra for {0} at {1}A'.format(str(selected_material), str(starting_thickness)),
            xaxis={
                'title': 'Wavelength',
                'type' : 'linear'
            },
            yaxis={
                'title': 'Reflectance',
                'type': 'linear'
            }
        )
    }


# from bokeh.embed import server_document
# from bokeh.layouts import column
# from bokeh.models import ColumnDataSource, Slider
# from bokeh.plotting import figure
# from bokeh.server.server import Server
# from bokeh.themes import Theme
# from tornado.ioloop import IOLoop
# from bokeh.sampledata.sea_surface_temperature import sea_surface_temperature
# from scipy.interpolate import interp1d
# from tmm.color import calc_reflectances
# import numpy as np






# def modify_doc(doc, mat_name):
#     starting_thk = 2000
#     mat_df = get_nkvals(mat_name) ## change to make film passable
#     mat_fn = interp1d(mat_df.wavelength, mat_df.nk, kind='linear')
#     water_fn = lambda wavelength: 1.333333
#     si_df = get_nkvals('Si') ## change to make film passable
#     si_fn = interp1d(si_df.wavelength, si_df.nk, kind='linear')
#     reflectance = calc_reflectances(n_fn_list=[water_fn, mat_fn, si_fn], 
#                                     d_list=[np.inf, starting_thk, np.inf], 
#                                     th_0=0, 
#                                     spectral_range='wide')
#     r_df = pd.DataFrame(reflectance, columns=['wavelength', 'reflectance'])
#     source = ColumnDataSource(data=r_df)

#     plot = figure(x_axis_type='auto', y_range=(0, 1), 
#                   y_axis_label='reflectance', title="Spectra from SiO on Si")
#     plot.line('wavelength', 'reflectance', source=source)

#     def callback(attr, old, new):
#         if new == starting_thk:
#             data = r_df
#         else:
#             reflectance = calc_reflectances([water_fn, mat_fn, si_fn], [np.inf, new, np.inf], 0, spectral_range='wide')
#             data = pd.DataFrame(reflectance, columns=['wavelength', 'reflectance'])
#         source.data = ColumnDataSource(data=data).data

#     slider = Slider(start=0, end=starting_thk, value=starting_thk, step=starting_thk/20, title="SiO Thickness")
#     slider.on_change('value', callback)

#     doc.add_root(column(slider, plot))

#     doc.theme = Theme(filename="theme.yaml")


# @app.route('/data', methods=['GET'])
# def bkapp_page():
#     script = server_document('http://localhost:5006/bkapp')
#     return render_template("embed.html", script=script, template="Flask")


# def bk_worker():
#     # Can't pass num_procs > 1 in this configuration. If you need to run multiple
#     # processes, see e.g. flask_gunicorn_embed.py
#     server = Server({'/bkapp': modify_doc}, io_loop=IOLoop(), allow_websocket_origin=["localhost:8000"])
#     server.start()
#     server.io_loop.start()
