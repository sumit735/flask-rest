from flask import Flask, json, jsonify, request, g
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from DB import db, jwt_secret
from models.Users import users, tokens
from models.Categories import categories
from models.Products import Products
from models.Cart import Cart
from models.Orders import Orders
import time
from middlewares.Auth import checkAuth
from slugify import slugify
import random
import uuid

# ! Init App
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/test'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ! Init DB
db.init_app(app)

with app.app_context():
    db.create_all()
    

@app.route("/signup", methods=["POST"])
def signup():
    try:
        payload = request.json
        if all (k in payload for k in ("email","mobile","password")):
            hashed_password = generate_password_hash(payload['password'], method='sha256')
            payload['password'] = hashed_password
            newUser = users(email = payload['email'], mobile = payload['mobile'], password = payload['password'])
            db.session.add(newUser)
            try:
                db.session.commit()
                del payload['password']
                payload['id'] = newUser.id 
                security_payload = {'user_id': payload['id'], 'email': payload['email'], 'usertype': 'user'}
                print(security_payload)
                encoded_jwt = jwt.encode(security_payload, 'flask_rest_project', algorithm='HS256')
                newToken = tokens(user_id = payload['id'], token = encoded_jwt)
                db.session.add(newToken)
                db.session.commit()
                print('new token created '+ str(newToken.id))
                payload['token'] = encoded_jwt
                return payload
            except Exception as e:
                return jsonify({"error": "Sorry! Something went wrong while creating user.", "message": str(e.orig) if e.orig else 'no reference'}), 500

        return jsonify({"error": "Invalid Data. Please send mobile number, email and password while signing up"}), 400
    except Exception as coreError:
        return jsonify({"error": "Sorry! Something went wrong.", "message": str(coreError.orig) if coreError.orig else 'no reference'}), 500

@app.route("/login", methods=["POST"])
def login():
    try:
        payload = request.json
        print(payload)
        if all (k in payload for k in ("username","password")):
            findUserByEmail = users.query.filter_by(email = payload['username']).first()
            findUserByMobile = users.query.filter_by(mobile = payload['username']).first()
            if findUserByEmail:
                isValidPass = check_password_hash(findUserByEmail.password, payload['password'])
                if isValidPass:
                    userDetails = { "id" : findUserByEmail.id, "email" : findUserByEmail.email }
                    jwtToken = jwt.encode(userDetails, 'flask_rest_project', algorithm='HS256')
                    insertToken = tokens(user_id = findUserByEmail.id, token = jwtToken)
                    db.session.add(insertToken)
                    db.session.commit()
                    return jsonify({"email": findUserByEmail.email, "token": jwtToken}), 200  
                else: 
                    return jsonify({ "error" : "Incorrect Username or password" }), 401
            elif findUserByMobile:
                isValidPass = check_password_hash(findUserByMobile.password, payload['password'])
                if isValidPass:
                    userDetails = { "id" : findUserByMobile.id, "email" : findUserByMobile.email }
                    jwtToken = jwt.encode(userDetails, 'flask_rest_project', algorithm='HS256')
                    insertToken = tokens(user_id = findUserByMobile.id, token = jwtToken)
                    db.session.add(insertToken)
                    db.session.commit()
                    return jsonify({"email": findUserByMobile.email, "token": jwtToken}), 200  
                else:
                    return jsonify({ "error" : "Incorrect Username or password" }), 401
            else:
                return jsonify({"error" : "No Users Available"}), 404
        else:
            return jsonify({"error": "Invalid Data. Please send mobile number/email and password while logging in."}), 400 
    except Exception as coreError:
        return jsonify({"error": "Sorry! Something went wrong.", "message": str(coreError.orig) if coreError.orig else 'no reference'}), 500


@app.route("/logout", methods=["GET"])
def logout():
    try:
        authorization = request.headers.get('Authorization')
        bearer = authorization.split()[1]
        if bearer:
            decodedToken = jwt.decode(bearer, 'flask_rest_project', algorithms=["HS256"])
            print(decodedToken['id'])
            print(bearer)
            obj = tokens.query.filter_by(user_id=decodedToken['id'], token=bearer).first()
            db.session.delete(obj)
            db.session.commit()
            return jsonify({ "message": "OK" }), 200
        else: 
            return jsonify({ "message": "OK" }), 200
    except Exception as coreError:
        if coreError.orig:
            message = str(coreError.orig)
        else:
            message = 'no reference'
        return jsonify({"error": "Sorry! Something went wrong.", "message": message }), 500


