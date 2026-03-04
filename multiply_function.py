def multiply_numbers(a, b):
    return a * b

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python multiply_function.py <number1> <number2>")
        sys.exit(1)

    num1 = int(sys.argv[1])
    num2 = int(sys.argv[2])
    product = multiply_numbers(num1, num2)
    print("The product is:", product)