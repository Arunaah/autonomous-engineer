import argparse

def handle_request(request):
    # Placeholder function to handle user requests
    return f"Processed request: {request}"

def main():
    parser = argparse.ArgumentParser(description="User Request Handler")
    parser.add_argument('request', type=str, help="The user request to process")
    args = parser.parse_args()
    
    result = handle_request(args.request)
    print(result)

if __name__ == "__main__":
    main()