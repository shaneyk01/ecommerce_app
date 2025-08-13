from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
from sqlalchemy.orm import DeclarativeBase, relationship, Mapped, mapped_column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey, Table, Column, String, Integer, Float, select
from marshmallow import ValidationError
from typing import List, Optional
# Removed invalid __Future__ import statement


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:Sageyk01!2024@localhost/ECOMMERCE_APP_API'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
db.init_app(app)
ma = Marshmallow(app)

order_products = Table(
    "order_products",
    Base.metadata,
    Column("order_id", ForeignKey("orders.id"), primary_key=True),
    Column("product_id", ForeignKey("products.id"), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(200))
    street_number: Mapped[int] = mapped_column(Integer)
    street_name: Mapped[str] = mapped_column(String(100))
    city: Mapped[str] = mapped_column(String(100))
    state: Mapped[str] = mapped_column(String(100))
    zip_code: Mapped[str] = mapped_column(String(20))

    orders: Mapped[List["Order"]] = relationship("Order", back_populates="user")

class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_date: Mapped[DateTime] = mapped_column(DateTime, nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="orders")
    products: Mapped[List["Product"]] = relationship("Product", secondary=order_products, back_populates="orders")

class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)

    orders: Mapped[List["Order"]] = relationship("Order", secondary=order_products, back_populates="products")

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User

class OrderSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Order
        include_fk = True

class ProductSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Product

User_Schema = UserSchema()
Users_Schema = UserSchema(many=True)
Order_Schema = OrderSchema()
Orders_Schema = OrderSchema(many=True)
Product_Schema = ProductSchema()
Products_Schema = ProductSchema(many=True)

@app.route("/users", methods = ["POST"])
def create_user():
    try:
        user_data = User_Schema.load(request.json)
        
        new_user = User(
            name=user_data['name'],
            email=user_data['email'],
            street_number=user_data['street_number'],
            street_name=user_data['street_name'],
            city=user_data['city'],
            state=user_data['state'],
            zip_code=user_data['zip_code']
        )
        db.session.add(new_user)
        db.session.commit()
        
        return User_Schema.jsonify(new_user), 201
        
    except ValidationError as e:
        print("Validation error:", e.messages)  # Debug logging
        return jsonify({"validation_errors": e.messages}), 400
    except Exception as e:
        print("Other error:", str(e))
        return jsonify({"error": str(e)}), 500
    

@app.route("/users", methods = ["GET"])
def get_users():
    users = db.session.execute(db.select(User)).scalars().all()
    return Users_Schema.jsonify(users)  

@app.route("/users/<int:id>", methods = ["GET"])
def get_user(id):
    user = db.session.get(User, id)
    if user:
        return User_Schema.jsonify(user)
    return {"message": "User not found"}, 404


@app.route("/users/<int:id>", methods=["PUT"])
def update_user(id):
    print(f"PUT request for user ID: {id}")  # Debug logging
    
    user = db.session.get(User, id)
    if not user:
        print(f"User with ID {id} not found")  # Debug logging
        return jsonify({"message": "User not found"}), 404

    print(f"Request data: {request.json}")  # Debug logging
    
    try:
        user_data = User_Schema.load(request.json, partial=True)
        print(f"Loaded data: {user_data}")  # Debug logging
    except ValidationError as e:
        print(f"Validation error: {e.messages}")  # Debug logging
        return jsonify({"validation_errors": e.messages}), 400
    
    # Update user fields
    for field, value in user_data.items():
        setattr(user, field, value)
        print(f"Updated {field} to {value}")  # Debug logging

    db.session.commit()
    print("User updated successfully")  # Debug logging
    return User_Schema.jsonify(user), 200



