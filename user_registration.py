import re

class UserRegistration:
    def __init__(self):
        self.users = {}

    def is_valid_email(self, email):
        pattern = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        return re.match(pattern, email) is not None

    def is_valid_username(self, username):
        pattern = r'^[a-zA-Z0-9_]{3,16}$'
        return re.match(pattern, username) is not None

    def is_valid_password(self, password):
        pattern = r'^(?=.*[A-Za-z])(?=.*\d)[A-Za-z\d]{8,}$'
        return re.match(pattern, password) is not None

    def register_user(self, username, email, password):
        if not self.is_valid_username(username):
            return "Invalid username"
        if not self.is_valid_email(email):
            return "Invalid email"
        if not self.is_valid_password(password):
            return "Invalid password"
        if username in self.users:
            return "Username already exists"
        if email in self.users.values():
            return "Email already in use"
        self.users[username] = email
        return "User registered successfully"

    def get_user_email(self, username):
        return self.users.get(username, "User not found")

    def unregister_user(self, username):
        if username in self.users:
            del self.users[username]
            return "User unregistered successfully"
        return "User not found"