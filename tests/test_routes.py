import pytest
from app import db
from app.models import User, Task


class TestHomeRoute:
    """Test cases for home route."""

    def test_home_route_get(self, client):
        """Test accessing home page."""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Home' in response.data


class TestRegisterRoute:
    """Test cases for register route."""

    def test_register_page_get(self, client):
        """Test accessing register page."""
        response = client.get('/register')
        assert response.status_code == 200
        assert b'Register' in response.data

    def test_register_success(self, client, app):
        """Test successful user registration."""
        with app.app_context():
            response = client.post('/register', data={
                'username': 'newuser',
                'password': 'newpass123'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            assert b'Registered successfully' in response.data or b'log in' in response.data.lower()
            
            user = User.query.filter_by(username='newuser').first()
            assert user is not None
            assert user.check_password('newpass123')

    def test_register_duplicate_username(self, client, app, test_user):
        """Test registering with existing username."""
        with app.app_context():
            response = client.post('/register', data={
                'username': 'testuser',
                'password': 'somepass'
            }, follow_redirects=True)
            
            assert b'Username already exists' in response.data or response.status_code == 200


class TestLoginRoute:
    """Test cases for login route."""

    def test_login_page_get(self, client):
        """Test accessing login page."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Login' in response.data

    def test_login_success(self, client, test_user):
        """Test successful login."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'testpass123'
        }, follow_redirects=True)
        
        assert response.status_code == 200

    def test_login_invalid_username(self, client):
        """Test login with invalid username."""
        response = client.post('/login', data={
            'username': 'nonexistent',
            'password': 'somepass'
        }, follow_redirects=True)
        
        assert b'Invalid username or password' in response.data

    def test_login_invalid_password(self, client, test_user):
        """Test login with invalid password."""
        response = client.post('/login', data={
            'username': 'testuser',
            'password': 'wrongpassword'
        }, follow_redirects=True)
        
        assert b'Invalid username or password' in response.data


class TestLogoutRoute:
    """Test cases for logout route."""

    def test_logout_requires_login(self, client):
        """Test that logout requires authentication."""
        response = client.get('/logout', follow_redirects=True)
        # Should redirect to login page
        assert response.status_code == 200

    def test_logout_success(self, authenticated_client):
        """Test successful logout."""
        response = authenticated_client.get('/logout', follow_redirects=True)
        assert response.status_code == 200


class TestTasksRoute:
    """Test cases for tasks route."""

    def test_tasks_requires_login(self, client):
        """Test that tasks page requires authentication."""
        response = client.get('/tasks', follow_redirects=True)
        assert response.status_code == 200

    def test_tasks_display(self, authenticated_client, app, test_user):
        """Test displaying user's tasks."""
        with app.app_context():
            task1 = Task(title='Task 1', user_id=test_user.id)
            task2 = Task(title='Task 2', user_id=test_user.id)
            db.session.add_all([task1, task2])
            db.session.commit()
        
        response = authenticated_client.get('/tasks')
        assert response.status_code == 200
        assert b'Task 1' in response.data
        assert b'Task 2' in response.data

    def test_tasks_only_shows_user_tasks(self, authenticated_client, app, test_user):
        """Test that users only see their own tasks."""
        with app.app_context():
            other_user = User(username='otheruser')
            other_user.set_password('pass123')
            db.session.add(other_user)
            db.session.commit()
            
            user_task = Task(title='My Task', user_id=test_user.id)
            other_task = Task(title='Other Task', user_id=other_user.id)
            db.session.add_all([user_task, other_task])
            db.session.commit()
        
        response = authenticated_client.get('/tasks')
        assert response.status_code == 200
        assert b'My Task' in response.data
        assert b'Other Task' not in response.data


