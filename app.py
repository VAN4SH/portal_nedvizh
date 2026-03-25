from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
from config import Config

app = Flask(__name__)
app.config.from_object(Config)
db = SQLAlchemy(app)

# Настройка Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
login_manager.login_message_category = 'warning'

# Модели базы данных
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    phone = db.Column(db.String(20))
    is_agent = db.Column(db.Boolean, default=False)
    listings = db.relationship('Listing', backref='author', lazy=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Listing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Float, nullable=False)
    property_type = db.Column(db.String(50), nullable=False)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    area = db.Column(db.Float)
    location = db.Column(db.String(200), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    featured = db.Column(db.Boolean, default=False)
    main_image = db.Column(db.String(200), default='default.jpg')
    images = db.Column(db.Text, default='[]')
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def save_image(file):
    """Сохранение изображения и возврат имени файла"""
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().timestamp()}_{file.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        return filename
    return None

# Основные маршруты
@app.route('/')
def index():
    try:
        featured_listings = Listing.query.filter_by(featured=True)\
            .order_by(Listing.created_at.desc()).limit(6).all()
        latest_listings = Listing.query.order_by(Listing.created_at.desc()).limit(8).all()
    except Exception as e:
        print(f"Ошибка при получении списков: {e}")
        featured_listings = []
        latest_listings = []
    
    return render_template('index.html', 
                         featured_listings=featured_listings,
                         latest_listings=latest_listings)

@app.route('/listings')
def listings():
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 12
        property_type = request.args.get('type', 'all')
        city = request.args.get('city', '')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        
        query = Listing.query
        
        if property_type and property_type != 'all':
            query = query.filter_by(property_type=property_type)
        if city:
            query = query.filter_by(city=city)
        if min_price:
            query = query.filter(Listing.price >= min_price)
        if max_price:
            query = query.filter(Listing.price <= max_price)
        
        pagination = query.order_by(Listing.created_at.desc()).paginate(page=page, per_page=per_page)
        return render_template('listings.html', 
                             listings=pagination.items, 
                             pagination=pagination)
    except Exception as e:
        print(f"Ошибка при фильтрации: {e}")
        return render_template('listings.html', listings=[], pagination=None)

@app.route('/listing/<int:listing_id>')
def listing_detail(listing_id):
    try:
        listing = Listing.query.get_or_404(listing_id)
        similar_listings = Listing.query.filter(
            Listing.city == listing.city,
            Listing.id != listing.id
        ).limit(4).all()
        return render_template('listing_detail.html', 
                             listing=listing, 
                             similar_listings=similar_listings)
    except Exception as e:
        print(f"Ошибка при получении деталей: {e}")
        flash('Объявление не найдено', 'error')
        return redirect(url_for('listings'))

@app.route('/add-listing', methods=['GET', 'POST'])
@login_required
def add_listing():
    if request.method == 'POST':
        try:
            # Получаем данные из формы
            title = request.form.get('title', '').strip()
            description = request.form.get('description', '').strip()
            price_str = request.form.get('price', '0')
            property_type = request.form.get('property_type', 'apartment')
            bedrooms = request.form.get('bedrooms', '0', type=int)
            bathrooms = request.form.get('bathrooms', '0', type=int)
            area = request.form.get('area', '0', type=float)
            location = request.form.get('location', '').strip()
            city = request.form.get('city', '').strip()
            featured = request.form.get('featured') == 'on'
            
            # Валидация
            if not all([title, description, location, city]):
                flash('Пожалуйста, заполните все обязательные поля', 'error')
                return redirect(url_for('add_listing'))
            
            try:
                price = float(price_str.replace(',', '.'))
                if price <= 0:
                    flash('Цена должна быть положительным числом', 'error')
                    return redirect(url_for('add_listing'))
            except ValueError:
                flash('Неверный формат цены', 'error')
                return redirect(url_for('add_listing'))
            
            # Создаем объявление
            listing = Listing(
                title=title,
                description=description,
                price=price,
                property_type=property_type,
                bedrooms=bedrooms,
                bathrooms=bathrooms,
                area=area,
                location=location,
                city=city,
                featured=featured,
                user_id=current_user.id
            )
            
            # Обработка главного изображения
            if 'main_image' in request.files:
                file = request.files['main_image']
                if file.filename:
                    filename = save_image(file)
                    if filename:
                        listing.main_image = filename
            
            # Обработка дополнительных изображений
            additional_images = []
            for key in request.files:
                if key.startswith('image_'):
                    file = request.files[key]
                    if file.filename:
                        filename = save_image(file)
                        if filename:
                            additional_images.append(filename)
            
            if additional_images:
                listing.images = json.dumps(additional_images)
            
            db.session.add(listing)
            db.session.commit()
            
            flash('Объявление успешно добавлено!', 'success')
            return redirect(url_for('listing_detail', listing_id=listing.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при добавлении объявления: {e}")
            flash('Произошла ошибка при добавлении объявления', 'error')
    
    return render_template('add_listing.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        message = request.form.get('message', '').strip()
        
        if not all([name, email, message]):
            flash('Пожалуйста, заполните все поля', 'error')
            return redirect(url_for('contact'))
        
        # Здесь можно добавить отправку email
        # send_contact_email(name, email, message)
        
        flash('Сообщение отправлено! Мы свяжемся с вами в ближайшее время.', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

# Аутентификация
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        
        if not email or not password:
            flash('Пожалуйста, заполните все поля', 'error')
            return redirect(url_for('login'))
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user, remember='remember' in request.form)
            next_page = request.args.get('next')
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(next_page or url_for('index'))
        
        flash('Неверный email или пароль', 'error')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()
        confirm_password = request.form.get('confirm_password', '').strip()
        
        # Валидация
        errors = []
        if not username or len(username) < 3:
            errors.append('Имя пользователя должно содержать минимум 3 символа')
        if not email or '@' not in email:
            errors.append('Введите корректный email')
        if not password or len(password) < 6:
            errors.append('Пароль должен содержать минимум 6 символов')
        if password != confirm_password:
            errors.append('Пароли не совпадают')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return redirect(url_for('register'))
        
        # Проверяем, существует ли пользователь
        if User.query.filter_by(email=email).first():
            flash('Email уже зарегистрирован', 'error')
            return redirect(url_for('register'))
        
        if User.query.filter_by(username=username).first():
            flash('Имя пользователя уже занято', 'error')
            return redirect(url_for('register'))
        
        # Создаем пользователя
        try:
            user = User(
                username=username,
                email=email,
                is_agent='is_agent' in request.form
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            flash('Регистрация прошла успешно!', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при регистрации: {e}")
            flash('Произошла ошибка при регистрации', 'error')
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

# Добавьте эти маршруты после существующих маршрутов (перед API endpoints):

@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

@app.route('/my-listings')
@login_required
def my_listings():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    # Получаем объявления текущего пользователя
    query = Listing.query.filter_by(user_id=current_user.id)
    pagination = query.order_by(Listing.created_at.desc()).paginate(page=page, per_page=per_page)
    
    return render_template('my_listings.html', 
                         listings=pagination.items, 
                         pagination=pagination)

@app.route('/edit-listing/<int:listing_id>', methods=['GET', 'POST'])
@login_required
def edit_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    
    # Проверяем, что пользователь является владельцем объявления
    if listing.user_id != current_user.id:
        flash('У вас нет прав на редактирование этого объявления', 'error')
        return redirect(url_for('my_listings'))
    
    if request.method == 'POST':
        try:
            # Обновляем данные
            listing.title = request.form.get('title', '').strip()
            listing.description = request.form.get('description', '').strip()
            listing.price = float(request.form.get('price', '0').replace(',', '.'))
            listing.property_type = request.form.get('property_type', 'apartment')
            listing.bedrooms = request.form.get('bedrooms', '0', type=int)
            listing.bathrooms = request.form.get('bathrooms', '0', type=int)
            listing.area = request.form.get('area', '0', type=float)
            listing.location = request.form.get('location', '').strip()
            listing.city = request.form.get('city', '').strip()
            listing.featured = request.form.get('featured') == 'on'
            listing.updated_at = datetime.utcnow()
            
            # Обновление изображения
            if 'main_image' in request.files:
                file = request.files['main_image']
                if file and file.filename:
                    filename = save_image(file)
                    if filename:
                        # Удаляем старое изображение, если оно не используется другими объявлениями
                        if listing.main_image and listing.main_image != 'default.jpg':
                            old_path = os.path.join(app.config['UPLOAD_FOLDER'], listing.main_image)
                            if os.path.exists(old_path):
                                os.remove(old_path)
                        listing.main_image = filename
            
            db.session.commit()
            flash('Объявление успешно обновлено!', 'success')
            return redirect(url_for('listing_detail', listing_id=listing.id))
            
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при обновлении объявления: {e}")
            flash('Произошла ошибка при обновлении объявления', 'error')
    
    return render_template('edit_listing.html', listing=listing)

@app.route('/delete-listing/<int:listing_id>', methods=['POST'])
@login_required
def delete_listing(listing_id):
    listing = Listing.query.get_or_404(listing_id)
    
    # Проверяем, что пользователь является владельцем объявления
    if listing.user_id != current_user.id:
        flash('У вас нет прав на удаление этого объявления', 'error')
        return redirect(url_for('my_listings'))
    
    try:
        # Удаляем изображения
        if listing.main_image and listing.main_image != 'default.jpg':
            main_path = os.path.join(app.config['UPLOAD_FOLDER'], listing.main_image)
            if os.path.exists(main_path):
                os.remove(main_path)
        
        # Удаляем дополнительные изображения
        if listing.images:
            additional_images = json.loads(listing.images)
            for img in additional_images:
                img_path = os.path.join(app.config['UPLOAD_FOLDER'], img)
                if os.path.exists(img_path):
                    os.remove(img_path)
        
        # Удаляем запись из БД
        db.session.delete(listing)
        db.session.commit()
        
        flash('Объявление успешно удалено!', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при удалении объявления: {e}")
        flash('Произошла ошибка при удалении объявления', 'error')
    
    return redirect(url_for('my_listings'))

@app.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        try:
            current_user.username = request.form.get('username', '').strip()
            current_user.email = request.form.get('email', '').strip()
            current_user.phone = request.form.get('phone', '').strip()
            current_user.is_agent = 'is_agent' in request.form
            
            # Обновление пароля, если указан новый
            new_password = request.form.get('new_password', '').strip()
            if new_password:
                if len(new_password) < 6:
                    flash('Пароль должен содержать минимум 6 символов', 'error')
                    return redirect(url_for('edit_profile'))
                current_user.set_password(new_password)
            
            db.session.commit()
            flash('Профиль успешно обновлен!', 'success')
            return redirect(url_for('profile'))
            
        except Exception as e:
            db.session.rollback()
            print(f"Ошибка при обновлении профиля: {e}")
            flash('Произошла ошибка при обновлении профиля', 'error')
    
    return render_template('edit_profile.html', user=current_user)

# API endpoints
@app.route('/api/cities')
def get_cities():
    try:
        cities = db.session.query(Listing.city).distinct().all()
        return jsonify([city[0] for city in cities if city[0]])
    except Exception as e:
        print(f"Ошибка при получении городов: {e}")
        return jsonify([])

@app.route('/api/property-types')
def get_property_types():
    types = db.session.query(Listing.property_type).distinct().all()
    return jsonify([pt[0] for pt in types if pt[0]])

# Обработчики ошибок
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

# Создаем таблицы в БД при первом запуске
def create_tables():
    with app.app_context():
        db.create_all()
        print("Таблицы базы данных созданы!")

# Добавьте эту функцию перед if __name__ == '__main__':

def create_test_data():
    """Создание тестовых данных"""
    with app.app_context():
        # Проверяем, есть ли пользователи
        if not User.query.first():
            print("Создаю тестовых пользователей...")
            
            # Создаем администратора
            admin = User(
                username='admin',
                email='admin@example.com',
                phone='+7 (999) 123-45-67',
                is_agent=True
            )
            admin.set_password('admin123')
            
            # Создаем обычного пользователя
            user = User(
                username='user',
                email='user@example.com',
                phone='+7 (999) 765-43-21',
                is_agent=False
            )
            user.set_password('user123')
            
            db.session.add_all([admin, user])
            db.session.commit()
            print("Пользователи созданы!")
            
        # Проверяем, есть ли объявления
        if not Listing.query.first():
            print("Создаю тестовые объявления...")
            
            # Тестовые объявления
            test_listings = [
                Listing(
                    title='3-комн. квартира в центре Москвы',
                    description='Просторная квартира в новом доме с ремонтом. Панорамные окна, два санузла, кухня-гостиная.',
                    price=15000000,
                    property_type='apartment',
                    bedrooms=3,
                    bathrooms=2,
                    area=85.5,
                    location='ул. Тверская, 15',
                    city='Москва',
                    featured=True,
                    main_image='default.jpg',
                    user_id=1
                ),
                Listing(
                    title='Загородный дом в Подмосковье',
                    description='Кирпичный дом на участке 10 соток. Все коммуникации, гараж, баня.',
                    price=25000000,
                    property_type='house',
                    bedrooms=5,
                    bathrooms=3,
                    area=180.0,
                    location='Красногорский район',
                    city='Москва',
                    featured=True,
                    main_image='default.jpg',
                    user_id=1
                ),
                Listing(
                    title='Студия в новостройке',
                    description='Современная студия с евроремонтом. Готовка к проживанию. Ипотека.',
                    price=7500000,
                    property_type='apartment',
                    bedrooms=1,
                    bathrooms=1,
                    area=35.0,
                    location='ул. Ленина, 45',
                    city='Санкт-Петербург',
                    featured=False,
                    main_image='default.jpg',
                    user_id=2
                ),
            ]
            
            db.session.add_all(test_listings)
            db.session.commit()
            print("Тестовые объявления созданы!")
            
            print("\n" + "="*50)
            print("Данные для входа:")
            print("Администратор:")
            print("  Email: admin@example.com")
            print("  Пароль: admin123")
            print("\nПользователь:")
            print("  Email: user@example.com")
            print("  Пароль: user123")
            print("="*50)

if __name__ == '__main__':
    # Создаем папки, если их нет
    os.makedirs('static/images/properties', exist_ok=True)
    os.makedirs('instance', exist_ok=True)
    
    # Создаем таблицы
    with app.app_context():
        db.create_all()
        print("База данных создана!")
        
        # Создаем тестовые данные
        try:
            create_test_data()
        except Exception as e:
            print(f"Ошибка при создании тестовых данных: {e}")
    
    # Запускаем приложение
    app.run(debug=True, host='0.0.0.0', port=5000)
