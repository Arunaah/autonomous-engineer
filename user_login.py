import hashlib

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = self._hash_password(password)

    def _hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()

    def verify_password(self, password):
        return self.password == self._hash_password(password)

class LoginSystem:
    def __init__(self):
        self.users = {}

    def register(self, username, password):
        if username in self.users:
            raise ValueError("Username already exists.")
        self.users[username] = User(username, password)

    def login(self, username, password):
        if username not in self.users:
            raise ValueError("Username does not exist.")
        user = self.users[username]
        if user.verify_password(password):
            return True
        else:
            return False