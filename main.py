from datetime import datetime
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import asc, desc
from wtforms import StringField, PasswordField, validators
from wtforms.validators import InputRequired, Length, Email, EqualTo
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
import os

app = Flask(__name__)

app.config['SECRET_KEY'] = 'tram'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'db/user.db')

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(10), unique=True, nullable=False)
    password = db.Column(db.String(128))
    role = db.Column(db.String(50), default='user', nullable=False)

    def __init__(self, name, email, phone_number, password):
        self.name = name
        self.email = email
        self.phone_number = phone_number
        self.set_password(password)

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def update_profile(self, name, email, phone_number):
        self.name = name
        self.email = email
        self.phone_number = phone_number
        db.session.commit()

        session['current_user']['name'] = name


@app.route('/')
def homepage():
    if 'current_user' in session:
        user_id = session['current_user']['id']
        session['cart'] = len(Cart.query.filter_by(user_id=user_id).all())
    else:
        session['cart'] = 0
    top_products = Product.query.order_by(Product.sell_count.desc()).limit(5).all()
    return render_template('/user/trangchu.html', top_products=top_products)


@app.route('/contact')
def contact():
    return render_template('/user/contact.html')

@app.route('/cauchuyen')
def cauchuyen():
    return render_template('/user/cauchuyen.html')

@app.route('/tracaphechung')
def tracaphechung():
    return render_template('/user/tracaphechung.html')

@app.route('/tra')
def tra():
    return render_template('/user/tra.html')

@app.route('/caphe')
def caphe():
    return render_template('/user/caphe.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        phone_number = request.form['phone_number']
        password = request.form['password']
        user = User.query.filter_by(phone_number=phone_number).first()

        if user and user.check_password(password):
            obj_user = {
                "id": user.id,
                "name": user.name,
                "phone_number": user.phone_number,
                "role": user.role
            }
            session['current_user'] = obj_user
            flash(f'Đăng nhập thành công! Chào mừng {user.name}', 'success')
            return render_template('/user/trangchu.html', show_user_section=True)
        else:
            return render_template('/user/login.html')
    if 'current_user' in session:
        return redirect(url_for('homepage'))
    else:
        return render_template('/user/login.html')


@app.route('/logout')
def logout():
    session.pop('current_user', None)
    return redirect(url_for('homepage'))

class RegistrationForm(FlaskForm):
    name = StringField('Họ và tên', validators=[
        InputRequired(),
        Length(min=3, message="Tên phải có ít nhất 3 ký tự")
    ])
    email = StringField('Email', validators=[
        InputRequired(),
        Email(message="Email không đúng định dạng")
    ])
    phone_number = StringField('Số điện thoại', validators=[
        InputRequired(),
        Length(min=10, max=10, message="Số điện thoại phải có đúng 10 ký tự"),
        validators.Regexp(r'^[0-9]*$', message="Số điện thoại chỉ chứa số")
    ])
    password = PasswordField('Mật khẩu', validators=[
        InputRequired(),
        Length(min=8, message="Mật khẩu phải có ít nhất 8 ký tự")
    ])
    confirm_password = PasswordField('Xác nhận mật khẩu', validators=[
        InputRequired(),
        EqualTo('password', message="Mật khẩu không khớp")
    ])
@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'current_user' in session:
        return redirect(url_for('homepage'))
    else:
        form = RegistrationForm()
        if form.validate_on_submit():
            name = form.name.data
            email = form.email.data
            phone_number = form.phone_number.data
            password = form.password.data

            # Check if the email or phone number is already in use
            if User.query.filter_by(email=email).first() or User.query.filter_by(phone_number=phone_number).first():
                flash('Email or phone number is already in use', 'error')
            else:
                user = User(name, email, phone_number, password)
                user.role = 'user'
                db.session.add(user)
                db.session.commit()
                flash('Đăng ký thành công!', 'success')
                return redirect(url_for('login'))
        return render_template('user/register.html', form=form)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(10), nullable=False)
    city = db.Column(db.String(50))
    shop = db.Column(db.String(100))
    title = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(1000), nullable=False)

    def __init__(self, name, phone_number, city, shop, title, message):
        self.name = name
        self.phone_number = phone_number
        self.city = city
        self.shop = shop
        self.title = title
        self.message = message

