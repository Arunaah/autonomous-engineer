from flask import Flask, jsonify, request
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Dummy database for demonstration purposes
users = {}

@app.route('/register', methods=['POST'])
def register():
    username = request.json.get('username')
    password = request.json.get('password')
    
    if username in users:
        return jsonify({'error': 'Username already exists'}), 400
    
    users[username] = generate_password_hash(password)
    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    username = request.json.get('username')
    password = request.json.get('password')
    
    if username not in users:
        return jsonify({'error': 'Username does not exist'}), 404
    
    if not check_password_hash(users[username], password):
        return jsonify({'error': 'Invalid password'}), 401
    
    return jsonify({'message': 'Login successful'}), 200

if __name__ == '__main__':
    app.run(debug=True)