from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.models import User, Task
from app import db

main = Blueprint('main', __name__)

@main.route('/')
def home():
    return render_template('home.html', title="Home")

@main.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Username already exists!')
            return redirect(url_for('main.register'))

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        flash('Registered successfully! Please log in.')
        return redirect(url_for('main.login'))

    return render_template('register.html', title="Register")

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.home'))
        flash('Invalid username or password.')

    return render_template('login.html', title="Login")

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@main.route('/tasks')
@login_required
def tasks():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks.html', tasks=tasks, title="My Tasks")

@main.route('/tasks/add', methods=['POST'])
@login_required
def add_task():
    title = request.form['title']
    description = request.form.get('description', '')
    task = Task(title=title, description=description, user_id=current_user.id)
    db.session.add(task)
    db.session.commit()
    return redirect(url_for('main.tasks'))

@main.route('/tasks/update/<int:id>')
@login_required
def update_task(id):
    task = Task.query.get_or_404(id)
    if task.owner != current_user:
        flash("You can't update this task.")
        return redirect(url_for('main.tasks'))

    new_status = request.args.get('status', 'Pending')
    task.status = new_status
    db.session.commit()
    return redirect(url_for('main.tasks'))

@main.route('/tasks/delete/<int:id>')
@login_required
def delete_task(id):
    task = Task.query.get_or_404(id)
    if task.owner != current_user:
        flash("You can't delete this task.")
        return redirect(url_for('main.tasks'))

    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('main.tasks'))

@main.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash("Access denied. Admins only!")
        return redirect(url_for('main.home'))

    users = User.query.all()
    return render_template('admin.html', users=users, title="Admin Dashboard")
