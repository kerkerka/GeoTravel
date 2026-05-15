"""
GeoTravel — веб-приложение для планирования путешествий, расчёта расстояний
и сохранения маршрутов.
Стек: Flask + SQLAlchemy + Yandex Geocoder API + Bootstrap 5
"""

import os
import math
import requests
import sqlalchemy as sa
from flask import Flask, render_template, redirect, request, url_for, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from data import db_session
from data.models import User, Trip, Stop
from forms import RegisterForm, LoginForm

# ==================== КОНФИГУРАЦИЯ ПРИЛОЖЕНИЯ ====================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'geo_travel_2024_secret_key_12345'  # Ключ для подписи сессий
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}  # Разрешённые форматы файлов
app.config['UPLOAD_PATH'] = 'static/uploads'  # Путь для сохранения загруженных изображений

# ==================== АВТОРИЗАЦИЯ (Flask-Login) ====================
login_manager = LoginManager()
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    """Позволяет Flask-Login восстанавливать объект пользователя из сессии при каждом запросе."""
    db_sess = db_session.create_session()
    return db_sess.get(User, user_id)

# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def is_allowed_file(filename):
    """Проверяет, что расширение файла входит в разрешённый список."""
    if not filename or '.' not in filename:
        return False
    return filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def get_coordinates(address):
    """
    Преобразует текстовый адрес в координаты (lat, lon) через Yandex Geocoder API.
    Возвращает кортеж (lat, lon) или (None, None) при ошибке/если адрес не найден.
    """
    api_key = '8013b162-6b42-4997-9691-77b7074026e0'
    url = f'http://geocode-maps.yandex.ru/1.x/?apikey={api_key}&geocode={address}&format=json'
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        toponym = data["response"]["GeoObjectCollection"]["featureMember"][0]["GeoObject"]
        coords = toponym["Point"]["pos"]
        lon, lat = coords.split()
        return float(lat), float(lon)
    except:
        return None, None

