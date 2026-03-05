class Calculator:
    def add(self, x, y):
        return x + y

    def subtract(self, x, y):
        return x - y

    def multiply(self, x, y):
        return x * y

    def divide(self, x, y):
        if y == 0:
            raise ValueError("Cannot divide by zero")
        return x / y

def main():
    calculator = Calculator()
    while True:
        print("Options:")
        print("1. Add")
        print("2. Subtract")
        print("3. Multiply")
        print("4. Divide")
        print("5. Exit")
        choice = input("Enter your choice (1-5): ")
        if choice == '5':
            break
        if choice in ['1', '2', '3', '4']:
            if choice == '1':
                x = float(input("Enter first number: "))
                y = float(input("Enter second number: "))
                print("Result:", calculator.add(x, y))
            elif choice == '2':
                x = float(input("Enter first number: "))
                y = float(input("Enter second number: "))
                print("Result:", calculator.subtract(x, y))
            elif choice == '3':
                x = float(input("Enter first number: "))
                y = float(input("Enter second number: "))
                print("Result:", calculator.multiply(x, y))
            elif choice == '4':
                x = float(input("Enter first number: "))
                y = float(input("Enter second number: "))
                try:
                    print("Result:", calculator.divide(x, y))
                except ValueError as e:
                    print(e)
        else:
            print("Invalid choice. Please enter a number between 1 and 5.")

if __name__ == "__main__":
    main()