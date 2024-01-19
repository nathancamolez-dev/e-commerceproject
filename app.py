from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import UserMixin, login_user, LoginManager, login_required, \
    logout_user, current_user


app = Flask(__name__)
app.config['SECRET_KEY'] = 'test'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'

login_manager = LoginManager()
db = SQLAlchemy(app)
login_manager.init_app(app)
login_manager.login_view = 'login'
CORS(app)


class user(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(100), nullable=False)
    cart = db.relationship('CartItem', backref='user', lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    price = db.Column(db.Float, nullable=True)
    description = db.Column(db.Text, nullable=False)


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer,
                        db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer,
                           db.ForeignKey('product.id'), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return user.query.get(int(user_id))


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    userlog = user.query.filter_by(name=data.get("username")).first()

    if userlog and data.get("password") == userlog.password:
        login_user(userlog)
        return jsonify({"message": "Login successful"})
    return jsonify({"message": "Unauthorized. Invalid credentials"}), 401


@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"message": "Logout successful"}), 200


@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    products_list = []
    for product in products:
        pr_data = {
            "id": product.id,
            "name": product.name,
            "price": product.price,
        }
        products_list.append(pr_data)

    return jsonify(products_list)


@app.route('/api/products/add', methods=["POST"])
@login_required
def add_product():
    data = request.json
    if 'name' in data and 'price' in data:
        product = Product(
            name=data['name'],
            price=data['price'],
            description=data.get('description', ''))

        db.session.add(product)
        db.session.commit()
        return jsonify({"message": "Product added successfully"}), 201
    return jsonify({"message": "Invalid product data"}), 400


@app.route('/api/products/delete/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    product = Product.query.get(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": "Product deleted successfully"})
    return jsonify({"message": "Invalid product id"}), 404


@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product_details(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "description": product.description
        })
    return jsonify({"message": "Invalid product id"}), 404


@app.route('/api/products/update/<int:product_id>', methods=['PUT'])
@login_required
def updateProduct(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Invalid product id"}), 404

    data = request.json

    if 'name' in data:
        product.name = data['name']

    if 'price' in data:
        product.price = data['price']

    if 'description' in data:
        product.description = data['description']

    db.session.commit()
    return jsonify({"message": "Product updated"})

# Cart Checkout


@app.route('/api/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    id_user = user.query.get(int(current_user.id))
    product = Product.query.get(product_id)
    if id_user and product:
        cart_item = CartItem(user_id=id_user.id, product_id=product.id)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({'message': 'Item add to the cart successfully'})
    return jsonify({'message': 'Failed to add item to the cart'}), 400


if __name__ == '__main__':
    app.run(debug=True)
