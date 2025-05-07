import hashlib
from flask import Flask, request, render_template, redirect, url_for, send_from_directory, session, flash
import pymysql
import os
from create_coupon import generate_coupon_image  # Assuming this file exists
from functools import wraps
import decimal
import datetime
from flask import send_file
from fpdf import FPDF


app = Flask(__name__)
app.secret_key = 'your_secret_key'
UPLOAD_FOLDER = 'static/product_images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs('temp', exist_ok=True) # Ensure temp folder exists

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    return pymysql.connect(
        host="localhost",
        user="root",
        password="",
        database="discount",
        cursorclass=pymysql.cursors.DictCursor
    )

def generate_hash(data_string):
    return hashlib.sha256(data_string.encode('utf-8')).hexdigest()

def verify_data_integrity(record, uploaded_image_path=None):
    data_string = f"{record['coupon_name']}{record['consumer_name']}{record['consumer_number']}{record['consumer_email']}{record['gender']}{record['discount_amount']}{record['coupon_code']}{record['validity_date']}{record['identity_mark']}"
    new_hash = generate_hash(data_string)

    if new_hash != record['hash_code']:
        return False

    if uploaded_image_path:
        if not compare_images(uploaded_image_path, record['image']):
            return False
    return True

def compare_images(uploaded_image_path, stored_image_filename):
    try:
        with open(uploaded_image_path, "rb") as f:
            uploaded_image_hash = hashlib.sha256(f.read()).hexdigest()
        stored_image_path = os.path.join("static", "images", stored_image_filename)
        with open(stored_image_path, "rb") as f:
            stored_image_hash = hashlib.sha256(f.read()).hexdigest()
        return uploaded_image_hash == stored_image_hash
    except FileNotFoundError:
        return False

