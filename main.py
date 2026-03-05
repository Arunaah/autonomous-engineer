import random
import string

def generate_password(length=8):
    if length < 8:
        raise ValueError("Password length must be at least 8 characters.")
    characters = string.ascii_letters + string.digits + string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

if __name__ == "__main__":
    try:
        password_length = int(input("Enter the desired password length (minimum 8): "))
        password = generate_password(password_length)
        print(f"Generated password: {password}")
    except ValueError as e:
        print(e)