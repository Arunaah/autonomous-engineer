import json

def parse_json(json_str):
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        if len(json_str) > 0:
            print(f'Error parsing JSON: {e}')
        else:
            print('Empty JSON string provided')