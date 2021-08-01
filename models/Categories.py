from DB import db

class categories(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    image = db.Column(db.String(120), nullable=True)
    created_at = db.Column(db.String(255), nullable=False)
