import os
import re
from flask import Flask, json, jsonify, request, g, render_template, session, url_for, flash
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import redirect, secure_filename
from werkzeug.exceptions import HTTPException
from DB import db, jwt_secret, SMS_GATEWAY_UID, SMS_GATEWAY_PASS, SG_SENDER_ID
from models.Users import users, tokens
from models.Categories import categories
from models.Products import Products
from models.Cart import Cart
from models.Orders import Orders
from datetime import datetime
from middlewares.Auth import checkAuth, checkAdmin,checkApiAuth
from middlewares.categories import getCat, getCart
from slugify import slugify
import random
import uuid
import requests

# ! Init App
app = Flask(__name__)
app.secret_key = jwt_secret
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:''@localhost/test'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# ! Init DB
db.init_app(app)

with app.app_context():
    db.create_all()

# ! Error Handlers
# @app.errorhandler(HTTPException)
# def handle_exception(e):
#     """Return JSON instead of HTML for HTTP errors."""
#     # start with the correct headers and status code from the error
#     response = e.get_response()
#     # replace the body with JSON
#     response.data = json.dumps({
#         "code": e.code,
#         "name": e.name,
#         "description": e.description,
#     })
#     response.content_type = "application/json"
#     return response
    
# ! Admin Authentication Routes

@app.route("/admin/", methods=["GET", "POST"])
def admin():
    if request.method == 'POST':
        print('inside post')
        try:
            # ! Get Form Details
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
                errMsg = "Username Or Password Can't be Empty."
                return render_template('admin/login.html', error=errMsg)
            else:
                findUserByEmail = users.query.filter_by(email = username).first()
                findUserByMobile = users.query.filter_by(mobile = username).first()
                if findUserByEmail:
                    isValidPass = check_password_hash(findUserByEmail.password, password)
                    if isValidPass:
                        userDetails = { "id" : findUserByEmail.id, "email" : findUserByEmail.email }
                        jwtToken = jwt.encode(userDetails, jwt_secret, algorithm='HS256')
                        insertToken = tokens(user_id = findUserByEmail.id, token = jwtToken)
                        db.session.add(insertToken)
                        db.session.commit()
                        session['token'] = jwtToken
                        return redirect(url_for('adminHome')) 
                    else: 
                        errMsg = "Incorrect Username or Password."
                        return render_template('admin/login.html', error=errMsg)
                elif findUserByMobile:
                    isValidPass = check_password_hash(findUserByMobile.password, password)
                    if isValidPass:
                        userDetails = { "id" : findUserByMobile.id, "email" : findUserByMobile.email }
                        jwtToken = jwt.encode(userDetails, jwt_secret, algorithm='HS256')
                        insertToken = tokens(user_id = findUserByMobile.id, token = jwtToken)
                        db.session.add(insertToken)
                        db.session.commit()
                        session['token'] = jwtToken
                        return redirect(url_for('admin')) 
                    else:
                        errMsg = "Incorrect Username or Password."
                        return render_template('admin/login.html', error=errMsg)
                else:
                    errMsg = "Incorrect Username or Password."
                    return render_template('admin/login.html', error=errMsg)            
        except Exception as coreError:
            errMsg = "Sorry! Something went wrong."
            return render_template('admin/login.html', error=errMsg, original=str(coreError))
    else:
        if "token" in session:
            return redirect(url_for('adminHome'))
        else:
            errMsg = "Signin To Start Session."
            return render_template('admin/login.html', error=errMsg)

@app.route("/admin/home/", methods=["GET", "POST"])
@checkAdmin
def adminHome():
    getOrders = Orders.query.count()
    getUsers = users.query.filter_by(usertype="users").count()
    getCats = categories.query.count()
    getProds = Products.query.count()
    return render_template('admin/index.html', orders=getOrders, users=getUsers, categories=getCats, products=getProds, active='dashboard')

@app.route("/admin/logout/", methods=["GET", "POST"])
@checkAdmin
def adminLogout():
    session.clear()
    return redirect(url_for('admin'))

