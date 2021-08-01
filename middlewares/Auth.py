from functools import wraps
from flask import request, jsonify, g
from DB import jwt_secret, db
from models.Users import users
import jwt

def checkAuth(func):
    @wraps(func)
    def authChecker(*args, **kwargs):
        try:
            authorization = request.headers.get('Authorization')
            bearer = authorization.split()[1]
            if bearer:
                try:
                    user = jwt.decode(bearer, jwt_secret, algorithms=["HS256"])
                    foundUser = users.query.get(user['id'])
                    if foundUser:
                        g.user = { "id": foundUser.id, "email": foundUser.email, "usertype": foundUser.usertype }
                        return func(*args, **kwargs)
                    else:
                        return jsonify({"message": "Unauthorized User."}), 401
                except:
                    return jsonify({"message": "Invalid Bearer Token Passed."}), 401
            else:
                return jsonify({"message": "Not Allowed"}), 401
        except:
            return jsonify({"message": "It seems No Authorization header is present in system."}), 401

    return authChecker