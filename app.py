from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secure-key-here'  # Replace with a secure key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pickles.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(20))

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=False)
    image = db.Column(db.String(100), nullable=False)
    category = db.Column(db.String(50), nullable=False)

class Cart(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    product = db.relationship('Product', backref='carts', lazy=True)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    order_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    product = db.relationship('Product', backref='order_items', lazy=True)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    message = db.Column(db.Text, nullable=False)
    submitted_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

# Initialize database and update schema
with app.app_context():
    # Create tables
    db.create_all()
    # Check if 'category' column exists in 'product' table
    result = db.session.execute(text("PRAGMA table_info(product)")).fetchall()
    columns = [col[1] for col in result]
    if 'category' not in columns:
        db.session.execute(text('ALTER TABLE product ADD COLUMN category TEXT NOT NULL DEFAULT "Veg Pickles"'))
        db.session.commit()
    # Update existing products and seed new ones
    existing_products = Product.query.all()
    product_names = [p.name for p in existing_products]
    products_to_add = [
        Product(name="Spicy Mango Pickle", price=497.17, description="Tangy and spicy mango pickle made with fresh mangoes.", image="mango.jpg", category="Veg Pickles"),
        Product(name="Garlic Dill Pickle", price=414.17, description="Crunchy pickles with a hint of garlic and dill.", image="dill.jpg", category="Veg Pickles"),
        Product(name="Sweet Gherkins", price=538.67, description="Sweet and crispy gherkins, perfect for snacking.", image="gherkin.jpg", category="Veg Pickles"),
        Product(name="Classic Bread & Butter", price=456.67, description="Sweet and tangy slices, perfect for sandwiches.", image="bread_butter.jpg", category="Veg Pickles"),
        Product(name="Fiery Habanero Pickle", price=580.17, description="Spicy pickles with shrimp and habanero kick.", image="habanero.jpg", category="Veg Pickles"),
        Product(name="Lemon Ginger Pickle", price=522.07, description="Zesty pickle with a refreshing lemon-ginger twist.", image="lemon_ginger.jpg", category="Veg Pickles"),
        Product(name="Beetroot Pickle", price=480.57, description="Earthy and vibrant beet pickles, rich in flavor.", image="beetroot.jpg", category="Veg Pickles"),
        Product(name="Spicy Garlic Pickle", price=497.17, description="Pickles with anchovy and fiery garlic spice.", image="spicy_garlic.jpg", category="Veg Pickles"),
        Product(name="Sweet Onion Pickle", price=456.67, description="Mildly sweet pickles with caramelized onion notes.", image="sweet_onion.jpg", category="Veg Pickles"),
        Product(name="Jalapeño Dill Pickle", price=538.67, description="Dill pickles with a spicy jalapeño punch.", image="jalapeno_dill.jpg", category="Veg Pickles"),
        Product(name="Mustard Seed Pickle", price=489.47, description="Tangy pickles with a bold mustard seed crunch.", image="mustard_seed.jpg", category="Veg Pickles"),
        Product(name="Turmeric Cauliflower", price=513.77, description="Crunchy cauliflower pickles with turmeric flavor.", image="turmeric_cauli.jpg", category="Veg Pickles"),
        Product(name="Mixed Veggie Pickle", price=530.37, description="A colorful medley of pickled vegetables.", image="mixed_veggie.jpg", category="Veg Pickles"),
        Product(name="Masala Peanuts", price=150.00, description="Crunchy peanuts tossed in spicy masala.", image="masala_peanuts.jpg", category="Snacks"),
        Product(name="Chakli", price=200.00, description="Crispy spiral snacks with cumin and sesame.", image="chakli.jpg", category="Snacks"),
        Product(name="Spicy Sev", price=180.00, description="Thin, spicy gram flour noodles, perfect for snacking.", image="sev.jpg", category="Snacks"),
        Product(name="Banana Chips", price=220.00, description="Crispy banana chips with a hint of salt.", image="banana_chips.jpg", category="Snacks"),
        Product(name="Roasted Chana", price=170.00, description="Roasted chickpeas with tangy spices.", image="roasted_chana.jpg", category="Snacks"),
        Product(name="Fish Pickle", price=525.50, description="Traditional spicy fish pickle made with fresh seer fish and aromatic spices.", image="fish.jpg", category="Non-veg Pickles"),
        Product(name="Prawn Pickle", price=610.75, description="Delicious prawn pickle bursting with coastal flavors and a fiery spice blend.", image="prawn.jpg", category="Non-veg Pickles"),
        Product(name="Chicken Pickle", price=450.00, description="Succulent chicken pieces pickled in spicy masalas and mustard oil.", image="chicken.jpg", category="Non-veg Pickles"),
        Product(name="Mutton Pickle", price=680.25, description="Rich and spicy mutton pickle cooked with authentic spices for a robust taste.", image="mutton.jpg", category="Non-veg Pickles"),
        Product(name="Crab Pickle", price=745.30, description="Unique crab pickle with tender crab meat and a bold, spicy marinade.", image="crab.jpg", category="Non-veg Pickles"),
        Product(name="Beef Pickle", price=590.00, description="Kerala-style beef pickle with juicy beef chunks in a spicy, tangy masala.", image="beef.jpg", category="Non-veg Pickles"),
        Product(name="Squid Pickle", price=530.40, description="Soft squid pieces pickled in a spicy blend of coastal flavors.", image="squid.jpg", category="Non-veg Pickles"),
        Product(name="Dry Fish Pickle", price=475.20, description="Crispy dry fish pickle with intense flavors and a spicy, tangy finish.", image="dryfish.jpg", category="Non-veg Pickles"),
        Product(name="Duck Pickle", price=665.90, description="Special duck pickle made with traditional spices and a rich, flavorful gravy.", image="duck.jpg", category="Non-veg Pickles"),
        Product(name="Quail Pickle", price=710.15, description="Exotic quail meat pickle infused with aromatic spices and chili oil.", image="quail.jpg", category="Non-veg Pickles"),

    ]
    # Add only new products
    new_products = [p for p in products_to_add if p.name not in product_names]
    if new_products:
        db.session.bulk_save_objects(new_products)
    # Update existing products
    for product in existing_products:
        for new_product in products_to_add:
            if product.name == new_product.name:
                product.price = new_product.price
                product.description = new_product.description
                product.image = new_product.image
                product.category = new_product.category
    db.session.commit()

# Helper function to validate user session
def get_valid_user():
    if 'user_id' not in session:
        return None
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
    return user

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/veg-pickles')
def veg_pickles():
    products = Product.query.filter_by(category="Veg Pickles").all()
    return render_template('veg_pickles.html', products=products)

@app.route('/non-veg-pickles')
def non_veg_pickles():
    products = Product.query.filter_by(category="Non-veg Pickles").all()
    return render_template('non_veg_pickles.html', products=products)

@app.route('/snacks')
def snacks():
    products = Product.query.filter_by(category="Snacks").all()
    return render_template('snacks.html', products=products)

@app.route('/product/<int:id>')
def product_detail(id):
    product = Product.query.get_or_404(id)
    return render_template('product.html', product=product)

@app.route('/cart')
def cart():
    user = get_valid_user()
    if not user:
        flash('Please login to view your cart', 'error')
        return redirect(url_for('login'))
    
    cart_items = Cart.query.filter_by(user_id=user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    user = get_valid_user()
    if not user:
        flash('Please login to add items to cart', 'error')
        return redirect(url_for('login'))
    
    quantity = int(request.form.get('quantity', 1))
    cart_item = Cart.query.filter_by(user_id=user.id, product_id=product_id).first()
    
    if cart_item:
        cart_item.quantity += quantity
    else:
        cart_item = Cart(user_id=user.id, product_id=product_id, quantity=quantity)
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Item added to cart', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    user = get_valid_user()
    if not user:
        flash('Please login to checkout', 'error')
        return redirect(url_for('login'))
    
    cart_items = Cart.query.filter_by(user_id=user.id).all()
    if not cart_items:
        flash('Your cart is empty', 'error')
        return redirect(url_for('cart'))
    
    total = sum(item.product.price * item.quantity for item in cart_items)
    
    if request.method == 'POST':
        order = Order(user_id=user.id, total=total)
        db.session.add(order)
        db.session.flush()
        
        for item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.product.price
            )
            db.session.add(order_item)
            db.session.delete(item)
        
        db.session.commit()
        flash('Order placed successfully!', 'success')
        return redirect(url_for('orders'))
    
    return render_template('checkout.html', cart_items=cart_items, total=total)

@app.route('/orders')
def orders():
    user = get_valid_user()
    if not user:
        flash('Please login to view your orders', 'error')
        return redirect(url_for('login'))
    
    orders = Order.query.filter_by(user_id=user.id).order_by(Order.order_date.desc()).all()
    return render_template('orders.html', orders=orders)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        contact = Contact(name=name, email=email, message=message)
        db.session.add(contact)
        db.session.commit()
        
        flash('Your message has been saved! We will get back to you soon.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

@app.route('/profile', methods=['GET', 'POST'])
def profile():
    user = get_valid_user()
    if not user:
        flash('Please login to view your profile', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        phone = request.form['phone']
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first() and username != user.username:
            flash('Username already exists', 'error')
        elif User.query.filter_by(email=email).first() and email != user.email:
            flash('Email already exists', 'error')
        else:
            user.username = username
            user.email = email
            user.phone = phone
            if password:
                user.password = generate_password_hash(password)
            db.session.commit()
            flash('Profile updated successfully!', 'success')
        
        return redirect(url_for('profile'))
    
    return render_template('profile.html', user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('Username or email already exists', 'error')
            return redirect(url_for('register'))
        
        user = User(username=username, email=email, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')
    
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully', 'success')
    return redirect(url_for('home'))

@app.route('/remove_from_cart/<int:cart_id>')
def remove_from_cart(cart_id):
    user = get_valid_user()
    if not user:
        flash('Please login to manage your cart', 'error')
        return redirect(url_for('login'))
    
    cart_item = Cart.query.get_or_404(cart_id)
    if cart_item.user_id == user.id:
        db.session.delete(cart_item)
        db.session.commit()
        flash('Item removed from cart', 'success')
    return redirect(url_for('cart'))
with app.app_context():
    seen = set()
    duplicates = []
    nonveg_products = Product.query.filter_by(category="Non-veg Pickles").all()

    for product in nonveg_products:
        key = (product.name.lower(), product.price)
        if key in seen:
            duplicates.append(product)
        else:
            seen.add(key)

    for dup in duplicates:
        db.session.delete(dup)
    db.session.commit()
    print(f"Removed {len(duplicates)} duplicate products.")


if __name__ == '__main__':
    app.run(debug=True)