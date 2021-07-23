from flask_sqlalchemy import SQLAlchemy

# ! Init DB
db = SQLAlchemy()

# ! User Model
class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    mobile = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    usertype = db.Column(db.String(120), nullable=False, default='user')
# ! Login session Model
class jwt(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    token = db.Column(db.String, nullable=False)