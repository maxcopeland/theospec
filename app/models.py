from datetime import datetime
from app import db, login_manager
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"


class Material(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), unique=True, nullable=False)
    nkvalues = db.relationship('NKValues', backref='mat_name', lazy=True)

    def __repr__(self):
        return f"Material('{self.name}')'"


class NKValues(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    wavelength = db.Column(db.Float, unique=False, nullable=False)
    n_value = db.Column(db.Float, unique=False, nullable=False)
    k_value = db.Column(db.Float, unique=False, nullable=True)
    material_id = db.Column(db.Float, db.ForeignKey('material.id'), nullable=False)

    def __repr__(self):
        return f"NKValues('{self.wavelength}', '{self.n_value}', '{self.k_value}')'"
