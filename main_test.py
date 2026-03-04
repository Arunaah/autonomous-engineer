# Testing the FastAPI application
from fastapi.testclient import TestClient
from fastapi import FastAPI
from main import app, read_root  # Added proper import

client = TestClient(app)

def test_read_root():
    response = client.get('/')
    assert response.status_code == 200
    assert response.json() == read_root()
