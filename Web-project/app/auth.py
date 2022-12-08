from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from app import mysql
from user_policy import UsersPolicy


bp = Blueprint('auth', __name__, url_prefix='/auth')

class User(UserMixin):
    def __init__(self, user_id, login, role_id):
        super().__init__()
        self.id = user_id #ЗАПОМИНАЕТСЯ ID ПОЛЬЗОВАТЕЛЯ
        self.login = login
        self.role_id = role_id
    def can(self, action, record=None):
        policy = UsersPolicy(record=record)
        method = getattr(policy, action, None)
        if method:
            return method()
        return False

def load_record(user_id):
    if user_id is None:
        return None
    cursor = mysql.connection.cursor(named_tuple=True)
    cursor.execute('SELECT * FROM users WHERE id = %s;', (user_id,))
    record = cursor.fetchone()
    cursor.close()
    return record

def check_rights(action):
    def decorator(func):
        @wraps(func) #Возвращает декоратор
        def wrapper(*args, **kwargs): # И этот декоратор применяется в функ.обертки
            record = load_record(kwargs.get('user_id'))
            if not current_user.can(action, record=record):
                flash('У вас недостаточно прав для доступа к данной странице', 'danger')
                return redirect(url_for('index'))
            return func(*args, **kwargs)
        return wrapper
    return decorator




def load_user(user_id): #ЗАГРУЗКА ПОЛЬЗОВАТЕЛЯ ПО ID
    cursor = mysql.connection.cursor(named_tuple=True)
    cursor.execute('SELECT * FROM users WHERE id = %s;', (user_id,))
    db_user = cursor.fetchone()
    cursor.close()
    if db_user:
        return User(user_id=db_user.id, login=db_user.login, role_id=db_user.role_id)
    return None

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        login = request.form.get('login')
        password = request.form.get('password')
        remember_me = request.form.get('remember_me') == 'on'
        if login and password:
            cursor = mysql.connection.cursor(named_tuple=True)
            cursor.execute('SELECT * FROM users WHERE login = %s AND password_hash = SHA2(%s, 256);', (login, password))
            db_user = cursor.fetchone()
            cursor.close()

            if db_user:
                user = User(user_id=db_user.id, login=db_user.login, role_id=db_user.role_id)
                login_user(user, remember=remember_me) #ЗАПОМИНАЕТ ТЕКУЩЕГО ПОЛЬЗОВАТЕЛЯ.
                flash('Вы успешно аутентифицированы.', 'success') #ХРАНИМ В СЕССИИ СООБЩЕНИЕ.

                next = request.args.get('next')

                return redirect(next or url_for('index'))
        flash('Введены неверные логин или пароль.', 'danger')
    return  render_template('login.html')

@bp.route('/logout')
def logout():
    logout_user()
    return  redirect(url_for('index'))

def init_login_manager(app):
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Для доступа к данной странице необходимо аутентифицироваться.'
    login_manager.login_message_category = 'warning'
    login_manager.user_loader(load_user)