def login_required(role=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'role' not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('login'))
            if role is not None and session['role'] != role:
                flash("You do not have permission to access this page.", "danger")
                return redirect(url_for('home'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator

# --- Admin Product Management ---

@app.route("/admin/products")
@login_required(role='admin')
def admin_products():
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Products")
        products = cursor.fetchall()
        return render_template("admin_products.html", products=products)
    finally:
        connection.close()

@app.route("/admin/products/add", methods=["GET", "POST"])
@login_required(role='admin')
def admin_add_product():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        price = request.form["price"]
        stock = request.form["stock"]
        category = request.form["category"]
        image = request.files["image"]

        if image and allowed_file(image.filename):
            filename = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
            image.save(filename)
            image_filename = image.filename
        else:
            image_filename = None

        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            query = "INSERT INTO Products (product_name, description, price, image, stock_quantity, category) VALUES (%s, %s, %s, %s, %s, %s)"
            cursor.execute(query, (name, description, price, image_filename, stock, category))
            connection.commit()
            flash("Product added successfully!", "success")
            return redirect(url_for("admin_products"))
        finally:
            connection.close()
    return render_template("admin_add_product.html")

@app.route("/admin/products/edit/<int:product_id>", methods=["GET", "POST"])
@login_required(role='admin')
def admin_edit_product(product_id):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        if product:
            if request.method == "POST":
                name = request.form["name"]
                description = request.form["description"]
                price = request.form["price"]
                stock = request.form["stock"]
                category = request.form["category"]
                image = request.files["image"]

                if image and allowed_file(image.filename):
                    filename = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
                    image.save(filename)
                    image_filename = image.filename
                else:
                    image_filename = product['image']

                query = "UPDATE Products SET product_name=%s, description=%s, price=%s, image=%s, stock_quantity=%s, category=%s WHERE product_id=%s"
                cursor.execute(query, (name, description, price, image_filename, stock, category, product_id))
                connection.commit()
                flash("Product updated successfully!", "success")
                return redirect(url_for("admin_products"))
            return render_template("admin_edit_product.html", product=product)
        else:
            flash("Product not found!", "danger")
            return redirect(url_for("admin_products"))
    finally:
        connection.close()

@app.route("/admin/products/delete/<int:product_id>")
@login_required(role='admin')
def admin_delete_product(product_id):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("DELETE FROM Products WHERE product_id = %s", (product_id,))
        connection.commit()
        flash("Product deleted successfully!", "success")
    finally:
        connection.close()
    return redirect(url_for("admin_products"))

# --- User Product Display ---

@app.route("/products")
def user_products():
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Products")
        products = cursor.fetchall()
        return render_template("user_products.html", products=products)
    finally:
        connection.close()

@app.route("/product/<int:product_id>")
def product_detail(product_id):
    connection = get_db_connection()
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM Products WHERE product_id = %s", (product_id,))
        product = cursor.fetchone()
        if product:
            return render_template("product_detail.html", product=product)
        else:
            flash("Product not found!", "warning")
            return redirect(url_for("user_products"))
    finally:
        connection.close()

# --- Shopping Cart ---

@app.route("/cart")
def cart():
    cart_items = session.get('cart', {})
    products_in_cart = []
    total_price = 0

    if cart_items:
        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            for product_id, quantity in cart_items.items():
                cursor.execute("SELECT * FROM Products WHERE product_id = %s", (product_id,))
                product = cursor.fetchone()
                if product:
                    total_price += product['price'] * quantity
                    products_in_cart.append({'product': product, 'quantity': quantity})
        finally:
            connection.close()

    return render_template("cart.html", cart_items=products_in_cart, total_price=total_price)

@app.route("/add_to_cart/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    if product_id in cart:
        cart[product_id] += quantity
    else:
        cart[product_id] = quantity
    session['cart'] = cart
    flash("Product added to cart!", "success")
    return redirect(url_for("cart"))

@app.route("/update_cart/<int:product_id>", methods=["POST"])
def update_cart(product_id):
    quantity = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    if product_id in cart:
        if quantity > 0:
            cart[product_id] = quantity
        else:
            del cart[product_id]
    session['cart'] = cart
    flash("Cart updated!", "info")
    return redirect(url_for("cart"))

@app.route("/remove_from_cart/<int:product_id>")
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    if product_id in cart:
        del cart[product_id]
    session['cart'] = cart
    flash("Product removed from cart!", "warning")
    return redirect(url_for("cart"))

# --- Checkout and Coupon Application ---

@app.route("/checkout", methods=["GET", "POST"])
@login_required(role='user')
def checkout():
    cart_items = session.get('cart', {})
    products_in_cart = []
    subtotal = 0
    coupon = session.get('coupon')
    discount_amount = session.get('discount_amount', 0)
    total = 0

    if cart_items:
        connection = get_db_connection()
        try:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            for product_id, quantity in cart_items.items():
                cursor.execute("SELECT * FROM Products WHERE product_id = %s", (product_id,))
                product = cursor.fetchone()
                if product:
                    price = product['price']
                    if not isinstance(price, decimal.Decimal):
                        price = decimal.Decimal(str(price))
                    subtotal += price * quantity
                    products_in_cart.append({'product': product, 'quantity': quantity})

            if discount_amount is not None:
                discount_amount_decimal = decimal.Decimal(str(discount_amount))
                total = subtotal - discount_amount_decimal
            else:
                total = subtotal

        finally:
            connection.close()

    if request.method == "POST":
        if 'apply_coupon' in request.form:  # Check if the "Apply" button was clicked
            coupon_code = request.form.get('coupon_code')
            if coupon_code:
                connection = get_db_connection()
                try:
                    cursor = connection.cursor(pymysql.cursors.DictCursor)
                    cursor.execute("SELECT * FROM EcouponRecords WHERE coupon_code = %s AND validity_date >= CURDATE()", (coupon_code,))
                    coupon_record = cursor.fetchone()
                    if coupon_record:
                        uploaded_image = request.files.get('coupon_image')
                        temp_image_path = None
                        if uploaded_image and allowed_file(uploaded_image.filename):
                            temp_filename = os.path.join("temp", uploaded_image.filename)
                            uploaded_image.save(temp_filename)
                            temp_image_path = temp_filename

                        if temp_image_path is None:
                            if verify_data_integrity(coupon_record):
                                session['coupon'] = coupon_code
                                session['discount_amount'] = float(coupon_record['discount_amount'])
                                flash("Coupon applied successfully!", "success")
                                return redirect(url_for("checkout"))
                            else:
                                flash("Coupon verification failed. It may have been tampered with.", "danger")
                        else:
                            if verify_data_integrity(coupon_record, temp_image_path):
                                session['coupon'] = coupon_code
                                session['discount_amount'] = float(coupon_record['discount_amount'])
                                flash("Coupon applied successfully!", "success")
                                return redirect(url_for("checkout"))
                            else:
                                flash("Coupon verification failed. It may have been tampered with.", "danger")
                                os.remove(temp_image_path)
                    else:
                        flash("Invalid or expired coupon code.", "warning")
                finally:
                    connection.close()
            return redirect(url_for("checkout")) # Redirect after coupon attempt
        elif 'place_order' in request.form: # Check if the "Place Order" button was clicked
            # Simulate order placement
            order_details = {
                'name': session.get('username'),
                'shipping_address': request.form.get('address'),  # Get address from form
                'total_amount': float(total)
            }
            session['order_details'] = order_details
            session['cart'] = {}
            session.pop('coupon', None)
            session.pop('discount_amount', None)
            flash("Order placed successfully!", "success")
            return redirect(url_for('order_confirmation'))

    return render_template("checkout.html", cart_items=products_in_cart, subtotal=subtotal, discount=discount_amount, total=total, coupon_code=session.get('coupon', ''))

@app.route("/order_confirmation")
@login_required(role='user')
def order_confirmation():
    order = session.get('order_details')
    if not order:
        return redirect(url_for('user_dashboard'))  # Redirect if no order details found
    return render_template("order_confirmation.html", order=order, datetime=datetime)

@app.route("/download_bill/<order_id>")
@login_required(role='user')
def download_bill(order_id):
    order_details = session.get('order_details')
    if not order_details:
        flash("Order details not found for generating bill.", "warning")
        return redirect(url_for('user_dashboard'))

    pdf = FPDF()
    pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True) # Register the Unicode font
    pdf.add_page()
    pdf.set_font("DejaVu", size=12) # Set the font to DejaVu

    pdf.cell(200, 10, txt="Order Bill", ln=1, align="C")
    pdf.cell(200, 10, txt=f"Order ID: {order_id}", ln=1, align="L")
    pdf.cell(200, 10, txt=f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=1, align="L")
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Customer Name: {order_details.get('name', 'N/A')}", ln=1, align="L")
    pdf.cell(200, 10, txt=f"Shipping Address: {order_details.get('shipping_address', 'N/A')}", ln=1, align="L")
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Total Amount: ₹{order_details.get('total_amount', '0.00')}", ln=1, align="L")

    pdf_filename = f"bill_{order_id}.pdf"
    pdf_path = f"temp/{pdf_filename}"  # Save temporarily
    pdf.output(pdf_path, "F")

    return send_file(pdf_path, as_attachment=True, download_name=pdf_filename)








@app.route("/remove_coupon")
@login_required(role='user')
def remove_coupon():
    session.pop('coupon', None)
    session.pop('discount_amount', None)
    flash("Coupon removed.", "info")
    return redirect(url_for("checkout"))

# --- Existing Routes (Login, Dashboard, Register, Detect, Logout) ---
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        connection = get_db_connection()
        try:
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            query = "SELECT * FROM Users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()

            if user and user['password'] == password:
                session['user_id'] = user['user_id']
                session['role'] = user['role']
                session['username'] = user['username']
                return redirect(url_for("home"))
            else:
                flash("Invalid credentials, please try again.")
        finally:
            connection.close()
        return render_template("login.html")
    return render_template("login.html")

@app.route("/home")
def home():
    if 'role' in session and session['role'] == 'admin':
        return redirect(url_for('admin_dashboard'))
    elif 'role' in session and session['role'] == 'user':
        return redirect(url_for('user_dashboard'))
    return redirect(url_for('login'))

@app.route('/admin/dashboard')
@login_required(role='admin')
def admin_dashboard():
    connection = get_db_connection()
    try:
        cursor = connection.cursor(pymysql.cursors.DictCursor)  # Use DictCursor

        # Query to get the total number of coupons
        cursor.execute("SELECT COUNT(*) AS total_coupons FROM EcouponRecords")
        total_coupons_result = cursor.fetchone()
        total_coupons = total_coupons_result['total_coupons'] if total_coupons_result else 0

        # Query to get the number of active coupons
        cursor.execute("SELECT COUNT(*) AS active_coupons FROM EcouponRecords WHERE validity_date >= CURDATE()")
        active_coupons_result = cursor.fetchone()
        active_coupons = active_coupons_result['active_coupons'] if active_coupons_result else 0

        # Query to get the number of expired coupons
        cursor.execute("SELECT COUNT(*) AS expired_coupons FROM EcouponRecords WHERE validity_date < CURDATE()")
        expired_coupons_result = cursor.fetchone()
        expired_coupons = expired_coupons_result['expired_coupons'] if expired_coupons_result else 0

        # Query to get the total number of products
        cursor.execute("SELECT COUNT(*) AS total_products FROM Products")
        total_products_result = cursor.fetchone()
        total_products = total_products_result['total_products'] if total_products_result else 0

        return render_template('admin_dashboard.html', total_coupons=total_coupons, active_coupons=active_coupons, expired_coupons=expired_coupons, total_products=total_products)

    finally:
        connection.close()


@app.route("/user_dashboard")
@login_required(role='user')
def user_dashboard():
    return render_template("user_dashboard.html")


@app.route("/detect", methods=["GET", "POST"])
def detect():
    if request.method == "POST":
        coupon_code = request.form["coupon_code"]
        uploaded_image = request.files["image"]
        if uploaded_image and allowed_file(uploaded_image.filename):
            image_path = f"temp/{uploaded_image.filename}"
            uploaded_image.save(image_path)

            connection = get_db_connection()
            try:
                cursor = connection.cursor(pymysql.cursors.DictCursor)
                query = "SELECT * FROM EcouponRecords WHERE coupon_code = %s"
                cursor.execute(query, (coupon_code,))
                record = cursor.fetchone()
            finally:
                connection.close()

            if not record:
                return render_template("detect_result.html", tampered=None, message="E-Coupon Record not found!")

            if verify_data_integrity(record, image_path):
                return render_template("detect_result.html", tampered=False, message="Record is intact!", record=record)
            else:
                return render_template("detect_result.html", tampered=True, message="Data tampering detected!")
        else:
            return render_template("detect_result.html", tampered=None, message="Invalid image format.")
    return render_template("detect.html")


@app.route("/register", methods=["GET", "POST"])
@login_required(role='admin')
def register():
    if request.method == "POST":
        coupon_name = request.form["coupon_name"]
        consumer_name = request.form["consumer_name"]
        consumer_number = request.form["consumer_number"]
        consumer_email = request.form["consumer_email"]
        gender = request.form["gender"]
        discount_amount = request.form["discount_amount"]
        coupon_code = request.form["coupon_code"]
        validity_date = request.form["validity_date"]
        identity_mark = request.form["identity_mark"]
        image = request.files["image"]

        if image and allowed_file(image.filename):
            image_filename = image.filename
            image_path = os.path.join("static", "images", image_filename)
            image.save(image_path)

            data_string = f"{coupon_name}{consumer_name}{consumer_number}{consumer_email}{gender}{discount_amount}{coupon_code}{validity_date}{identity_mark}"
            hash_code = generate_hash(data_string)

            connection = get_db_connection()
            try:
                cursor = connection.cursor()
                query = """
                    INSERT INTO EcouponRecords (coupon_name, consumer_name, consumer_number, consumer_email, gender, discount_amount, coupon_code, validity_date, identity_mark, image, hash_code)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cursor.execute(query, (coupon_name, consumer_name, consumer_number, consumer_email, gender,
                                       discount_amount, coupon_code, validity_date, identity_mark, image_filename, hash_code))
                connection.commit()
                flash("E-Coupon registered successfully!", "success")
                return render_template('blocknumber.html', hash_code=hash_code)
            finally:
                connection.close()
        else:
            flash("Invalid image format.", "danger")
    return render_template("register.html")


@app.route("/user_register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            flash("Passwords do not match.", "danger")
            return redirect(url_for('user_register'))

        connection = get_db_connection()
        try:
            cursor = connection.cursor()
            query = "INSERT INTO Users (username, password, role) VALUES (%s, %s, %s)"
            cursor.execute(query, (username, password, 'user'))
            connection.commit()
            flash("Registration successful. Please login.", "success")
            return redirect(url_for("login"))
        finally:
            connection.close()
    return render_template("user_register.html")


@app.route("/generate_coupon_image", methods=["GET", "POST"])
@login_required(role='admin')
def generate_coupon_image_route():
    if request.method == "POST":
        coupon_code = request.form.get("coupon_code")
        if not coupon_code:
            flash("Please enter a coupon code.", "warning")
            return redirect(url_for("generate_coupon_image_route"))

        filename = f"{coupon_code}.jpg"
        output_path = os.path.join("static", "generated_coupons")
        os.makedirs(output_path, exist_ok=True)

        save_path = os.path.join(output_path, filename)
        generate_coupon_image(coupon_code, save_path)

        image_path = url_for('static', filename=f'generated_coupons/{filename}')
        flash(f"Coupon image generated successfully: {filename}", "success")
        return render_template("coupon_generated.html", image_path=image_path)
    return render_template("generate_coupon_image.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


def handler(request):
    with app.test_request_context(
        path=request.path,
        method=request.method,
        headers=request.headers,
        data=request.body,
        query_string=request.query
    ):
        response = app.full_dispatch_request()
        return response
