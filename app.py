import os
from flask import Flask, render_template, request, redirect, session, flash, url_for, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import or_, func
import random
from dotenv import load_dotenv

# Загружаем переменные окружения из файла .env (если есть)
load_dotenv()

app = Flask(__name__)

# Секретный ключ лучше хранить в переменной окружения
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Подключение к PostgreSQL через переменную окружения DATABASE_URL
# Если переменная не задана, используется строка по умолчанию (замените на свои данные)
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://myuser:mypassword@localhost/rgz_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'rgz_login_page'

# Модель User (без изменений)
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    
    name = db.Column(db.String(100), nullable=False)
    service_type = db.Column(db.String(50), nullable=False)
    experience = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    about = db.Column(db.Text, nullable=True)
    
    is_hidden = db.Column(db.Boolean, default=False)
    is_admin = db.Column(db.Boolean, default=False)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Инициализация бд и тестовых пользователей
@app.cli.command('init-rgz')
def init_rgz_db():
    db.create_all()
    # админ
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(
            username='admin',
            name='Администратор',
            service_type='admin',
            experience=0,
            price=0,
            about='Администратор сайта',
            is_admin=True
        )
        admin.set_password('admin123')
        db.session.add(admin)
    
    #  30 случайных пользователей
    services = ['Репетитор', 'Бухгалтер', 'Программист', 'Юрист', 'Врач', 'Дизайнер', 'Переводчик', 'Строитель']
    for i in range(1, 31):
        username = f'user{i}'
        if not User.query.filter_by(username=username).first():
            user = User(
                username=username,
                name=f'Имя{i}',
                service_type=random.choice(services),
                experience=random.randint(1, 25),
                price=random.randint(500, 5000),
                about=f'Описание пользователя {i}. Здесь может быть текст о его услугах.'
            )
            user.set_password('pass')
            db.session.add(user)
    
    db.session.commit()
    print('База данных инициализирована: администратор и 30 тестовых пользователей.')

# ----- HTML-страницы -----
@app.route('/rgz/')
def rgz_index():
    """Главная страница с поиском"""
    return render_template('rgz/index.html')

@app.route('/rgz/login')
def rgz_login_page():
    """Страница входа"""
    return render_template('rgz/login.html')

@app.route('/rgz/register')
def rgz_register_page():
    """Страница регистрации"""
    return render_template('rgz/register.html')

@app.route('/rgz/profile')
@login_required
def rgz_profile_page():
    """Страница профиля (только для авторизованных)"""
    return render_template('rgz/profile.html')

# ----- JSON-RPC API -----
@app.route('/rgz/api', methods=['POST'])
def rgz_api():
    print("API вызван!")  # отладка
    data = request.get_json()
    print("Получены данные:", data)
    # остальной код...      
    data = request.get_json()
    
    # Проверка наличия обязательных полей
    if not data or not isinstance(data, dict):
        return jsonify({
            'jsonrpc': '2.0',
            'error': {'code': -32600, 'message': 'Invalid Request'},
            'id': None
        })
    
    jsonrpc = data.get('jsonrpc')
    method = data.get('method')
    params = data.get('params', {})
    req_id = data.get('id')
    
    if jsonrpc != '2.0':
        return jsonify({
            'jsonrpc': '2.0',
            'error': {'code': -32600, 'message': 'Invalid JSON-RPC version'},
            'id': req_id
        })
    
    if not method:
        return jsonify({
            'jsonrpc': '2.0',
            'error': {'code': -32600, 'message': 'Method not specified'},
            'id': req_id
        })
    
    # Диспетчеризация методов
    if method == 'user.register':
        result = api_user_register(params, req_id)
    elif method == 'user.login':
        result = api_user_login(params, req_id)
    elif method == 'user.logout':
        result = api_user_logout(params, req_id)
    elif method == 'user.get_profile':
        result = api_user_get_profile(params, req_id)
    elif method == 'user.update_profile':
        result = api_user_update_profile(params, req_id)
    elif method == 'user.hide_profile':
        result = api_user_hide_profile(params, req_id)
    elif method == 'user.delete_account':
        result = api_user_delete_account(params, req_id)
    elif method == 'search':
        result = api_search(params, req_id)
    elif method == 'admin.get_all_users':
        result = api_admin_get_all_users(params, req_id)
    elif method == 'admin.update_user':
        result = api_admin_update_user(params, req_id)
    elif method == 'admin.delete_user':
        result = api_admin_delete_user(params, req_id)
    else:
        return jsonify({
            'jsonrpc': '2.0',
            'error': {'code': -32601, 'message': f'Method "{method}" not found'},
            'id': req_id
        })
    
    return jsonify(result)

