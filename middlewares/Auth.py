from functools import wraps
from flask import request, jsonify, g, session, flash, url_for
from werkzeug.utils import redirect
from DB import jwt_secret, db
from models.Users import users
import jwt

def checkApiAuth(func):
    @wraps(func)
    def apiauthChecker(*args, **kwargs):
        try:
            if "token" in session:
                try:
                    user = jwt.decode(session['token'], jwt_secret, algorithms=["HS256"])
                    foundUser = users.query.get(user['id'])
                    if foundUser:
                        if foundUser.usertype == "users":
                            g.user = { "id": foundUser.id, "email": foundUser.email, "usertype": foundUser.usertype }
                            return func(*args, **kwargs)
                        else:
                            session.clear()
                            return jsonify({ "message": "You Need To Be Logged In" }), 401
                except Exception as coreError:
                    print(coreError)
                    return jsonify({ "message": "Some Exception Occured" }), 401
            else:
                return jsonify({ "message": "You Need To Be Logged In" }), 401
        except Exception as e:
            print(e)
            return jsonify({ "message": "Something Went Wrong" }), 500

    return apiauthChecker


def checkAuth(func):
    @wraps(func)
    def authChecker(*args, **kwargs):
        try:
            if "token" in session:
                try:
                    user = jwt.decode(session['token'], jwt_secret, algorithms=["HS256"])
                    foundUser = users.query.get(user['id'])
                    if foundUser:
                        if foundUser.usertype == "user":
                            g.user = { "id": foundUser.id, "email": foundUser.email, "usertype": foundUser.usertype }
                            return func(*args, **kwargs)
                        else:
                            session.clear()
                            flash('Unauthorized User.' ,'danger')
                            return redirect(url_for('login'))
                except Exception as coreError:
                    print(coreError)
                    flash('Sorry! Something Went Wrong....' ,'danger')
                    return redirect(url_for('login'))
            else:
                flash('Signin to enjoy our services' ,'danger')
                return redirect(url_for('login'))
        except Exception as e:
            flash('Some Exception Occured' ,'danger')
            return redirect('')
    return authChecker

def checkAdmin(func):
    @wraps(func)
    def adminChecker(*args, **kwargs):
        try:
            if "token" in session:
                try:
                    user = jwt.decode(session['token'], jwt_secret, algorithms=["HS256"])
                    foundUser = users.query.get(user['id'])
                    if foundUser:
                        if foundUser.usertype == "admin":
                            g.user = { "id": foundUser.id, "email": foundUser.email, "usertype": foundUser.usertype }
                            return func(*args, **kwargs)
                        else:
                            session.clear()
                            errMsg = "Unauthorized User"
                            return redirect('admin', error=errMsg)
                except Exception as coreError:
                    print(coreError)
                    errMsg = "Sorry! Something Went Wrong..."
                    return redirect('admin', error=errMsg)
            else:
                errMsg = "Sign in to start your session"
                return redirect('admin', error=errMsg)
        except:
            errMsg = "Sorry! Something Went Wrong"
            return redirect('admin', error=errMsg)
            # ! Create a Server Error Page

    return adminChecker