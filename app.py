from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy import text
from email.message import EmailMessage
import boto3
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# AWS Config
AWS_REGION = os.getenv('AWS_REGION')
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN')
sns = boto3.client('sns', region_name=AWS_REGION)
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
users_table = dynamodb.Table('Users')
orders_table = dynamodb.Table('Orders')
products_table = dynamodb.Table('Products')
cart_table = dynamodb.Table('Cart')

# Email Config
EMAIL_ADDRESS = os.getenv('228x1a1240@khitguntur.ac.in')
EMAIL_PASSWORD = os.getenv('znsq vwkt gjlw zijw')

# Helper Functions
def send_email(subject, body, to):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = EMAIL_ADDRESS
    msg['To'] = to
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            smtp.send_message(msg)
            print("Email sent.")
    except Exception as e:
        print("Email failed:", e)

def send_sns_notification(message, subject='New Order Notification'):
    try:
        sns.publish(TopicArn=SNS_TOPIC_ARN, Message=message, Subject=subject)
        print("SNS sent.")
    except Exception as e:
        print("SNS failed:", e)

def save_user_to_dynamo(user):
    try:
        users_table.put_item(Item={
            'username': user.username,
            'email': user.email,
            'phone': user.phone or '',
            'registered_at': datetime.utcnow().isoformat()
        })
        print("User saved to DynamoDB.")
    except Exception as e:
        print("User DynamoDB error:", e)

def save_order_to_dynamo(user, order):
    try:
        orders_table.put_item(Item={
            'order_id': str(order.id),
            'username': user.username,
            'total': order.total,
            'order_date': order.order_date.isoformat()
        })
        print("Order saved to DynamoDB.")
    except Exception as e:
        print("Order DynamoDB error:", e)

# Models
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

# Init DB
with app.app_context():
    db.create_all()

# Session Helper
def get_valid_user():
    if 'user_id' not in session:
        return None
    user = User.query.get(session['user_id'])
    if not user:
        session.pop('user_id', None)
    return user

# Routes
@app.route('/')
def home():
    return render_template('index.html')

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

        save_user_to_dynamo(user)
        save_order_to_dynamo(user, order)

        send_email(
            subject="Order Confirmation",
            body=f"Hello {user.username}, your order #{order.id} has been placed! Total: ₹{total}",
            to=user.email
        )

        send_sns_notification(
            message=f"New order from {user.username} - Order ID: {order.id}, Amount: ₹{total}",
            subject="New Order Received"
        )

        flash('Order placed successfully!', 'success')
        return redirect(url_for('orders'))

    return render_template('checkout.html', cart_items=cart_items, total=total)

# Placeholder: define other routes like login, register, cart, orders...

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