@app.route('/submit_contact', methods=['POST'])
def submit_contact():
    if request.method == 'POST':
        name = request.form.get('name')
        phone_number = request.form.get('number')
        city = request.form.get('dinoselect')
        shop = request.form.get('shop')
        title = request.form.get('tieude')
        message = request.form.get('message')

        # Create a new Contact instance and add it to the database
        contact = Contact(name=name, phone_number=phone_number, city=city, shop=shop, title=title, message=message)
        db.session.add(contact)
        db.session.commit()

        return redirect('/contact')

class ProductType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    picture = db.Column(db.String(400), nullable=False)
    products = db.relationship('Product', backref='product_type')

    def delete(self):
        for product in self.products:
            db.session.delete(product)

        db.session.delete(self)
        db.session.commit()

    def update(self, name, picture):
        self.name = name
        self.picture = picture
        db.session.commit()

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(300), nullable=False)
    model = db.Column(db.Integer, db.ForeignKey('product_type.id'), nullable=False)
    picture = db.Column(db.String(400), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    sell_count = db.Column(db.Integer)
    date_added = db.Column(db.DateTime, nullable=False)
    order = db.relationship('OrderItem', backref='product')

def get_product_type_name(product_type_id):
    product_type = ProductType.query.get(product_type_id)
    return product_type.name if product_type else None


@app.route('/product/', defaults={'typeid': None}, methods=['GET'])
@app.route('/product/<int:typeid>/', methods=['GET'])
def product(typeid):
    query = Product.query
    if typeid != None:
        query = query.filter_by(model=typeid)

    sort_by = request.args.get('sort_by', '')
    sort_order = request.args.get('sort_order', '')
    if sort_order == 'asc':
        query = query.order_by(asc(Product.price))
    elif sort_order == 'desc':
        query = query.order_by(desc(Product.price))
    if sort_by == 'times':
        query = query.order_by(desc(Product.sell_count))
    elif sort_by == 'date':
        query = query.order_by(desc(Product.date_added))
    products = query.all()
    return render_template('user/product.html', data=products, drink_types=ProductType.query.all())


@app.route('/product/search',  methods=['POST'])
def search():
    query = Product.query
    if request.method == 'POST':
        search_text = request.form.get('searchInput', '')
        if search_text != '':
            query = query.filter(Product.name.ilike(f"%{search_text}%"))
    products = query.all()
    return render_template('user/product.html', data=products, drink_types=ProductType.query.all(), search_text=search_text)


@app.route('/product/details/<int:productid>/', methods=['GET'])
def product_details(productid):
    product = Product.query.filter_by(id=productid).first()

    all_products = Product.query.all()
    product_names = [p.name for p in all_products]
    vectorizer = TfidfVectorizer()
    product_matrix = vectorizer.fit_transform(product_names)
    current_product_matrix = vectorizer.transform([product.name])
    cosine_similarities = linear_kernel(current_product_matrix, product_matrix).flatten()
    similar_product_indices = cosine_similarities.argsort()[:-6:-1]

    # Get the actual similar products
    similar_products = [all_products[i] for i in similar_product_indices if i != productid]

    return render_template('user/product_details.html', product=product, similar_products=similar_products)

@app.route('/admin/category')
def category():
    product_types = ProductType.query.all()
    return render_template('/admin/category.html', product_types=product_types)


class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    name = db.Column(db.String(300), nullable=False)
    picture = db.Column(db.String(400), nullable=False)
    size = db.Column(db.String(10), nullable=False)
    sugar_level = db.Column(db.String(10), nullable=False)
    ice_place = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    date_added = db.Column(db.DateTime, nullable=False)

@app.route("/cart/add", methods=["POST"])
def add_to_cart():
    if 'current_user' in session:
        user_id = session['current_user']['id']
        product_id = request.form['id']
        size = request.form['size']
        sugar_level = request.form['sugar_level']
        ice_place = request.form['ice_place']
        quantity = int(request.form['quantity'])
        product = Product.query.filter_by(id=product_id).first()

        size_prices = {
            'M': 0,
            'L': 5
        }
        total_price = (product.price + size_prices.get(size, 0)) * quantity

        cart = Cart.query.filter_by(user_id=user_id, product_id=product_id, size=size, sugar_level=sugar_level,
                                    ice_place=ice_place).first()
        if cart:
            cart.quantity += quantity
            cart.total_price += total_price
        else:
            # Nếu sản phẩm chưa có trong giỏ hàng, thêm một bản ghi mới
            cart = Cart(
                user_id=user_id,
                product_id=product_id,
                name=product.name,
                picture=product.picture,
                size=size,
                sugar_level=sugar_level,
                ice_place=ice_place,
                quantity=quantity,
                total_price=total_price,
                date_added=datetime.utcnow()
            )
            db.session.add(cart)

        db.session.commit()

        session['cart'] = len(Cart.query.filter_by(user_id=user_id).all())

        #rows = Cart.query.filter_by(user_id=user_id).count()
        flash(f'Thêm vào giỏ hàng thành công!', 'success')
        return redirect(url_for('product_details', productid=product_id))

    else:
        flash('Bạn chưa đăng nhập!', 'info')
        return redirect(url_for('login'))


@app.route("/cart/")
@app.route("/cart")
def view_cart():
    if 'current_user' in session:
        user_id = session['current_user']['id']

        # Lấy tất cả các mục giỏ hàng cho người dùng hiện tại
        cart_items = Cart.query.filter_by(user_id=user_id).all()

        # Tính tổng giá trị giỏ hàng
        total_cart_value = sum(item.total_price for item in cart_items)

        rows = len(cart_items)
        session['cart'] = rows

        return render_template('/user/cart.html', rows=rows, carts=cart_items, total_cart_value=total_cart_value)
    else:
        return redirect(url_for('login'))


@app.route('/update_cart', methods=['POST'])
def update_cart():
    user_id = session['current_user']['id']
    cart_items = Cart.query.filter_by(user_id=user_id).all()

    for cart_item in cart_items:
        product_id = str(cart_item.id)
        if f'delete-{product_id}' in request.form:
            db.session.delete(cart_item)

    db.session.commit()
    return redirect(url_for('view_cart'))

@app.route('/thanhtoan')
def checkout():
    if 'current_user' in session:
        user_id = session['current_user']['id']
        cart_items = Cart.query.filter_by(user_id=user_id).all()
        if cart_items:
            total_cart_value = sum(item.total_price for item in cart_items)
            rows = len(cart_items)
            user_info = User.query.filter_by(id=user_id).first()
            return render_template('/user/thanhtoan.html', cart_items=cart_items, total_cart_value=total_cart_value, rows=rows, user_info=user_info)
        else:
            return redirect(url_for('view_cart'))
    else:
        return redirect(url_for('login'))


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    phone_number = db.Column(db.String(10), nullable=False)
    address = db.Column(db.String(500), nullable=False)
    products = db.relationship('OrderItem', backref='order')
    total_price = db.Column(db.Float, nullable=False)
    message = db.Column(db.String(300), nullable=True)
    payment_method = db.Column(db.String(300), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    status_id = db.Column(db.Integer, db.ForeignKey('order_status.id'), nullable=False, default=1)


class OrderStatus(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    status_name = db.Column(db.String(255), nullable=False, unique=True)
    status = db.relationship('Order', backref='order_status')

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    product_name = db.Column(db.String(300), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    feature = db.Column(db.String(300), nullable=False)


@app.route('/submit_order', methods=['POST'])
def submit_order():
    if 'current_user' in session:
        user_id = session['current_user']['id']
        name = request.form.get('name')
        phone_number = request.form.get('number')
        address = f"{request.form.get('dinoselect')} - {request.form.get('dinoselect2')} - {request.form.get('dinoselect3')} - {request.form.get('address')}"
        message = request.form.get('message')
        payment_method = request.form.get('dinoselect5')

        # Create a new order instance
        order = Order(user_id=user_id, name=name, phone_number=phone_number, address=address, message=message,
                      payment_method=payment_method, total_price=0, status_id=1)
        db.session.add(order)
        db.session.commit()

        # Add order items to the order
        user_cart_items = Cart.query.filter_by(user_id=user_id).all()
        order_total_price = 0

        for cart_item in user_cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                product_name=cart_item.name,
                quantity=cart_item.quantity,
                total_price=cart_item.total_price,
                feature=f"{cart_item.size} - {cart_item.sugar_level} - {cart_item.ice_place}"
            )
            db.session.add(order_item)
            order_total_price += cart_item.total_price

        # Update the total price of the order
        order.total_price = order_total_price
        db.session.commit()

        # Clear the user's cart after the order is submitted
        Cart.query.filter_by(user_id=user_id).delete()
        db.session.commit()
        session['cart'] = len(Cart.query.filter_by(user_id=user_id).all())
        return render_template('/user/thanhcong.html')

    return render_template('/user/login.html')

@app.route('/order_history/', defaults={'statusid': None}, methods=['GET'])
@app.route('/order_history/<int:statusid>/', methods=['GET'])
def order_history(statusid):
    if 'current_user' in session:
        user_id = session['current_user']['id']
        query = Order.query.filter_by(user_id=user_id)
        if statusid != None:
            query = query.filter_by(status_id=statusid)
        customer_orders = query.all()
        order_statuses = OrderStatus.query.all()
        return render_template('user/order_history.html', orders=customer_orders, order_statuses=order_statuses)
    else:
        return redirect(url_for('login'))


@app.route('/orders/<int:order_id>/')
def order_details(order_id):
    if 'current_user' in session:
        order_items = OrderItem.query.filter_by(order_id=order_id).all()
        order = Order.query.filter_by(id=order_id).first()
        item_images = []
        for order_item in order_items:
            pro = Product.query.filter_by(id=order_item.product_id).first()
            image = pro.picture
            item_images.append(image)
        print(item_images)
        return render_template('user/order_details.html', order=order, order_items=order_items, images=item_images)
    else:
        return redirect(url_for('login'))


# Admin

@app.route('/admin/product')
def index():
    connection = get_db_connection()
    cursor = connection.cursor()
    try:
        cursor.execute('SELECT * from product')
        products = cursor.fetchall()
        print("Products:", products)
    except Exception as e:
        print("Error executing query:", e)
        products = []
    finally:
        connection.close()
    return render_template('admin/product.html', data=products, get_product_type_name=get_product_type_name)


from datetime import datetime, date, timedelta
from sqlalchemy import func
from calendar import monthrange

@app.route('/admin/')
def admin():
    if 'current_user' in session and session['current_user']['role'] == 'admin':
        today = date.today()
        start_of_day = datetime(today.year, today.month, today.day, 0, 0, 0)
        end_of_day = datetime(today.year, today.month, today.day, 23, 59, 59)
        start_of_month = datetime(today.year, today.month, 1, 0, 0, 0)
        last_day_of_month = monthrange(today.year, today.month)[1]
        end_of_month = datetime(today.year, today.month, last_day_of_month, 23, 59, 59)

        total_revenue_today = db.session.query(func.sum(OrderItem.total_price)).\
            join(Order, OrderItem.order_id == Order.id).\
            filter(Order.order_date.between(start_of_day, end_of_day)).scalar()
        total_revenue_month = db.session.query(func.sum(OrderItem.total_price)). \
            join(Order, OrderItem.order_id == Order.id). \
            filter(Order.order_date.between(start_of_month, end_of_month)).scalar()

        start_of_year = datetime(today.year, 1, 1, 0, 0, 0)
        end_of_year = start_of_year + timedelta(days=365)

        total_revenue_year = db.session.query(func.sum(OrderItem.total_price)). \
            join(Order, OrderItem.order_id == Order.id). \
            filter(Order.order_date.between(start_of_year, end_of_year)).scalar()

        total_users = db.session.query(func.count(User.id)).scalar()
        total_orders = db.session.query(func.count(Order.id)).scalar()
        total_products = db.session.query(func.count(Product.id)).scalar()


        return render_template('admin/home.html', total_revenue_today=total_revenue_today,
                               total_revenue_month=total_revenue_month, total_revenue_year=total_revenue_year,
                               total_users=total_users, total_orders=total_orders, total_products=total_products
                               )
    else:
        return redirect(url_for('login'))

db_file = 'db/user.db'
def get_db_connection():
    connection = sqlite3.connect(db_file)
    connection.row_factory = sqlite3.Row
    return connection

# Admin product

@app.route('/add', methods=['GET', 'POST'])
def add():
    if request.method == 'POST':
        name = request.form['name']
        model = request.form['model']
        picture = request.form['picture']
        price = request.form['price']
        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''INSERT INTO product (name, model, picture, price, date_added)
        VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)''',
                       (name, model, picture, price))
        connection.commit()
        connection.close()

        flash('Product added successfully!', 'success')
        return redirect(url_for('index'))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT id, name FROM product_type')
    product_types = cursor.fetchall()
    connection.close()

    product = {
        'name': '',
        'model': '',
        'picture': '',
        'price': '',
    }

    return render_template('admin/add_pro.html', product=product, product_types=product_types)

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM product WHERE id = ?', (id,))
    row = cursor.fetchone()
    connection.close()

    product = dict(row) if row else None

    if request.method == 'POST':
        name = request.form['name']
        model = request.form['model']
        picture = request.form['picture']
        price = request.form['price']

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute('''UPDATE product SET name=?, model=?,
        picture=?, price=? WHERE id=?''',
                       (name, model, picture, price, id))
        connection.commit()
        connection.close()

        flash('Product updated successfully!', 'success')
        return redirect(url_for('index'))

    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT id, name FROM product_type')
    product_types = cursor.fetchall()
    connection.close()

    return render_template('admin/edit_pro.html', product=product, product_types=product_types)

@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    connection = get_db_connection()
    cursor = connection.cursor()
    cursor.execute('SELECT * FROM order_item where product_id = ?', (id,))
    order = cursor.fetchall()
    if order:
        flash('Không thể xóa vì sản phẩm đã được đặt hàng!', 'warning')
    else:
        cursor.execute('DELETE FROM product WHERE id = ?', (id,))
        connection.commit()
        flash('Product deleted successfully!', 'success')

    connection.close()

    return redirect(url_for('index'))

# Admin users

@app.route('/admin/users')
def view_users():
    if 'current_user' in session and session['current_user']['role'] == 'admin':
        users = User.query.all()
        return render_template('admin/view_users.html', users=users)
    else:
        return redirect(url_for('login'))

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    if 'current_user' in session and session['current_user']['role'] == 'admin':
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            flash('User deleted successfully!', 'success')
        else:
            flash('User not found!', 'danger')

        return redirect(url_for('view_users'))
    else:
        return redirect(url_for('login'))

@app.route('/admin/update_role/<int:user_id>/<new_role>', methods=['POST'])
def update_role(user_id, new_role):
    if 'current_user' in session and session['current_user']['role'] == 'admin':
        user = User.query.get(user_id)
        if user:
            user.role = new_role
            db.session.commit()
            flash(f'User role updated to {new_role} successfully!', 'success')
        else:
            flash('User not found!', 'danger')

        return redirect(url_for('view_users'))
    else:
        return redirect(url_for('login'))


@app.route('/edit_type/<int:type_id>', methods=['GET', 'POST'])
def edit_type(type_id):
    product_type = ProductType.query.get(type_id)

    if request.method == 'POST':
        name = request.form['name']
        picture = request.form['picture']
        product_type.update(name, picture)
        flash('Product type updated successfully!', 'success')
        return redirect(url_for('category'))
    return render_template('admin/edit_cat.html', product_type=product_type)

@app.route('/delete_type/<int:type_id>', methods=['POST'])
def delete_type(type_id):
    product_type = ProductType.query.get(type_id)
    if product_type:
        product_type.delete()
        flash('Product type deleted successfully!', 'success')
    else:
        flash('Product type not found!', 'danger')

    return redirect(url_for('category'))

@app.route('/admin/add_type', methods=['GET', 'POST'])
def add_type():
    if request.method == 'POST':
        name = request.form['name']
        picture = request.form['picture']

        new_type = ProductType(name=name, picture=picture)
        db.session.add(new_type)
        db.session.commit()

        flash('Product type added successfully!', 'success')
        return redirect(url_for('category'))

    return render_template('admin/add.cat.html')

@app.route('/admin/orders')
def view_orders():
    if 'current_user' in session and session['current_user']['role'] == 'admin':
        orders = Order.query.all()
        order_statuses = OrderStatus.query.all()
        return render_template('admin/view_orders.html', orders=orders, order_statuses=order_statuses)
    else:
        return redirect(url_for('login'))

@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    if 'current_user' in session and session['current_user']['role'] == 'admin':
        new_status_str = request.form.get('new_status')
        if new_status_str is not None:
            new_status_id = int(new_status_str)

            order = Order.query.get(order_id)
            if order:
                if order.status_id == 1:  # Assuming 1 is 'Đang thực hiện'
                    # Check if the new status is valid (either 'Đã nhận hàng' or 'Đã hủy')
                    if new_status_id in [2, 3]:  # Assuming 2 is 'Đã nhận hàng' and 3 is 'Đã hủy'
                        order.status_id = new_status_id
                        db.session.commit()
                        flash('Order status updated successfully!', 'success')
                        if new_status_id == 2:
                            return redirect(url_for('update_product', orderid=order.id))
                    else:
                        flash('Invalid new status!', 'danger')
                else:
                    flash('Order status can only be updated from "Đang thực hiện"!', 'danger')
            else:
                flash('Order not found!', 'danger')
                return redirect(url_for('view_orders'))
        return redirect(url_for('view_orders'))
    else:
        return redirect(url_for('login'))

@app.route('/admin/update_product/<int:orderid>')
def update_product(orderid):
    if 'current_user' in session and session['current_user']['role'] == 'admin':
        products = OrderItem.query.filter_by(order_id=orderid).all()
        for product in products:
            pro = Product.query.filter_by(id=product.product_id).first()
            pro.sell_count += product.quantity
            db.session.commit()
        flash('Product sold quantity updated successfully!', 'success')
        return redirect(url_for('view_orders'))
    else:
        return redirect(url_for('login'))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'current_user' in session:
        user_id = session['current_user']['id']
        user = User.query.get(user_id)

        if request.method == 'POST':
            name = request.form['name']
            email = request.form['email']
            phone_number = request.form['phone_number']

            user.update_profile(name, email, phone_number)

            flash('Profile updated successfully!', 'success')
            return redirect(url_for('profile'))

        return render_template('user/update_profile.html', user=user)
    else:
        flash('You need to log in!', 'info')
        return redirect(url_for('login'))


class ProductView(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    product_id = db.Column(db.Integer, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, user_id, product_id):
        self.user_id = user_id
        self.product_id = product_id


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)