from functools import wraps
from models.Cart import Cart
from models.Users import users
from flask import g, session
from werkzeug.utils import redirect
from models.Categories import categories
from DB import jwt_secret
import jwt

def getCat(func):
    @wraps(func)
    def categoriesFetch(*args, **kwargs):
        try:
            allCategories = categories.query.order_by(categories.id.desc()).all()
            g.categories = allCategories
            return func(*args, **kwargs)
        except:
            return func(*args, **kwargs)

    return categoriesFetch

def getCart(func):
    @wraps(func)
    def categoriesFetch(*args, **kwargs):
        print('cart middleware executes')
        if "token" in session:
            try:
                user = jwt.decode(session['token'], jwt_secret, algorithms=["HS256"])
                foundUser = users.query.get(user['id'])
                if foundUser:
                    if foundUser.usertype == "users":
                        # get cart
                        getCart = Cart.query.filter_by(user_id = foundUser.id).count()
                        g.cart = getCart
                        return func(*args, **kwargs)
                    else:
                        g.cart = 0
                        return func(*args, **kwargs)
            except Exception as coreError:
                print(str(coreError))
                g.cart = 0
                return func(*args, **kwargs)
        else:
            g.cart = ''
            return func(*args, **kwargs)

    return categoriesFetch