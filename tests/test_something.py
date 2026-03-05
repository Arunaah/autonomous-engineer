import pytest
from path.to.file import process_request, InvalidRequestError

def test_process_request_valid():
    """
    Test that a valid request is processed correctly.
    """
    assert process_request("ValidRequest") == "Processed ValidRequest"

def test_process_request_invalid():
    """
    Test that an invalid request raises an InvalidRequestError.
    """
    with pytest.raises(InvalidRequestError) as exc_info:
        process_request("")
    assert str(exc_info.value) == "Invalid request: Request must be a non-empty string."

def test_process_request_type_error():
    """
    Test that passing a non-string type raises an InvalidRequestError.
    """
    with pytest.raises(InvalidRequestError) as exc_info:
        process_request(123)
    assert str(exc_info.value) == "Invalid request: Request must be a non-empty string."