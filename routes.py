from flask import Flask, jsonify, request

app = Flask(__name__)

# Define a route for the root URL
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the API!"})

# Define a route for a list of items
@app.route('/items', methods=['GET'])
def get_items():
    # This is a placeholder for the actual data retrieval logic
    items = [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
        {"id": 3, "name": "Item 3"}
    ]
    return jsonify(items)

# Define a route for creating a new item
@app.route('/items', methods=['POST'])
def create_item():
    data = request.json
    new_item = {
        "id": data["id"],
        "name": data["name"]
    }
    # This is a placeholder for the actual item creation logic
    # For demonstration purposes, we'll just return the new item
    return jsonify(new_item)

# Define a route for retrieving a single item by ID
@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    # This is a placeholder for the actual data retrieval logic
    # For demonstration purposes, we'll return the item if it exists
    item = next((item for item in [
        {"id": 1, "name": "Item 1"},
        {"id": 2, "name": "Item 2"},
        {"id": 3, "name": "Item 3"}
    ] if item["id"] == item_id), None)
    return jsonify(item)

# Define a route for updating an existing item
@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.json
    # This is a placeholder for the actual item update logic
    # For demonstration purposes, we'll return the updated item
    updated_item = {
        "id": item_id,
        "name": data["name"]
    }
    return jsonify(updated_item)

# Define a route for deleting an item
@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    # This is a placeholder for the actual item deletion logic
    # For demonstration purposes, we'll return a success message
    return jsonify({"message": "Item deleted successfully"})

if __name__ == '__main__':
    app.run(debug=True)