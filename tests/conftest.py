import pytest
from app import create_app, db
from app.models import User, Task


@pytest.fixture
def app():
    """Create and configure a test app instance."""
    import os
    # Set test environment variables before creating app
    os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
    os.environ['SECRET_KEY'] = 'test-secret-key'
    
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    """Create a test client."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """Create a test CLI runner."""
    return app.test_cli_runner()


@pytest.fixture
def test_user(app):
    """Create a test user."""
    with app.app_context():
        user = User(username='testuser', is_admin=False)
        user.set_password('testpass123')
        db.session.add(user)
        db.session.commit()
        return user


@pytest.fixture
def test_admin(app):
    """Create a test admin user."""
    with app.app_context():
        admin = User(username='admin', is_admin=True)
        admin.set_password('adminpass123')
        db.session.add(admin)
        db.session.commit()
        return admin


@pytest.fixture
def test_task(app, test_user):
    """Create a test task."""
    with app.app_context():
        task = Task(title='Test Task', description='Test Description', 
                   status='Pending', user_id=test_user.id)
        db.session.add(task)
        db.session.commit()
        return task


@pytest.fixture
def authenticated_client(client, test_user):
    """Create an authenticated test client."""
    client.post('/login', data={
        'username': 'testuser',
        'password': 'testpass123'
    }, follow_redirects=True)
    return client


@pytest.fixture
def admin_client(client, test_admin):
    """Create an authenticated admin test client."""
    client.post('/login', data={
        'username': 'admin',
        'password': 'adminpass123'
    }, follow_redirects=True)
    return client

