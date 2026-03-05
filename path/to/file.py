# models.py

from peewee import *

# Define the database connection
database = SqliteDatabase('my_database.db')

# Define the base class for all models
class BaseModel(Model):
    class Meta:
        database = database

# Define a User model
class User(BaseModel):
    username = CharField(unique=True)
    email = CharField(unique=True)
    password = CharField()

# Define a Product model
class Product(BaseModel):
    name = CharField()
    price = DecimalField()
    stock = IntegerField()

# Define an Order model
class Order(BaseModel):
    user = ForeignKeyField(User, backref='orders')
    date = DateTimeField(default=datetime.datetime.now)
    items = ManyToManyField(Product, through='OrderItem')

# Define an OrderItem model
class OrderItem(BaseModel):
    order = ForeignKeyField(Order, backref='order_items')
    product = ForeignKeyField(Product, backref='order_items')
    quantity = IntegerField()

# Create the database and tables
database.connect()
database.create_tables([User, Product, Order, OrderItem])