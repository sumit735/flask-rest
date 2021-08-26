from DB import db

class Addresses(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    firstName = db.Column(db.String(100), nullable=False)
    lastName = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state = db.Column(db.String(100), nullable=False)
    pincode = db.Column(db.String(6), nullable=False)
    phone = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.String(255), nullable=False)
