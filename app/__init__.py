import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager



app = Flask(__name__)
app.config['SECRET_KEY'] = 'a76d7217ce0c96c0464127de75e1d8e7'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///theospec.db'
app.config['UPLOAD_FOLDER'] =  "C:\\Users\\MCopeland155816\\Documents\\fvxe\\spectral_sim\\theospec\\uploads"
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'


from app import routes