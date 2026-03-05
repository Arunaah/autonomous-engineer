# test_something.py

import pytest
from path.to.file import User, Product, Order, OrderItem, database

# Setup and teardown
@pytest.fixture(scope='module')
def setup_database():
    database.connect()
    database.create_tables([User, Product, Order, OrderItem])
    yield
    database.drop_tables([User, Product, Order, OrderItem])
    database.close()

# Test User model
def test_user_creation(setup_database):
    user = User.create(username='john_doe', email='john@example.com', password='password123')
    assert user.username == 'john_doe'
    assert user.email == 'john@example.com'

# Test Product model
def test_product_creation(setup_database):
    product = Product.create(name='Laptop', price=999.99, stock=10)
    assert product.name == 'Laptop'
    assert product.price == 999.99
    assert product.stock == 10

# Test Order model
def test_order_creation(setup_database):
    user = User.create(username='john_doe', email='john@example.com', password='password123')
    product = Product.create(name='Laptop', price=999.99, stock=10)
    order = Order.create(user=user)
    assert order.user == user
    assert order.date is not None

# Test OrderItem model
def test_order_item_creation(setup_database):
    user = User.create(username='john_doe', email='john@example.com', password='password123')
    product = Product.create(name='Laptop', price=999.99, stock=10)
    order = Order.create(user=user)
    order_item = OrderItem.create(order=order, product=product, quantity=1)
    assert order_item.order == order
    assert order_item.product == product
    assert order_item.quantity == 1