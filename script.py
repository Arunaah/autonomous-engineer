import json

def parse_json(json_str):
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        print(f'Error parsing JSON: {e}')