# ----- Вспомогательные функции для API -----
def error_response(code, message, req_id):
    return {
        'jsonrpc': '2.0',
        'error': {'code': code, 'message': message},
        'id': req_id
    }

def success_response(result, req_id):
    return {
        'jsonrpc': '2.0',
        'result': result,
        'id': req_id
    }

def admin_required():
    if not current_user.is_authenticated or not current_user.is_admin:
        return False
    return True

# ----- Реализация методов API -----
def api_user_register(params, req_id):
    username = params.get('username')
    password = params.get('password')
    name = params.get('name')
    service_type = params.get('service_type')
    experience = params.get('experience')
    price = params.get('price')
    about = params.get('about', '')
    
    # Проверка обязательных полей
    if not all([username, password, name, service_type, experience, price]):
        return error_response(-32000, 'Missing required fields', req_id)
    
    # Проверка существования пользователя
    if User.query.filter_by(username=username).first():
        return error_response(-32001, 'Username already exists', req_id)
    
    user = User(
        username=username,
        name=name,
        service_type=service_type,
        experience=int(experience),
        price=int(price),
        about=about
    )
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    
    # Автоматический вход после регистрации
    login_user(user)
    
    return success_response({'success': True, 'user_id': user.id}, req_id)

def api_user_login(params, req_id):
    username = params.get('username')
    password = params.get('password')
    
    if not username or not password:
        return error_response(-32000, 'Username and password required', req_id)
    
    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return error_response(-32002, 'Invalid username or password', req_id)
    
    login_user(user)
    return success_response({'success': True, 'user_id': user.id}, req_id)

def api_user_logout(params, req_id):
    if not current_user.is_authenticated:
        return error_response(-32003, 'Not authenticated', req_id)
    
    logout_user()
    return success_response({'success': True}, req_id)

def api_user_get_profile(params, req_id):
    user_id = params.get('user_id')
    
    if user_id is None:
        # Профиль текущего пользователя
        if not current_user.is_authenticated:
            return error_response(-32003, 'Not authenticated', req_id)
        user = current_user
    else:
        # Профиль другого пользователя
        user = User.query.get(user_id)
        if not user:
            return error_response(-32004, 'User not found', req_id)
        # Проверка, скрыта ли анкета
        if user.is_hidden and (not current_user.is_authenticated or (current_user.id != user_id and not current_user.is_admin)):
            return error_response(-32005, 'Profile is hidden', req_id)
    
    result = {
        'id': user.id,
        'username': user.username,
        'name': user.name,
        'service_type': user.service_type,
        'experience': user.experience,
        'price': user.price,
        'about': user.about,
        'is_hidden': user.is_hidden,
        'is_admin': user.is_admin
    }
    return success_response(result, req_id)

def api_user_update_profile(params, req_id):
    if not current_user.is_authenticated:
        return error_response(-32003, 'Not authenticated', req_id)
    
    user = current_user
    if 'name' in params:
        user.name = params['name']
    if 'service_type' in params:
        user.service_type = params['service_type']
    if 'experience' in params:
        user.experience = int(params['experience'])
    if 'price' in params:
        user.price = int(params['price'])
    if 'about' in params:
        user.about = params['about']
    
    db.session.commit()
    return success_response({'success': True}, req_id)

def api_user_hide_profile(params, req_id):
    if not current_user.is_authenticated:
        return error_response(-32003, 'Not authenticated', req_id)
    
    hide = params.get('hide', True)
    current_user.is_hidden = bool(hide)
    db.session.commit()
    return success_response({'success': True, 'is_hidden': current_user.is_hidden}, req_id)

def api_user_delete_account(params, req_id):
    if not current_user.is_authenticated:
        return error_response(-32003, 'Not authenticated', req_id)
    
    user = current_user
    logout_user()
    db.session.delete(user)
    db.session.commit()
    return success_response({'success': True}, req_id)