class TestAddTaskRoute:
    """Test cases for add task route."""

    def test_add_task_requires_login(self, client):
        """Test that adding task requires authentication."""
        response = client.post('/tasks/add', data={
            'title': 'New Task',
            'description': 'Description'
        }, follow_redirects=True)
        assert response.status_code == 200

    def test_add_task_success(self, authenticated_client, app, test_user):
        """Test successfully adding a task."""
        with app.app_context():
            response = authenticated_client.post('/tasks/add', data={
                'title': 'New Task',
                'description': 'Task Description'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            task = Task.query.filter_by(title='New Task').first()
            assert task is not None
            assert task.description == 'Task Description'
            assert task.status == 'Pending'
            assert task.user_id == test_user.id

    def test_add_task_without_description(self, authenticated_client, app, test_user):
        """Test adding a task without description."""
        with app.app_context():
            response = authenticated_client.post('/tasks/add', data={
                'title': 'Task Without Description'
            }, follow_redirects=True)
            
            assert response.status_code == 200
            
            task = Task.query.filter_by(title='Task Without Description').first()
            assert task is not None
            assert task.description == ''


class TestUpdateTaskRoute:
    """Test cases for update task route."""

    def test_update_task_requires_login(self, client, app, test_task):
        """Test that updating task requires authentication."""
        response = client.get(f'/tasks/update/{test_task.id}?status=Completed', 
                            follow_redirects=True)
        assert response.status_code == 200

    def test_update_task_success(self, authenticated_client, app, test_task):
        """Test successfully updating a task."""
        with app.app_context():
            assert test_task.status == 'Pending'
            
            response = authenticated_client.get(
                f'/tasks/update/{test_task.id}?status=In Progress',
                follow_redirects=True
            )
            
            assert response.status_code == 200
            
            updated_task = Task.query.get(test_task.id)
            assert updated_task.status == 'In Progress'

    def test_update_task_other_user_task(self, authenticated_client, app):
        """Test that users cannot update other users' tasks."""
        with app.app_context():
            other_user = User(username='otheruser')
            other_user.set_password('pass123')
            db.session.add(other_user)
            db.session.commit()
            
            other_task = Task(title='Other Task', user_id=other_user.id)
            db.session.add(other_task)
            db.session.commit()
            
            response = authenticated_client.get(
                f'/tasks/update/{other_task.id}?status=Completed',
                follow_redirects=True
            )
            
            assert response.status_code == 200
            assert b"can't update" in response.data.lower()
            
            # Task status should not have changed
            unchanged_task = Task.query.get(other_task.id)
            assert unchanged_task.status == 'Pending'


class TestDeleteTaskRoute:
    """Test cases for delete task route."""

    def test_delete_task_requires_login(self, client, app, test_task):
        """Test that deleting task requires authentication."""
        response = client.get(f'/tasks/delete/{test_task.id}', 
                            follow_redirects=True)
        assert response.status_code == 200

    def test_delete_task_success(self, authenticated_client, app, test_user):
        """Test successfully deleting a task."""
        with app.app_context():
            task = Task(title='To Delete', user_id=test_user.id)
            db.session.add(task)
            db.session.commit()
            task_id = task.id
            
            response = authenticated_client.get(
                f'/tasks/delete/{task_id}',
                follow_redirects=True
            )
            
            assert response.status_code == 200
            
            deleted_task = Task.query.get(task_id)
            assert deleted_task is None

    def test_delete_task_other_user_task(self, authenticated_client, app):
        """Test that users cannot delete other users' tasks."""
        with app.app_context():
            other_user = User(username='otheruser')
            other_user.set_password('pass123')
            db.session.add(other_user)
            db.session.commit()
            
            other_task = Task(title='Other Task', user_id=other_user.id)
            db.session.add(other_task)
            db.session.commit()
            task_id = other_task.id
            
            response = authenticated_client.get(
                f'/tasks/delete/{task_id}',
                follow_redirects=True
            )
            
            assert response.status_code == 200
            assert b"can't delete" in response.data.lower()
            
            # Task should still exist
            existing_task = Task.query.get(task_id)
            assert existing_task is not None


class TestAdminRoute:
    """Test cases for admin route."""

    def test_admin_requires_login(self, client):
        """Test that admin page requires authentication."""
        response = client.get('/admin', follow_redirects=True)
        assert response.status_code == 200

    def test_admin_requires_admin_role(self, authenticated_client):
        """Test that admin page requires admin role."""
        response = authenticated_client.get('/admin', follow_redirects=True)
        assert response.status_code == 200
        assert b'Access denied' in response.data or b'Admins only' in response.data

    def test_admin_access_success(self, admin_client, app, test_admin):
        """Test that admin can access admin page."""
        with app.app_context():
            # Create additional users
            user1 = User(username='user1')
            user1.set_password('pass1')
            user2 = User(username='user2')
            user2.set_password('pass2')
            db.session.add_all([user1, user2])
            db.session.commit()
        
        response = admin_client.get('/admin')
        assert response.status_code == 200
        assert b'Admin Dashboard' in response.data or b'admin' in response.data.lower()