# categories route
@app.route("/category", methods=["POST"])
@checkAuth
def category():
    if g.user['usertype'] == 'admin':
        try:
            payload = request.json
            print(payload)
            if "name" in payload:
                if "image" in payload:
                    newCategory = categories( name=payload['name'], image=payload['image'], created_at=time.time() )
                else:
                    newCategory = categories(name=payload['name'], created_at=time.time())
                try:
                    db.session.add(newCategory)
                    db.session.commit()
                    if newCategory:
                        payload['id'] = newCategory.id 
                        payload['message'] = "Category Has Been Created"
                        return payload, 200
                    else:
                        return jsonify({ "message": "Failed To Add Category" }), 500
                except Exception as e:
                    if e:
                        message = str(e.orig)
                    else:
                        message = 'no reference'
                    return jsonify({ "error": "Sorry! Something went wrong while creating Category.", "message": message }), 500
            else:
                return jsonify({"error": "Invalid Data. Please send Name Of The Category"}), 400
        except Exception as coreError:
            if coreError:
                message = str(coreError.orig)
            else:
                message = 'no reference'
            return jsonify({ "error": "Sorry! Something went wrong.", "message": message }), 500
    else:
        return jsonify({ "error": "Sorry! You Are Not Authorized." }), 401


@app.route("/categories", methods=["GET"])
def allCategories():
    try:
        allCategories = categories.query.order_by(categories.id).all()
        if allCategories:
            print(allCategories)
            categoriesList = []
            for list in allCategories:
                categoriesList.append({ "id": list.id, "name": list.name, "created_at": list.created_at })
            return jsonify(categoriesList), 200
        else:
            return jsonify({ "message": "Failed To Get Categories" }), 500
    except Exception as e:
        print(str(e))
        return jsonify({ "error": "Sorry! Something went wrong while getting Categories."}), 500

@app.route("/category/<int:cat_id>", methods=["GET"])
def fetchCatById(cat_id):
    try:
        categoryDetails = categories.query.filter_by(id=cat_id).first()
        if categoryDetails:
            print(categoryDetails)
            return jsonify({ "id": categoryDetails.id, "name": categoryDetails.name, "created_at": categoryDetails.created_at }), 200
        else:
            return jsonify({ "message": "No Category Available against that id" }), 404
    except Exception as e:
        print(str(e))
        return jsonify({ "error": "Sorry! Something went wrong while getting Categories."}), 500

@app.route("/category/delete/<int:cat_id>", methods=["DELETE"])
@checkAuth
def deleteCatById(cat_id):
    try:
        categoryDetails = categories.query.filter_by(id=cat_id).first()
        if categoryDetails:
            db.session.delete(categoryDetails)
            db.session.commit()
            return jsonify({ "message": "Category Deleted Successfully", "name": categoryDetails.name }), 200
        else:
            return jsonify({ "message": "No Category Available against that id" }), 404
    except Exception as e:
        print(str(e))
        return jsonify({ "error": "Sorry! Something went wrong while getting Categories."}), 500

@app.route("/category/edit/<int:cat_id>", methods=["PUT"])
@checkAuth
def editCatById(cat_id):
    try:
        payload = request.json
        print(payload)
        if "name" in payload:
            categoryDetails = categories.query.filter_by(id=cat_id).first()
            if categoryDetails:
                categoryDetails.name = payload["name"]
                db.session.commit()
                return jsonify({ "message": "Category Updated Successfully", "name": categoryDetails.name }), 200
            else:
                return jsonify({ "message": "No Category Available against that id" }), 404
        else:
            return jsonify({ "message": "Minimum Requirements Not Satisfied For Updating a category" }), 404

    except Exception as e:
        print(str(e))
        return jsonify({ "error": "Sorry! Something went wrong while getting Categories."}), 500


# ! Products Routes

