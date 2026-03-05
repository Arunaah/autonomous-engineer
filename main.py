class BankAccount:
    def __init__(self, initial_balance=0):
        self.balance = initial_balance
        self.balance_history = [(0, initial_balance)]

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            self.balance_history.append((amount, self.balance))

    def withdraw(self, amount):
        if 0 < amount <= self.balance:
            self.balance -= amount
            self.balance_history.append((-amount, self.balance))

    def get_balance_history(self):
        return self.balance_history