import json
from main import create_app
from db import db

def test_register_user():
    app = create_app('config.TestingConfig')
    client = app.test_client()

    with app.app_context():
        db.create_all()

    response = client.post('/users/register', data=json.dumps({
        'username': 'testuser',
        'password': 'testpassword'
    }), content_type='application/json')

    assert response.status_code == 201
    assert response.json['message'] == 'User created successfully.'