@app.route("/products/add", methods=["POST"])
@checkAuth
def addProduct():
    try:
        payload = request.json
        print(payload)
        if all (k in payload for k in ("name","price","stock", "category_id")):
            # ! Create A Slug From Name
            slug = slugify(payload['name'])
            checkSLugExists = Products.query.filter_by(slug=slug).first()
            if checkSLugExists is None:
                if "image" in payload:
                    newProduct = Products( name = payload['name'], slug = slug, price = payload['price'], stock = payload['stock'], category_id = payload['category_id'], image = payload['image'], created_at = time.time() )
                else:
                    newProduct = Products(name = payload['name'], slug = slug, price = payload['price'], stock = payload['stock'], category_id = payload['category_id'], created_at = time.time())                
            else:
                # ! generate a random slug
                number = random.randint(1111,9999)
                slug = slugify(payload['name']) + '-' + str(number)
                if "image" in payload:
                    newProduct = Products( name = payload['name'], slug = slug, price = payload['price'], stock = payload['stock'], category_id = payload['category_id'], image = payload['image'], created_at = time.time() )
                else:
                    newProduct = Products(name = payload['name'], slug = slug, price = payload['price'], stock = payload['stock'], category_id = payload['category_id'], created_at = time.time())
            # ! Add Product Now
            try:
                db.session.add(newProduct)
                db.session.commit()
                if newProduct:
                    payload['id'] = newProduct.id 
                    payload['message'] = "Product Has Been Created"
                    return payload, 200
                else:
                    return jsonify({ "message": "Failed To Add Product" }), 500
            except Exception as e:
                if e:
                    message = str(e)
                else:
                    message = 'no reference'
                return jsonify({ "error": "Sorry! Something went wrong while creating Category.", "message": message }), 500
        else:
            return jsonify({"error": "Invalid Data. Please send name, price, stock and category id to create a product."}), 400
    except Exception as coreError:
        if coreError:
            message = str(coreError)
        else:
            message = 'no reference'
        return jsonify({ "error": "Sorry! Something went wrong.", "message": message }), 500

@app.route("/products/all", methods=["GET"])
def getAllProducts():
    try:
        allProducts = Products.query.order_by(Products.id).all()
        if allProducts:
            print(allProducts)
            productsList = []
            for list in allProducts:
                productsList.append({ "id": list.id, "name": list.name, "price": list.price, "stock": list.stock, "category_id": list.category_id ,"created_at": list.created_at })
            return jsonify(productsList), 200
    except Exception as coreError:
        if coreError:
            message = str(coreError.orig)
        else:
            message = 'no reference'
        return jsonify({ "error": "Sorry! Something went wrong.", "message": message }), 500

@app.route("/products/<int:prod_id>", methods=["GET"])
def fetchProdById(prod_id):
    try:
        productDetails = Products.query.filter_by(id=prod_id).first()
        if productDetails:
            print(productDetails)
            return jsonify({ "id": productDetails.id, "name": productDetails.name, "price": productDetails.price, "stock": productDetails.stock, "category_id": productDetails.category_id ,"created_at": productDetails.created_at }), 200
        else:
            return jsonify({ "message": "No Product Available against that id" }), 404
    except Exception as e:
        print(str(e))
        return jsonify({ "error": "Sorry! Something went wrong while getting Products."}), 500

@app.route("/products/category/<int:cat_id>", methods=["GET"])
def fetchProdByCatId(cat_id):
    try:
        productDetails = Products.query.filter_by(category_id=cat_id).all()
        if productDetails:
            print(productDetails)
            productsList = []
            for list in productDetails:
                productsList.append({ "id": list.id, "name": list.name, "price": list.price, "stock": list.stock, "category_id": list.category_id ,"created_at": list.created_at })
            return jsonify(productsList), 200
        else:
            return jsonify({ "message": "No Product Available against that Category id" }), 404
    except Exception as e:
        print(str(e))
        return jsonify({ "error": "Sorry! Something went wrong while getting Products."}), 500\