@app.route("/users/<int:id>", methods=["DELETE"])
def delete_user(id):
    user = db.session.get(User, id)
    if not user:
        return jsonify({"message": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200

@app.route("/products", methods=["POST"])
def create_product():
    try:
        product_data = Product_Schema.load(request.json)
        
        new_product = Product(
            name=product_data['name'],
            price=product_data['price']
        )
        db.session.add(new_product)
        db.session.commit()
        
        return Product_Schema.jsonify(new_product), 201
        
    except ValidationError as e:
        return jsonify({"validation_errors": e.messages}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/products", methods=["GET"])
def get_products():
    products = db.session.execute(db.select(Product)).scalars().all()
    return Products_Schema.jsonify(products)

@app.route("/products/<int:id>", methods=["GET"])
def get_product(id):
    product = db.session.get(Product, id)
    if product:
        return Product_Schema.jsonify(product)
    return {"message": "Product not found"}, 404

@app.route("/products/<int:id>", methods=["PUT"])
def update_product(id):
    product = db.session.get(Product, id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    try:
        product_data = Product_Schema.load(request.json, partial=True)
    except ValidationError as e:
        return jsonify({"validation_errors": e.messages}), 400
    
    # Update product fields
    for field, value in product_data.items():
        setattr(product, field, value)

    db.session.commit()
    return Product_Schema.jsonify(product), 200

@app.route("/products/<int:id>", methods=["DELETE"])
def delete_product(id):
    product = db.session.get(Product, id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    try:
        db.session.delete(product)
        db.session.commit()
        return jsonify({"message": f"Product {id} deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete product"}), 500

@app.route("/orders", methods=["POST"])
def create_order():
    try:
        order_data = Order_Schema.load(request.json)
        
        # Check if user exists
        user = db.session.get(User, order_data['user_id'])
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        new_order = Order(
            user_id=order_data['user_id'],
            order_date=order_data['order_date']
        )
        db.session.add(new_order)
        db.session.commit()
        
        return Order_Schema.jsonify(new_order), 201
        
    except ValidationError as e:
        return jsonify({"validation_errors": e.messages}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/orders", methods=["GET"])
def get_orders():
    orders = db.session.execute(db.select(Order)).scalars().all()
    return Orders_Schema.jsonify(orders)

@app.route("/orders/<int:id>", methods=["GET"])
def get_order(id):
    order = db.session.get(Order, id)
    if order:
        return Order_Schema.jsonify(order)
    return {"message": "Order not found"}, 404

@app.route("/orders/<int:id>", methods=["PUT"])
def update_order(id):
    order = db.session.get(Order, id)
    if not order:
        return jsonify({"message": "Order not found"}), 404

    try:
        order_data = Order_Schema.load(request.json, partial=True)
        
        # If user_id is being updated, check if new user exists
        if 'user_id' in order_data:
            user = db.session.get(User, order_data['user_id'])
            if not user:
                return jsonify({"error": "User not found"}), 404
        
    except ValidationError as e:
        return jsonify({"validation_errors": e.messages}), 400
    
    # Update order fields
    for field, value in order_data.items():
        setattr(order, field, value)

    db.session.commit()
    return Order_Schema.jsonify(order), 200

@app.route("/orders/<int:id>", methods=["DELETE"])
def delete_order(id):
    order = db.session.get(Order, id)
    if not order:
        return jsonify({"message": "Order not found"}), 404

    try:
        db.session.delete(order)
        db.session.commit()
        return jsonify({"message": f"Order {id} deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": "Failed to delete order"}), 500

@app.route("/users/<int:user_id>/orders", methods=["GET"])
def get_user_orders(user_id):
    # Check if user exists
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    # Get all orders for this user
    orders = db.session.execute(
        db.select(Order).where(Order.user_id == user_id)
    ).scalars().all()
    
    return Orders_Schema.jsonify(orders)

@app.route("/orders/<int:order_id>/products", methods=["GET"])
def get_order_products(order_id):
    # Check if order exists
    order = db.session.get(Order, order_id)
    if not order:
        return jsonify({"message": "Order not found"}), 404
    
    # Get all products in this order
    products = order.products  # Using the relationship defined in the model
    
    return Products_Schema.jsonify(products)

@app.route("/orders/<int:order_id>/products", methods=["POST"])
def add_product_to_order(order_id):
    try:
        # Check if order exists
        order = db.session.get(Order, order_id)
        if not order:
            return jsonify({"message": "Order not found"}), 404
        
        # Get product_id from request
        data = request.json
        if not data or 'product_id' not in data:
            return jsonify({"error": "product_id is required"}), 400
        
        product_id = data['product_id']
        
        # Check if product exists
        product = db.session.get(Product, product_id)
        if not product:
            return jsonify({"message": "Product not found"}), 404
        
        # Check if product is already in the order
        if product in order.products:
            return jsonify({"message": "Product already in order"}), 400
        
        # Add product to order
        order.products.append(product)
        db.session.commit()
        
        return jsonify({"message": f"Product {product_id} added to order {order_id}"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@app.route("/orders/<int:order_id>/products/<int:product_id>", methods=["DELETE"])
def remove_product_from_order(order_id, product_id):
    try:
        # Check if order exists
        order = db.session.get(Order, order_id)
        if not order:
            return jsonify({"message": "Order not found"}), 404
        
        # Check if product exists
        product = db.session.get(Product, product_id)
        if not product:
            return jsonify({"message": "Product not found"}), 404
        
        # Check if product is in the order
        if product not in order.products:
            return jsonify({"message": "Product not in order"}), 400
        
        # Remove product from order
        order.products.remove(product)
        db.session.commit()
        
        return jsonify({"message": f"Product {product_id} removed from order {order_id}"}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        app.run(debug=True)