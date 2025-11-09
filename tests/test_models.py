import pytest
from app import db
from app.models import User, Task


class TestUser:
    """Test cases for User model."""

    def test_user_creation(self, app):
        """Test creating a new user."""
        with app.app_context():
            user = User(username='newuser')
            user.set_password('password123')
            db.session.add(user)
            db.session.commit()
            
            assert user.id is not None
            assert user.username == 'newuser'
            assert user.is_admin is False
            assert user.password_hash is not None
            assert user.password_hash != 'password123'  # Should be hashed

    def test_user_password_hashing(self, app):
        """Test password hashing and verification."""
        with app.app_context():
            user = User(username='testuser')
            user.set_password('mypassword')
            
            assert user.check_password('mypassword') is True
            assert user.check_password('wrongpassword') is False
            assert user.password_hash != 'mypassword'

    def test_user_unique_username(self, app):
        """Test that usernames must be unique."""
        with app.app_context():
            user1 = User(username='uniqueuser')
            user1.set_password('pass123')
            db.session.add(user1)
            db.session.commit()
            
            user2 = User(username='uniqueuser')
            user2.set_password('pass456')
            db.session.add(user2)
            
            with pytest.raises(Exception):  # Should raise IntegrityError
                db.session.commit()

    def test_user_relationship_with_tasks(self, app, test_user):
        """Test user's relationship with tasks."""
        with app.app_context():
            task1 = Task(title='Task 1', user_id=test_user.id)
            task2 = Task(title='Task 2', user_id=test_user.id)
            db.session.add_all([task1, task2])
            db.session.commit()
            
            assert len(test_user.tasks) == 2
            assert task1.owner == test_user
            assert task2.owner == test_user

    def test_user_is_admin_default(self, app):
        """Test that is_admin defaults to False."""
        with app.app_context():
            user = User(username='regularuser')
            user.set_password('pass123')
            db.session.add(user)
            db.session.commit()
            
            assert user.is_admin is False

    def test_user_is_admin_setting(self, app):
        """Test setting is_admin to True."""
        with app.app_context():
            admin = User(username='adminuser', is_admin=True)
            admin.set_password('adminpass')
            db.session.add(admin)
            db.session.commit()
            
            assert admin.is_admin is True


class TestTask:
    """Test cases for Task model."""

    def test_task_creation(self, app, test_user):
        """Test creating a new task."""
        with app.app_context():
            task = Task(title='New Task', description='Task description', 
                       status='Pending', user_id=test_user.id)
            db.session.add(task)
            db.session.commit()
            
            assert task.id is not None
            assert task.title == 'New Task'
            assert task.description == 'Task description'
            assert task.status == 'Pending'
            assert task.user_id == test_user.id

    def test_task_default_status(self, app, test_user):
        """Test that task status defaults to 'Pending'."""
        with app.app_context():
            task = Task(title='Default Task', user_id=test_user.id)
            db.session.add(task)
            db.session.commit()
            
            assert task.status == 'Pending'

    def test_task_optional_description(self, app, test_user):
        """Test that task description can be None."""
        with app.app_context():
            task = Task(title='No Description Task', user_id=test_user.id)
            db.session.add(task)
            db.session.commit()
            
            assert task.description is None

    def test_task_relationship_with_user(self, app, test_user):
        """Test task's relationship with user."""
        with app.app_context():
            task = Task(title='Related Task', user_id=test_user.id)
            db.session.add(task)
            db.session.commit()
            
            assert task.owner == test_user
            assert task.user_id == test_user.id

    def test_task_update_status(self, app, test_task):
        """Test updating task status."""
        with app.app_context():
            assert test_task.status == 'Pending'
            
            test_task.status = 'In Progress'
            db.session.commit()
            
            updated_task = Task.query.get(test_task.id)
            assert updated_task.status == 'In Progress'
            
            updated_task.status = 'Completed'
            db.session.commit()
            
            final_task = Task.query.get(test_task.id)
            assert final_task.status == 'Completed'

    def test_task_delete(self, app, test_user):
        """Test deleting a task."""
        with app.app_context():
            task = Task(title='To Delete', user_id=test_user.id)
            db.session.add(task)
            db.session.commit()
            task_id = task.id
            
            db.session.delete(task)
            db.session.commit()
            
            deleted_task = Task.query.get(task_id)
            assert deleted_task is None

    def test_multiple_tasks_per_user(self, app, test_user):
        """Test that a user can have multiple tasks."""
        with app.app_context():
            task1 = Task(title='Task 1', user_id=test_user.id)
            task2 = Task(title='Task 2', user_id=test_user.id)
            task3 = Task(title='Task 3', user_id=test_user.id)
            db.session.add_all([task1, task2, task3])
            db.session.commit()
            
            user_tasks = Task.query.filter_by(user_id=test_user.id).all()
            assert len(user_tasks) == 3