@app.route("/products/edit/<int:prod_id>", methods=["PUT"])
@checkAuth
def editProdByCatId(prod_id):
    try:
        payload = request.json
        if "name" in payload or "price" in payload or "stock" in payload or "category_id" in payload:
            productDetails = Products.query.filter_by(id=prod_id).first()
            if productDetails:
                print(productDetails)
                # update old data
                if "name" in payload:
                    productDetails.name = payload["name"] 
                if "price" in payload:
                    productDetails.price = payload["price"]
                if "stock" in payload:
                    productDetails.stock = payload["stock"]
                if "category_id" in payload:
                    productDetails.category_id = payload["category_id"]
                db.session.commit()

                products = []
                products.append({ "id": productDetails.id, "name": productDetails.name, "price": productDetails.price, "stock": productDetails.stock, "category_id": productDetails.category_id ,"created_at": productDetails.created_at })

                return jsonify({"message": "Product Has Been Updated", "product": products}), 200
            else:
                return jsonify({ "message": "No Product Available against that Category id" }), 404
        else:
            return jsonify({ "message": "Minimum requirements has not been satisfied for updating the product." }), 404

    except Exception as e:
        print(str(e))
        return jsonify({ "error": "Sorry! Something went wrong while getting Products."}), 500

@app.route("/products/delete/<int:product_id>", methods=["DELETE"])
@checkAuth
def deleteProdById(product_id):
    try:
        productDetails = Products.query.filter_by(id=product_id).first()
        if productDetails:
            db.session.delete(productDetails)
            db.session.commit()
            return jsonify({ "message": "Product Deleted Successfully", "name": productDetails.name }), 200
        else:
            return jsonify({ "message": "No Product Available against that id" }), 404
    except Exception as e:
        print(str(e))
        return jsonify({ "error": "Sorry! Something went wrong while getting Product Details."}), 500


# ! Cart Routes
@app.route("/cart/add", methods=["POST"])
@checkAuth
def addToCart():
    try:
        payload = request.json
        print(payload)
        if all (k in payload for k in ("product_id","user_id")):
            findProduct = Products.query.get(payload["product_id"])
            if findProduct:
                price = findProduct.price
                if "qty" in payload:
                    # TODO - Calculate Amount
                    totalAmt = int(payload['qty']) * float(price)
                    newCart = Cart( product_id = payload['product_id'], user_id = payload['user_id'], qty = payload['qty'], amount = totalAmt, created_at = time.time() )
                else:
                    totalAmt = int(1) * float(price)
                    newCart = Cart( product_id = payload['product_id'], user_id = payload['user_id'], qty = 1, amount = totalAmt, created_at = time.time() )
            else:
                return jsonify({ "message": "Failed To Add. No Product Exist With That id." }), 500
            
            try:
                db.session.add(newCart)
                db.session.commit()
                if newCart:
                    payload['id'] = newCart.id 
                    payload['message'] = "Added To Cart Successfully"
                    return payload, 200
                else:
                    return jsonify({ "message": "Failed To Add To Cart" }), 500
            except Exception as e:
                if e:
                    message = str(e.orig)
                else:
                    message = 'no reference'
                return jsonify({ "error": "Sorry! Something went wrong while adding to cart.", "message": message }), 500
        else:
            return jsonify({"error": "Invalid Data. Please send product id, user id to create a cart item."}), 400
    except Exception as coreError:
        if coreError:
            message = str(coreError.orig)
        else:
            message = 'no reference'
        return jsonify({ "error": "Sorry! Something went wrong.", "message": message }), 500

@app.route("/cart/all", methods=["GET"])
@checkAuth
def getAllCart():
    try:
        userDetails = g.user
        print(userDetails)
        allCart = Cart.query.filter_by(user_id=userDetails['id']).all()
        if allCart:
            print(allCart)
            cartList = []
            for list in allCart:
                name = Products.query.get(list.product_id).name
                price = Products.query.get(list.product_id).price
                cartList.append({ "id": list.id, "qty": list.qty, "amount": list.amount, "name": name, "price": price ,"created_at": list.created_at })
            return jsonify(cartList), 200
        else:
            return jsonify({ "error": "Sorry! Empty Cart. Add Products First" }), 400
    except Exception as coreError:
        if coreError:
            message = str(coreError.orig)
        else:
            message = 'no reference'
        return jsonify({ "error": "Sorry! Something went wrong.", "message": message }), 500

