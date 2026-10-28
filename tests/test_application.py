import os
import tempfile

# Set the database before application module initialization.
fd, db_path = tempfile.mkstemp(suffix='.db')
os.close(fd)
os.environ['DATABASE_URL'] = 'sqlite:///' + db_path
from application import application, db, Student
import pytest

@pytest.fixture(autouse=True)
def clean_db():
    with application.app_context():
        db.drop_all()
        db.create_all()
    yield

@pytest.fixture
def client():
    application.config['TESTING'] = True
    return application.test_client()

def sample():
    return {'register_number':'25MX348','name':'Sample Student','department':'MCA','email':'sample@example.com'}

def test_health_and_home(client):
    assert client.get('/health').json == {'status':'ok'}
    assert client.get('/').status_code == 200

def test_crud_and_search(client):
    assert client.post('/students', data=sample()).status_code == 302
    assert b'Sample Student' in client.get('/').data
    assert b'Sample Student' in client.get('/?q=25MX348').data
    with application.app_context():
        student_id = Student.query.first().id
    edited = sample() | {'name':'Updated Student'}
    assert client.post(f'/students/{student_id}/edit', data=edited).status_code == 302
    assert b'Updated Student' in client.get('/').data
    assert client.post(f'/students/{student_id}/delete').status_code == 302
    assert b'Updated Student' not in client.get('/').data

def test_duplicate_register_number(client):
    client.post('/students', data=sample())
    client.post('/students', data=sample())
    with application.app_context():
        assert Student.query.count() == 1
    assert b'already exists' in client.get('/').data

def test_required_fields(client):
    client.post('/students', data={'name':'Incomplete'})
    with application.app_context():
        assert Student.query.count() == 0
