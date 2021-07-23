from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
import uuid
import jwt
import datetime
# ! Init App
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/test'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ! Init DB
db = SQLAlchemy(app)

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
    token = db.Column(db.String(1000), nullable=False)

db.create_all()
@app.route("/signup", methods=["POST"])
def signup():
    try:
        payload = request.json
        if all (k in payload for k in ("email","mobile","password")):
            newUser = users(email = payload['email'], mobile = payload['mobile'], password = payload['password'])
            db.session.add(newUser)
            try:
                db.session.commit()
                del payload['password']
                payload['id'] = newUser.id 
                # jwt.encode({'key': 'value'}, 'secret', algorithm='HS256')
                security_payload = {'user_id': payload['id'], 'email': payload['email'], 'usertype': 'user'}
                print(security_payload)
                encoded_jwt = jwt.encode({'key': 'value'}, 'secret', algorithm='HS256')
                newToken = jwt(user_id = payload['id'], token = encoded_jwt)
                print('new token created '+ newToken.id)
                payload['token'] = encoded_jwt
                return payload
            except Exception as e:
                return jsonify({"error": "Sorry! Something went wrong while creating user.", "message": e.orig if e.orig else 'no reference'}), 500

        return jsonify({"error": "Invalid Data. Please send mobile number, email and password while signing up"}), 400
    except Exception as coreError:
        return jsonify({"error": "Sorry! Something went wrong.", "message": coreError.orig if coreError.orig else 'no reference'}), 500

@app.route("/")
def home():
    token = jwt.JWT.encode({'public_id': '14545454545', 'exp' : datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, '45454545')  
    return jsonify({"message": "Hello There", "token": token})


app.run(debug=True)