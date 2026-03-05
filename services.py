import datetime

class UserService:
    def __init__(self):
        self.users = []

    def add_user(self, username, email):
        if any(user['username'] == username for user in self.users):
            raise ValueError(f"User with username '{username}' already exists.")
        new_user = {
            'username': username,
            'email': email,
            'created_at': datetime.datetime.now()
        }
        self.users.append(new_user)

    def get_user(self, username):
        for user in self.users:
            if user['username'] == username:
                return user
        raise ValueError(f"User with username '{username}' not found.")

    def update_user(self, username, email=None):
        user = self.get_user(username)
        if email:
            user['email'] = email
        return user

    def delete_user(self, username):
        self.users = [user for user in self.users if user['username'] != username]

class ProductService:
    def __init__(self):
        self.products = []

    def add_product(self, product_id, name, price):
        if any(product['product_id'] == product_id for product in self.products):
            raise ValueError(f"Product with ID '{product_id}' already exists.")
        new_product = {
            'product_id': product_id,
            'name': name,
            'price': price,
            'created_at': datetime.datetime.now()
        }
        self.products.append(new_product)

    def get_product(self, product_id):
        for product in self.products:
            if product['product_id'] == product_id:
                return product
        raise ValueError(f"Product with ID '{product_id}' not found.")

    def update_product(self, product_id, name=None, price=None):
        product = self.get_product(product_id)
        if name:
            product['name'] = name
        if price:
            product['price'] = price
        return product

    def delete_product(self, product_id):
        self.products = [product for product in self.products if product['product_id'] != product_id]