@app.route("/cart/edit/<int:cart_id>", methods=["PUT"])
@checkAuth
def updateCart(cart_id):
    try:
        payload = request.json
        if "qty" in payload:
            cartDetails = Cart.query.get(cart_id)
            if cartDetails:
                # ! fetch amount
                price = Products.query.get(cartDetails.product_id).price
                # update old data
                totalAmt = int(payload['qty']) * float(price)
                cartDetails.qty = payload["qty"]
                cartDetails.amount = totalAmt
                
                db.session.commit()

                cart = []
                cart.append({ "id": cartDetails.id, "amount": cartDetails.amount, "qty": cartDetails.qty, "product_id": cartDetails.product_id })

                return jsonify({"message": "Cart Has Been Updated", "cart": cart}), 200
            else:
                return jsonify({ "message": "No Cart Details Available against that Category id" }), 404
        else:
            return jsonify({ "message": "Minimum requirements has not been satisfied for updating the Cart Details." }), 404

    except Exception as e:
        print(str(e))
        return jsonify({ "error": "Sorry! Something went wrong.."}), 500

@app.route("/cart/delete/<int:cart_id>", methods=["DELETE"])
@checkAuth
def deleteCart(cart_id):
    try:
        cartDetails = Cart.query.get(cart_id)
        if cartDetails:
            db.session.delete(cartDetails)
            db.session.commit()
            return jsonify({ "message": "Cart Deleted Successfully" }), 200
        else:
            return jsonify({ "message": "No Cart Details Available against that id" }), 404
    except Exception as e:
        print(str(e))
        return jsonify({ "error": "Sorry! Something went wrong while getting Cart Details."}), 500

# ! USER Routes
@app.route("/users/me", methods=["GET"])
@checkAuth
def getMyDetails():
    # print()
    try:
        me = users.query.get(g.user['id'])
        if me:
            print(me)
            return jsonify({ "id": me.id, "email": me.email, "mobile": me.mobile }), 200
    except Exception as coreError:
        if coreError:
            message = str(coreError.orig)
        else:
            message = 'no reference'
        return jsonify({ "error": "Sorry! Something went wrong.", "message": message }), 500

@app.route("/me", methods=["PUT"])
@checkAuth
def updateMyDetails():
    try:
        payload = request.json
        if "email" in payload or "mobile" in payload:
            userDetails = users.query.get(g.user['id'])
            if userDetails:
                print(userDetails)
                # update old data
                if "email" in payload:
                    userDetails.email = payload["email"] 
                if "mobile" in payload:
                    userDetails.mobile = payload["mobile"]
                db.session.commit()

                user = []
                user.append({ "id": userDetails.id, "email": userDetails.email, "mobile": userDetails.mobile })

                return jsonify({"message": "User Details Has Been Updated", "user": user}), 200
            else:
                return jsonify({ "message": "No User Available against that id" }), 404
        else:
            return jsonify({ "message": "Minimum requirements has not been satisfied for updating the user." }), 404
        
    except Exception as coreError:
        if coreError:
            message = str(coreError)
        else:
            message = 'no reference'
        return jsonify({ "error": "Sorry! Something went wrong.", "message": message }), 500

# ! Order Routes
@app.route("/orders/create", methods=["POST"])
@checkAuth
def createOrder():
    try:
        userDetails = g.user
        print(userDetails)
        # ! Fetch Cart Details
        try:
            userDetails = g.user
            print(userDetails['id'])
            allCart = Cart.query.filter_by(user_id=userDetails['id']).all()
            if allCart:
                print(allCart)
                cartList = []
                allTotal = float(0)
                for list in allCart:
                    name = Products.query.get(list.product_id).name
                    price = Products.query.get(list.product_id).price
                    allTotal += list.amount
                    cartList.append({ "id": list.id, "qty": list.qty, "amount": list.amount, "name": name, "price": price ,"created_at": list.created_at })
                    
                # ! Get Total amount & create Order Obj
                order_id = 'UU'+ str(uuid.uuid4().hex[:8])
                orderObj = { "user_id": userDetails['id'], "order": cartList, "total": allTotal, "status": "stage", "payment_method": "COD", "order_id": order_id.upper() }

                # ! Create Order
                newOrder = Orders(order_id=order_id, user_id=userDetails['id'], order=json.dumps(cartList), amount=orderObj['total'], status=orderObj['status'], payment_method = orderObj['payment_method'], created_at = time.time())
                db.session.add(newOrder)
                db.session.commit()
                if newOrder:
                    # ! Empty user's cart
                    deleteCart = Cart.__table__.delete().where(Cart.user_id == userDetails['id'])
                    db.session.execute(deleteCart)
                    db.session.commit()
                    return jsonify(orderObj), 200
                else:
                    return jsonify({ "error": "Sorry! Something went wrong."}), 500
            else:
                return jsonify({ "error": "Sorry! Empty Cart. Add Products First" }), 400
        except Exception as coreError:
            print(coreError)
            if coreError:
                message = str(coreError)
            else:
                message = 'no reference'
            return jsonify({ "error": "Sorry! Something went wrong.", "message": message }), 500
        # TODO Generate Signature(PG)
    except Exception as coreError:
        if coreError:
            message = str(coreError)
        else:
            message = 'no reference'
        return jsonify({ "error": "Sorry! Something went wrong.", "message": message }), 500

