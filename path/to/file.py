import sys

class InvalidRequestError(Exception):
    """Custom exception for invalid requests."""
    pass

def process_request(request):
    """
    Process a request and raise an InvalidRequestError if the request is invalid.
    
    :param request: The request to process.
    :return: The processed result.
    :raises InvalidRequestError: If the request is invalid.
    """
    if not isinstance(request, str) or not request:
        raise InvalidRequestError("Invalid request: Request must be a non-empty string.")
    
    # Simulate processing the request
    return f"Processed {request}"

# Example usage
if __name__ == "__main__":
    # Test with valid request
    print(process_request("ValidRequest"))
    
    # Test with invalid request
    try:
        print(process_request(""))
    except InvalidRequestError as e:
        print(f"Error: {e}")