# ! Admin Category Routes
@app.route("/admin/category/add/", methods=["GET", "POST"])
@checkAdmin
def addCategory():
    allCategories = categories.query.order_by(categories.id.desc()).all()
    if request.method == 'GET':
        try:
            if allCategories:
                return render_template('admin/addCategory.html', activePage='Add Category', categories=allCategories, active='addCat')
            else:
                return render_template('admin/addCategory.html', activePage='Add Category', active='addCat')
        except Exception as e:
            print(str(e))
            return render_template('admin/addCategory.html', activePage='Add Category', active='addCat')
    else:
        try:
            catName = request.form.get('catName')
            checkIfCatExists = categories.query.filter_by(name=catName).first()
            if checkIfCatExists is None:
                if 'catImg' in request.files:
                    UPLOAD_FOLDER = 'static/uploads'
                    ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg', 'webp'}
                    catImg = request.files['catImg']
                    if catImg.filename == '':
                        return render_template('admin/addCategory.html', activePage='Add Category', error="Image Is Mandatory To Add A Category", categories=allCategories, active='addCat')
                    else:
                        if('.' in catImg.filename and catImg.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
                            file_uuid = secure_filename(str(uuid.uuid4())+'.'+catImg.filename.rsplit('.', 1)[1].lower())
                            catImg.save(os.path.join(UPLOAD_FOLDER, file_uuid))
                            newCategory = categories( name=catName, image=file_uuid, created_at=datetime.now().strftime("%d/%m/%Y %H:%M:%S") )
                            db.session.add(newCategory)
                            db.session.commit()
                            if newCategory:
                                allCategories = categories.query.order_by(categories.id.desc()).all()
                                return render_template('admin/addCategory.html', active='addCat', success="Category Has Been Added Succesfully.", activePage='Add Category', categories=allCategories)
                            else:
                                return render_template('admin/addCategory.html', active='addCat', activePage='Add Category', categories=allCategories)
                        else:
                            return render_template('admin/addCategory.html', active='addCat', activePage='Add Category', error="Only Images Are Allowed.", categories=allCategories)
                else:
                    return render_template('admin/addCategory.html', active='addCat', activePage='Add Category', error="Image Is Mandatory To Add A Category", categories=allCategories)
            else:
                return render_template('admin/addCategory.html', active='addCat', activePage='Add Category', error="Category Already Exists. Please Add A New One", categories=allCategories)
        except Exception as e:
            print(str(e))
            return render_template('admin/addCategory.html', active='addCat', activePage='Add Category', categories=allCategories)

@app.route("/admin/category/edit/<int:cat_id>/", methods=["GET", "POST"])
@checkAdmin
def editCategory(cat_id):
    allCategories = categories.query.order_by(categories.id).all()
    findCategory = categories.query.filter_by(id=cat_id).first()
    if request.method == 'GET':
        try:
            if allCategories:
                return render_template('admin/editCategory.html', active='editCat', activePage='Edit Category', singleCat = findCategory)
            else:
                return render_template('admin/editCategory.html', active='editCat', activePage='Edit Category', singleCat = findCategory)
        except Exception as e:
            print(str(e))
            return render_template('admin/editCategory.html', active='editCat', activePage='Edit Category')
    else:
        try:
            catName = request.form.get('catName')
            checkIfCatExists = categories.query.filter_by(name=catName).first()
            if checkIfCatExists is None:
                if 'catImg' in request.files:
                    UPLOAD_FOLDER = 'static/uploads'
                    ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg', 'webp'}
                    catImg = request.files['catImg']
                    if catImg.filename == '':
                        print('filename is empty')
                        findCategory.name = catName
                        db.session.commit()
                        return render_template('admin/editCategory.html', activePage='Edit Category', success="Category Updated Successfully", categories=allCategories, singleCat=findCategory, active='editCat')
                    else:
                        if('.' in catImg.filename and catImg.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
                            file_uuid = secure_filename(str(uuid.uuid4())+'.'+catImg.filename.rsplit('.', 1)[1].lower())
                            catImg.save(os.path.join(UPLOAD_FOLDER, file_uuid))
                            findCategory.name = catName
                            findCategory.image = file_uuid
                            findCategory.created_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
                            db.session.commit()
                            return render_template('admin/editCategory.html', success="Category Has Been Updated Succesfully.", activePage='Add Category', categories=allCategories, singleCat=findCategory, active='editCat')
                        else:
                            return render_template('admin/editCategory.html', activePage='Edit Category', error="Only Images Are Allowed.", categories=allCategories, singleCat=findCategory, active='editCat')
                else:
                    return render_template('admin/editCategory.html', activePage='Edit Category', error="Image Is Mandatory To Add A Category", categories=allCategories, singleCat=findCategory, active='editCat')

            else:
                print('in else')
                return render_template('admin/editCategory.html', activePage='Edit Category', error="Category With This Name Already Exists. Please Use A New One", categories=allCategories, singleCat = findCategory, active='editCat')
        except Exception as e:
            print(str(e))
            return render_template('admin/editCategory.html', activePage='Edit Category', error=str(e), singleCat = findCategory, active='editCat')

@app.route("/admin/category/delete/<int:cat_id>/", methods=["GET"])
@checkAdmin
def deleteCategory(cat_id):
    # delete products related to category
    try:
        getAllProducts = Products.query.filter_by(category_id=cat_id).delete()
        catDetails = categories.query.filter_by(id=cat_id).delete()
        db.session.commit()
        if catDetails:
            flash('Category Deleted Successfully.' ,'success')
            return redirect(url_for('addCategory'))
        else:
            flash('Failed To Delete Category.' ,'danger')
            return redirect(url_for('addCategory'))
    except Exception as e:
        print(str(e))
        flash('Some Exception Occured.' ,'danger')
        return redirect(url_for('addCategory'))


# ! Admin Product Routes
@app.route("/admin/product/add/", methods=["GET", "POST"])
@checkAdmin
def addProduct():
    if(request.method == "GET"):
        allProducts = Products.query.order_by(Products.id).all()
        allCategories = categories.query.order_by(categories.id.desc()).all()
        return render_template('admin/addProduct.html', products=allProducts, activePage="Add Product", active="addProd", categories=allCategories)
    else:

        # For Template Variables
        allProducts = Products.query.order_by(Products.id).all()
        allCategories = categories.query.order_by(categories.id.desc()).all()

        # Form Data
        name = request.form.get('productName')
        cat_id = request.form.get('cat_id')
        price = request.form.get('price')
        stock = request.form.get('stock')
        files = request.files.getlist("catImg")
        slug = slugify(name)

        # Upload Files
        checkSLugExists = Products.query.filter_by(slug=slug).first()
        UPLOAD_FOLDER = 'static/uploads/products'
        ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg', 'webp'}
        catImg = files

        # image upload process
        if 'catImg' in request.files:
            if catImg is None:
                return render_template('admin/addProduct.html', products=allProducts, error="Image Is Mandatory To Add A Product", activePage="Add Product", active="addProd", categories=allCategories)
            else:
                images = ""
                for singleImage in catImg:
                    if('.' in singleImage.filename and singleImage.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
                        file_uuid = secure_filename(str(uuid.uuid4())+'.'+singleImage.filename.rsplit('.', 1)[1].lower())
                        singleImage.save(os.path.join(UPLOAD_FOLDER, file_uuid))
                        images += str('uploads/products/'+file_uuid) + ','
        else:
            return render_template('admin/addProduct.html', active='addProd', activePage='Add Product', error="Image Is Mandatory To Add A Product", categories=allCategories)           
        
        # DB Insertion
        if checkSLugExists is None:
            newProduct = Products( name = name, slug = slug, price = price, stock = stock, category_id = cat_id, image = images, created_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S") )   
        else:
            number = random.randint(1111,9999)
            slug = slugify(name) + '-' + str(number)
            newProduct = Products( name = name, slug = slug, price = price, stock = stock, category_id = cat_id, image = images, created_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S") ) 

        db.session.add(newProduct)
        db.session.commit()
        # Check Final Status  
        if newProduct:
            # Refresh New Product
            allProducts = Products.query.order_by(Products.id.desc()).all()
            return render_template('admin/addProduct.html', products=allProducts, success="Product Added Successfully.", activePage="Add Product", active="addProd", categories=allCategories)
        else:
            return render_template('admin/addProduct.html', active='addProd', activePage='Add Product', error="Failed To Add Product.", categories=allCategories)           

@app.route("/admin/product/edit/<string:slug>/", methods=["GET", "POST"])
@checkAdmin
def editProduct(slug):
    try:
        if(request.method == "GET"):
            searchedProduct = Products.query.filter_by(slug=slug).first()
            allCategories = categories.query.order_by(categories.id.desc()).all()
            if searchedProduct:
                return render_template('admin/editProduct.html', product=searchedProduct, activePage="Edit Product", active="editProd", categories=allCategories)
            else:
                return redirect(url_for('addProduct'))
        else:

            # For Template Variables
            searchedProduct = Products.query.filter_by(slug=slug).first()
            allCategories = categories.query.order_by(categories.id.desc()).all()

            # Form Data
            name = request.form.get('productName')
            cat_id = request.form.get('cat_id')
            price = request.form.get('price')
            stock = request.form.get('stock')
            files = request.files.getlist("catImg")
            slug = slugify(name)

            # Upload Files
            checkSLugExists = Products.query.filter_by(slug=slug).first()
            UPLOAD_FOLDER = 'static/uploads/products'
            ALLOWED_EXTENSIONS = { 'png', 'jpg', 'jpeg', 'webp'}
            catImg = files

            # image upload process
            if 'catImg' in request.files and not any(f for f in files):
                print('empty')
                searchedProduct.name = name
                searchedProduct.category_id = cat_id
                searchedProduct.price = price
                searchedProduct.stock = stock
            else:
                print('n empty')
                print(catImg)
                images = ""
                for singleImage in catImg:
                    if('.' in singleImage.filename and singleImage.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS):
                        file_uuid = secure_filename(str(uuid.uuid4())+'.'+singleImage.filename.rsplit('.', 1)[1].lower())
                        singleImage.save(os.path.join(UPLOAD_FOLDER, file_uuid))
                        images += str('uploads/products/'+file_uuid) + ','
                # update others except image
                searchedProduct.name = name
                searchedProduct.category_id = cat_id
                searchedProduct.price = price
                searchedProduct.stock = stock
                searchedProduct.image = images
            # DB Commit

            # check for slug changes
            if checkSLugExists is not None:
                number = random.randint(1111,9999)
                slug = slugify(name) + '-' + str(number)
                searchedProduct.slug = slug
            db.session.commit()
            # Check Final Status  
            return render_template('admin/editProduct.html', product=searchedProduct, success="Product Updated Successfully.", activePage="Edit Product", active="editProd", categories=allCategories)        
    except Exception as e:
        print(str(e))
        return render_template('admin/editProduct.html', product=searchedProduct, error="Sorry Something went wrong.", activePage="Edit Product", active="editProd", categories=allCategories)        

@app.route("/admin/product/delete/<string:slug>/", methods=["GET"])
@checkAdmin
def deleteProduct(slug):
    # delete products related to category
    try:
        catDetails = Products.query.filter_by(slug=slug).delete()
        db.session.commit()
        if catDetails:
            flash('Product Deleted Successfully.' ,'success')
            return redirect(url_for('addProduct'))
        else:
            flash('Failed To Delete Product.' ,'danger')
            return redirect(url_for('addProduct'))
    except Exception as e:
        print(str(e))
        flash('Some Exception Occured.' ,'danger')
        return redirect(url_for('addProduct'))

# ! ----------------------------------------------------------------------------------
# ! --------------------------------USER ROUTE----------------------------------------
# ! ----------------------------------------------------------------------------------
@app.context_processor
@getCat
@getCart
def inject_category():
    return dict(categories = g.categories, cartCount=str(g.cart))

@app.route("/", methods=['GET'])
def home():
    # allProducts = Products.query.order_by(Products.id.desc()).all()
    products = db.session.query(Products, categories).join(categories, Products.category_id == categories.id).all()
    print(products)
    # Products.query(categories.name.label("category_name"), categories.image.label("category_img"), categories.created_at.label("category_name")).join(categories, Products.category_id == categories.id).order_by(Products.id).all()
    # products = db.session.execute('SELECT products.*, categories.id, categories.name AS cat_name FROM products INNER JOIN categories ON products.category_id=categories.id')
    # Products.query.join(categories, Products.category_id == categories.id).order_by(Products.id).first()
    # print(products.first().cat_name)
    # ? -: Get User Cart Details If logged In
    # TODO -: Login, signup and cart page
    # TODO -: Add To Cart
    # TODO -: Individual Product Page
    # TODO -: Checkout Page
    # TODO -: Payment Gateway Integration

    return render_template('user/index.html', title="Home || Ecom", active='home', products=products)

# ! User Authentication Routes

@app.route("/login", methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        if "token" in session:
            return redirect('home')
        else:
            return render_template('user/login.html', title="Login")
    else:
        try:
            # ! Get Form Details
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
                errMsg = "Username Or Password Can't be Empty."
                return render_template('user/login.html', error=errMsg)
            else:
                findUserByEmail = users.query.filter_by(email = username, usertype="users").first()
                findUserByMobile = users.query.filter_by(mobile = username, usertype="users").first()
                if findUserByEmail:
                    isValidPass = check_password_hash(findUserByEmail.password, password)
                    if isValidPass:
                        userDetails = { "id" : findUserByEmail.id, "email" : findUserByEmail.email }
                        jwtToken = jwt.encode(userDetails, jwt_secret, algorithm='HS256')
                        insertToken = tokens(user_id = findUserByEmail.id, token = jwtToken)
                        db.session.add(insertToken)
                        db.session.commit()
                        session['token'] = jwtToken
                        return redirect(url_for('home')) 
                    else: 
                        errMsg = "Incorrect Username or Password."
                        return render_template('user/login.html', error=errMsg)
                elif findUserByMobile:
                    isValidPass = check_password_hash(findUserByMobile.password, password)
                    if isValidPass:
                        userDetails = { "id" : findUserByMobile.id, "email" : findUserByMobile.email }
                        jwtToken = jwt.encode(userDetails, jwt_secret, algorithm='HS256')
                        insertToken = tokens(user_id = findUserByMobile.id, token = jwtToken)
                        db.session.add(insertToken)
                        db.session.commit()
                        session['token'] = jwtToken
                        return redirect(url_for('home')) 
                    else:
                        errMsg = "Incorrect Username or Password."
                        return render_template('user/login.html', error=errMsg)
                else:
                    errMsg = "Incorrect Username or Password."
                    return render_template('user/login.html', error=errMsg)            
        except Exception as coreError:
            errMsg = "Sorry! Something went wrong."
            return render_template('user/login.html', error=errMsg, original=str(coreError))


@app.route("/signup", methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        if "token" in session:
            return redirect('home')
        else:
            return render_template('user/signup.html', title="Sign Up")
    else:
        try:
            # ! Get Form Details
            # ! sms otp verification
            # ! Successfully signup
            username = request.form.get('username')
            password = request.form.get('password')
            if not username or not password:
                errMsg = "Username Or Password Can't be Empty."
                return render_template('user/login.html', error=errMsg)
            else:
                findUserByEmail = users.query.filter_by(email = username, usertype="users").first()
                findUserByMobile = users.query.filter_by(mobile = username, usertype="users").first()
                if findUserByEmail:
                    isValidPass = check_password_hash(findUserByEmail.password, password)
                    if isValidPass:
                        userDetails = { "id" : findUserByEmail.id, "email" : findUserByEmail.email }
                        jwtToken = jwt.encode(userDetails, jwt_secret, algorithm='HS256')
                        insertToken = tokens(user_id = findUserByEmail.id, token = jwtToken)
                        db.session.add(insertToken)
                        db.session.commit()
                        session['token'] = jwtToken
                        return redirect(url_for('home')) 
                    else: 
                        errMsg = "Incorrect Username or Password."
                        return render_template('user/login.html', error=errMsg)
                elif findUserByMobile:
                    isValidPass = check_password_hash(findUserByMobile.password, password)
                    if isValidPass:
                        userDetails = { "id" : findUserByMobile.id, "email" : findUserByMobile.email }
                        jwtToken = jwt.encode(userDetails, jwt_secret, algorithm='HS256')
                        insertToken = tokens(user_id = findUserByMobile.id, token = jwtToken)
                        db.session.add(insertToken)
                        db.session.commit()
                        session['token'] = jwtToken
                        return redirect(url_for('home')) 
                    else:
                        errMsg = "Incorrect Username or Password."
                        return render_template('user/login.html', error=errMsg)
                else:
                    errMsg = "Incorrect Username or Password."
                    return render_template('user/login.html', error=errMsg)            
        except Exception as coreError:
            errMsg = "Sorry! Something went wrong."
            return render_template('user/login.html', error=errMsg, original=str(coreError))

@app.route("/logout", methods=['GET'])
def logout():
    session.clear()
    flash('Successfully Logged Out.', 'success')
    return redirect('login')

# ! User Rest APIS

@app.route('/api/verify/mobile/', methods=['POST'])
def sendOtp():
    try:
        payload = request.json
        if "mobile" in payload:
            if len(payload['mobile']) == 10:
                otp = str(random.randint(111111,999999))
                session['otp'] = otp
                text = "Dear User, Use this OTP To Verify Your Mobile Number %s" % otp
                url = 'http://sms.bpcc.org.in/API/pushsms.aspx?loginID=%s&password=%s&mobile=%s&text=%s&senderid=%s&route_id=2&Unicode=0&IP=&Template_id=1207161831449029662' % (SMS_GATEWAY_UID, SMS_GATEWAY_PASS, payload['mobile'], text, SG_SENDER_ID)
                r = requests.get(url)
                print(r.status_code)
                return jsonify({ "message": "OTP Has Been Sent Successfully." })
            else:
                return jsonify({ "message": "Invalid Mobile Number." }), 400
        else:
            return jsonify({ "message": "Invalid Mobile Number Passed." }), 400
    except Exception as e:
        print(str(e))
        return jsonify({ "message": "Sorry! Something went wrong" }), 500

@app.route('/api/verify/otp/', methods=['POST'])
def verifyOtp():
    try:
        payload = request.json
        if "otp" in payload:
            if session['otp'] == payload["otp"]:
                return jsonify({ "message": "Verified Successfully." })
            else:
                return jsonify({ "message": "Incorrect OTP." }), 400
        else:
            return jsonify({ "message": "Please Send Otp with your request." }), 400
    except Exception as e:
        print(str(e))
        return jsonify({ "message": "Sorry! Something went wrong" }), 500


# ! User Authenticated Routes

#  CART
@app.route("/api/cart/add", methods=["POST"])
@checkApiAuth
def addToCart():
    try:
        payload = request.json
        print(payload)
        if "product_id" in payload:
            findProduct = Products.query.get(payload["product_id"])
            if findProduct:
                price = findProduct.price
                if "quantity" in payload:
                    # TODO - Calculate Amount
                    totalAmt = int(payload['quantity']) * float(price)
                    newCart = Cart( product_id = payload['product_id'], user_id = g.user['id'], qty = payload['quantity'], amount = totalAmt, created_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S") )
                else:
                    totalAmt = int(1) * float(price)
                    newCart = Cart( product_id = payload['product_id'], user_id = g.user['id'], qty = 1, amount = totalAmt, created_at = datetime.now().strftime("%d/%m/%Y %H:%M:%S") )
            else:
                return jsonify({ "message": "Failed To Add. No Product Exist With That id." }), 500
            
            try:
                db.session.add(newCart)
                db.session.commit()
                if newCart:
                    # fetch cart count for user
                    getCart = Cart.query.filter_by(user_id = g.user['id']).count()
                    payload['cartItems'] = getCart
                    payload['message'] = "Added To Cart Successfully"
                    return payload, 200
                else:
                    return jsonify({ "message": "Failed To Add To Cart" }), 500
            except Exception as e:
                print(e)
                return jsonify({ "error": "Sorry! Something went wrong while adding to cart."}), 500
        else:
            return jsonify({"error": "Invalid Data. Please send product id, user id to create a cart item."}), 400
    except Exception as coreError:
        print(coreError)
        return jsonify({ "error": "Sorry! Something went wrong."}), 500



# ! Product Route
@app.route("/product/<string:slug>/", methods=['GET'])
def viewProduct(slug):
    # ! get product details and render
    product = Products.query.filter_by(slug=slug).first()
    if(product):
        # render page
        return render_template('user/product.html', title = product.name, product=product)
    else:
        # render 404 page
        return ""

# ! Run App In Debug Mode
app.run(debug=True)