@app.route("/orders/get", methods=["GET"])
@checkAuth
def getMyOrders():
    try:
        if g.user['usertype'].lower() == 'admin':
            getOrders = Orders.query.order_by(Orders.id.desc()).all()
        else:
            getOrders = Orders.query.filter_by(user_id=g.user['id'])
        if getOrders:
            orderList = []
            for list in getOrders:
                orderList.append({ "id": list.id,"amount": list.amount, "status": list.status, "payment_method": list.payment_method ,"created_at": list.created_at, "order": json.loads(list.order) })
            return jsonify(orderList), 200
        else:
            return jsonify({ "message": "Sorry! No Orders Found." }), 404        
    except Exception as coreError:
        if coreError:
            message = str(coreError)
        else:
            message = 'no reference'
        return jsonify({ "error": "Sorry! Something went wrong.", "message": message }), 500

@app.route("/order/get/<string:order_id>", methods=["GET"])
@checkAuth
def getOrderById(order_id):
    try:
        getOrder = Orders.query.filter_by(order_id=order_id).first()
        if getOrder:
            if g.user['usertype'].lower() == 'admin':
                return jsonify({ "id": getOrder.id,"amount": getOrder.amount, "status": getOrder.status, "payment_method": getOrder.payment_method ,"created_at": getOrder.created_at, "order": json.loads(getOrder.order) })     
            else:
                if getOrder.user_id == g.user['id']:
                    return jsonify({ "id": getOrder.id,"amount": getOrder.amount, "status": getOrder.status, "payment_method": getOrder.payment_method ,"created_at": getOrder.created_at, "order": json.loads(getOrder.order) })
                else:
                    return jsonify({ "message": "No Order Found With That Detail." }), 404                       
        else:
            return jsonify({ "message": "No Order Found." }), 404 

    except Exception as coreError:
        if coreError:
            message = str(coreError)
        else:
            message = 'no reference'
        return jsonify({ "error": "Sorry! Something went wrong.", "message": message }), 500

@app.route("/order/edit/<string:order_id>", methods=["GET"])
@checkAuth
def updateOrderStatus(order_id):
    try:
        if g.user['usertype'] == 'admin':
            fetchOrder = Orders.query.filter_by(order_id=order_id).first()
            if fetchOrder:
                payload = request.json
                if "status" in payload:
                    if payload["status"] == 'pending' or payload["status"] == 'processing' or payload["status"] == 'shipped' or payload["status"] == 'delivered' or payload["status"] == 'cancelled':
                        fetchOrder.status = payload["status"]
                        db.session.commit()
                        return jsonify({ "message": "Order Status Updated Successfully.", "status": fetchOrder.status }), 200
                    else:
                        return jsonify({ "message": "Incorrect Status Update." }), 403
                else:
                    return jsonify({ "message": "Minimum requirements has not been satisfied for updating the order." }), 400
            else:
                return jsonify({ "message": "No Order found against that id." }), 404
        else:
            return jsonify({ "message": "Unauthorized User." }), 401

    except Exception as coreError:
        if coreError:
            message = str(coreError)
        else:
            message = 'no reference'
        return jsonify({ "error": "Sorry! Something went wrong.", "message": message }), 500

@app.route("/")
def home():
    return jsonify({ "message": "Hello There" })


app.run(debug=True)