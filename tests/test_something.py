import pytest
from path.to.file import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_register(client):
    response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
    assert response.status_code == 201
    assert response.json['message'] == 'User registered successfully'

def test_register_duplicate(client):
    client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
    response = client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
    assert response.status_code == 400
    assert response.json['error'] == 'Username already exists'

def test_login(client):
    client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
    response = client.post('/login', json={'username': 'testuser', 'password': 'testpass'})
    assert response.status_code == 200
    assert response.json['message'] == 'Login successful'

def test_login_invalid_password(client):
    client.post('/register', json={'username': 'testuser', 'password': 'testpass'})
    response = client.post('/login', json={'username': 'testuser', 'password': 'wrongpass'})
    assert response.status_code == 401
    assert response.json['error'] == 'Invalid password'

def test_login_nonexistent_user(client):
    response = client.post('/login', json={'username': 'nonexistent', 'password': 'testpass'})
    assert response.status_code == 404
    assert response.json['error'] == 'Username does not exist'