def api_search(params, req_id):
    # Параметры поиска
    name = params.get('name', '')
    service_type = params.get('service_type', '')
    exp_min = params.get('experience_min')
    exp_max = params.get('experience_max')
    price_min = params.get('price_min')
    price_max = params.get('price_max')
    page = int(params.get('page', 1))
    per_page = 5  # не более 5 на странице
    
    # Базовый запрос: только не скрытые анкеты
    query = User.query.filter_by(is_hidden=False)
    
    if name:
        query = query.filter(User.name.ilike(f'%{name}%'))
    if service_type:
        query = query.filter(User.service_type == service_type)
    if exp_min is not None:
        query = query.filter(User.experience >= int(exp_min))
    if exp_max is not None:
        query = query.filter(User.experience <= int(exp_max))
    if price_min is not None:
        query = query.filter(User.price >= int(price_min))
    if price_max is not None:
        query = query.filter(User.price <= int(price_max))
    
    # Пагинация
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    users = []
    for u in pagination.items:
        users.append({
            'id': u.id,
            'name': u.name,
            'service_type': u.service_type,
            'experience': u.experience,
            'price': u.price,
            'about': u.about[:100] + '...' if u.about and len(u.about) > 100 else u.about
        })
    
    result = {
        'users': users,
        'page': page,
        'total_pages': pagination.pages,
        'total_users': pagination.total
    }
    return success_response(result, req_id)

# ----- Админские методы -----
def api_admin_get_all_users(params, req_id):
    if not admin_required():
        return error_response(-32006, 'Admin privileges required', req_id)
    
    page = int(params.get('page', 1))
    per_page = int(params.get('per_page', 10))
    
    pagination = User.query.paginate(page=page, per_page=per_page, error_out=False)
    users = []
    for u in pagination.items:
        users.append({
            'id': u.id,
            'username': u.username,
            'name': u.name,
            'service_type': u.service_type,
            'is_hidden': u.is_hidden,
            'is_admin': u.is_admin
        })
    
    result = {
        'users': users,
        'page': page,
        'total_pages': pagination.pages,
        'total_users': pagination.total
    }
    return success_response(result, req_id)

def api_admin_update_user(params, req_id):
    if not admin_required():
        return error_response(-32006, 'Admin privileges required', req_id)
    
    user_id = params.get('user_id')
    if not user_id:
        return error_response(-32000, 'user_id required', req_id)
    
    user = User.query.get(user_id)
    if not user:
        return error_response(-32004, 'User not found', req_id)
    
    if 'name' in params:
        user.name = params['name']
    if 'service_type' in params:
        user.service_type = params['service_type']
    if 'experience' in params:
        user.experience = int(params['experience'])
    if 'price' in params:
        user.price = int(params['price'])
    if 'about' in params:
        user.about = params['about']
    if 'is_hidden' in params:
        user.is_hidden = bool(params['is_hidden'])
    if 'is_admin' in params:
        user.is_admin = bool(params['is_admin'])
    
    db.session.commit()
    return success_response({'success': True}, req_id)

def api_admin_delete_user(params, req_id):
    if not admin_required():
        return error_response(-32006, 'Admin privileges required', req_id)
    
    user_id = params.get('user_id')
    if not user_id:
        return error_response(-32000, 'user_id required', req_id)
    
    user = User.query.get(user_id)
    if not user:
        return error_response(-32004, 'User not found', req_id)
    
    # Не даём удалить самого себя? Можно разрешить, но осторожно.
    if current_user.id == user.id:
        return error_response(-32007, 'Cannot delete yourself', req_id)
    
    db.session.delete(user)
    db.session.commit()
    return success_response({'success': True}, req_id)


@app.route('/rgz/admin')
@login_required
def rgz_admin_page():
    """Страница администратора"""
    if not current_user.is_admin:
        flash('Доступ запрещён', 'error')
        return redirect(url_for('rgz_index'))
    return render_template('rgz/admin.html')

# Обработка ошибки 404
@app.errorhandler(404)
def not_found(err):
    return '''
    <!doctype html>
    <html>
        <head>
            <style>
                body { text-align: center; }
                h1 { color: red; font-size: 48px; }
                img { max-width: 300px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <h1>404</h1>
            <h2>Такой страницы не существует</h2>
            <img src="''' + url_for('static', filename='okak.jpg') + '''" alt="Ошибка 404">
        </body>
    </html>
    ''', 404
