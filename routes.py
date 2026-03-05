from flask import Flask, jsonify, request

app = Flask(__name__)

# Define a route for the root URL
@app.route('/', methods=['GET'])
def home():
    return jsonify({"message": "Welcome to the API!"})

# Define a route for getting a list of items
@app.route('/items', methods=['GET'])
def get_items():
    # This is a placeholder for the actual data retrieval logic
    items = ["item1", "item2", "item3"]
    return jsonify(items)

# Define a route for creating a new item
@app.route('/items', methods=['POST'])
def create_item():
    data = request.json
    new_item = data.get('name')
    if new_item:
        # This is a placeholder for the actual item creation logic
        items = ["item1", "item2", "item3"]
        items.append(new_item)
        return jsonify(items), 201
    else:
        return jsonify({"error": "Missing 'name' in the request body"}), 400

# Define a route for getting an item by ID
@app.route('/items/<int:item_id>', methods=['GET'])
def get_item(item_id):
    # This is a placeholder for the actual data retrieval logic
    items = ["item1", "item2", "item3"]
    if 0 <= item_id < len(items):
        return jsonify(items[item_id])
    else:
        return jsonify({"error": "Item not found"}), 404

# Define a route for updating an item by ID
@app.route('/items/<int:item_id>', methods=['PUT'])
def update_item(item_id):
    data = request.json
    new_name = data.get('name')
    if new_name:
        # This is a placeholder for the actual item update logic
        items = ["item1", "item2", "item3"]
        items[item_id] = new_name
        return jsonify(items)
    else:
        return jsonify({"error": "Missing 'name' in the request body"}), 400

# Define a route for deleting an item by ID
@app.route('/items/<int:item_id>', methods=['DELETE'])
def delete_item(item_id):
    # This is a placeholder for the actual item deletion logic
    items = ["item1", "item2", "item3"]
    if 0 <= item_id < len(items):
        items.pop(item_id)
        return jsonify(items)
    else:
        return jsonify({"error": "Item not found"}), 404

if __name__ == '__main__':
    app.run(debug=True)