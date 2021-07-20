from flask import Flask, jsonify, request
import requests
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/test'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)

db.create_all()

@app.route("/signup", methods=["POST"])
def signup():
    try:
        payload = request.json
        if all (k in payload for k in ("username","email","password")):
            newUser = users(email = payload['email'], username = payload['username'], password = payload['password'])
            db.session.add(newUser)
            try:
                db.session.commit()
                del payload['password']
                payload['id'] = newUser.id
                return payload
            except Exception as e:
                return jsonify({"error": "Sorry! Something went wrong while creating user.", "message": str(e.orig)}), 500

        return jsonify({"error": "Invalid Data. Please send username, email and password while signing up"}), 400
    except:
        return jsonify({"error": "Sorry! Something went wrong."}), 500

@app.route("/")
def home():
    return jsonify({"message": "Hello There"})


app.run(debug=True)