def calculate_distance(lat1, lon1, lat2, lon2):
    """
    Вычисляет расстояние между двумя точками по формуле Haversine.
    Возвращает расстояние в километрах (R = 6373 км — радиус Земли).
    """
    R = 6373.0
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (math.sin(d_lat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon/2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# ==================== ОСНОВНЫЕ РОУТЫ ====================

@app.route('/')
def index():
    """Главная страница приложения."""
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя. При отправке формы создаёт запись в БД,
    хеширует пароль и сохраняет аватар (если загружен)."""
    form = RegisterForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        if db_sess.query(User).filter(User.email == form.email.data).first():
            return render_template('register.html', form=form, message="Такой пользователь уже есть")
        user = User(name=form.name.data, email=form.email.data, about=form.about.data)
        user.set_password(form.password.data)
        file = request.files.get('avatar')
        if file and file.filename and is_allowed_file(file.filename):
            os.makedirs(app.config['UPLOAD_PATH'], exist_ok=True)
            filename = f'user_{user.id}_{file.filename}' if user.id else file.filename
            filepath = os.path.join(app.config['UPLOAD_PATH'], filename)
            file.save(filepath)
            user.avatar_path = filepath
        db_sess.add(user)
        db_sess.commit()
        return redirect('/login')
    return render_template('register.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Авторизация пользователя. Проверяет email и пароль, создаёт сессию."""
    if current_user.is_authenticated:
        return redirect('/')
    form = LoginForm()
    if form.validate_on_submit():
        db_sess = db_session.create_session()
        user = db_sess.query(User).filter(User.email == form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user)
            return redirect(f'/profile/{user.id}')
        return render_template('login.html', form=form, message="Неправильный логин или пароль")
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    """Завершение сессии пользователя."""
    logout_user()
    return redirect('/')

@app.route('/profile/<int:user_id>')
def profile(user_id):
    """Страница профиля пользователя. Отображает персональные данные и список путешествий."""
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)
    if not user:
        return "Пользователь не найден", 404
    return render_template('profile.html', user=user)

@app.route('/new_trip', methods=['GET', 'POST'])
@login_required
def new_trip():
    """Создание нового путешествия. Требует авторизации, сохраняет запись с привязкой к текущему пользователю."""
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        if not title:
            return "Укажите название", 400
        db_sess = db_session.create_session()
        trip = Trip(title=title, description=description, user_id=current_user.id)
        db_sess.add(trip)
        db_sess.commit()
        return redirect(f'/trip/{trip.id}')
    return render_template('new_trip.html')

@app.route('/trip/<int:trip_id>')
def trip_detail(trip_id):
    """Подробная информация о путешествии. Отображает все остановки с координатами и фото."""
    db_sess = db_session.create_session()
    trip = db_sess.get(Trip, trip_id)
    if not trip:
        return "Путешествие не найдено", 404
    return render_template('trip.html', trip=trip)

@app.route('/add_stop/<int:trip_id>', methods=['POST'])
@login_required
def add_stop(trip_id):
    """Добавление новой остановки в маршрут.
    Автоматически геокодирует адрес, рассчитывает координаты и сохраняет фото (если загружено)."""
    db_sess = db_session.create_session()
    trip = db_sess.get(Trip, trip_id)
    if not trip or trip.user_id != current_user.id:
        return "Доступ запрещен", 403
    name = request.form.get('name')
    address = request.form.get('address')
    lat, lon = get_coordinates(address)
    stop = Stop(name=name, address=address, latitude=lat, longitude=lon, trip_id=trip_id)
    file = request.files.get('photo')
    if file and file.filename and is_allowed_file(file.filename):
        os.makedirs(app.config['UPLOAD_PATH'], exist_ok=True)
        filename = f'stop_{stop.id}_{file.filename}' if stop.id else file.filename
        filepath = os.path.join(app.config['UPLOAD_PATH'], filename)
        file.save(filepath)
        stop.photo_path = filepath
    db_sess.add(stop)
    db_sess.commit()
    return redirect(f'/trip/{trip_id}')

@app.route('/trip_summary/<int:trip_id>')
def trip_summary(trip_id):
    """
    Подсчёт итоговой протяжённости маршрута (сумма расстояний между всеми соседними остановками).
    Возвращает HTML с заголовком, списком остановок и итоговым расстоянием в км.
    """
    db_sess = db_session.create_session()
    trip = db_sess.get(Trip, trip_id)
    if not trip or not trip.stops:
        return render_template('trip.html', trip=trip)
    total_dist = 0
    coords_list = [(s.latitude, s.longitude) for s in trip.stops]
    for i in range(1, len(coords_list)):
        total_dist += calculate_distance(coords_list[i-1][0], coords_list[i-1][1], coords_list[i][0], coords_list[i][1])
    stops_html = ''.join([f'<div class="border rounded p-2 mb-2"><b>{s.name}</b><br>{s.address}<br><small>📍 {s.latitude}, {s.longitude}</small></div>' for s in trip.stops])
    return f'<h1>{trip.title}</h1>{stops_html}<h3>Итого: {round(total_dist, 1)} км</h3>'

@app.route('/calculate_distance')
def api_distance():
    """REST API: расчёт расстояния между двумя адресами (GET-параметры a и b)."""
    addr1 = request.args.get('a')
    addr2 = request.args.get('b')
    if not addr1 or not addr2:
        return jsonify({'error': 'Укажите два адреса'}), 400
    c1 = get_coordinates(addr1)
    c2 = get_coordinates(addr2)
    if not c1[0] or not c2[0]:
        return jsonify({'error': 'Не удалось найти координаты'}), 400
    dist = calculate_distance(c1[0], c1[1], c2[0], c2[1])
    return jsonify({'distance_km': round(dist, 1)})

def main():
    """Точка входа. Создаёт папки БД и загрузок, инициализирует SQLAlchemy и запускает сервер."""
    if not os.path.exists('db'):
        os.makedirs('db')
    db_session.global_init("db/geo_travel.db")
    os.makedirs(app.config['UPLOAD_PATH'], exist_ok=True)
    app.run(debug=True, port=8080)

if __name__ == '__main__':
    main()
