import random
import string

def generate_password(length, include_special_chars):
    characters = string.ascii_letters + string.digits
    if include_special_chars:
        characters += string.punctuation
    return ''.join(random.choice(characters) for _ in range(length))

def main():
    try:
        length = int(input("Enter the desired password length: "))
        include_special_chars = input("Include special characters? (yes/no): ").lower() == 'yes'
        password = generate_password(length, include_special_chars)
        print(f"Generated Password: {password}")
    except ValueError:
        print("Please enter a valid number for the password length.")

if __name__ == "__main__":
    main()