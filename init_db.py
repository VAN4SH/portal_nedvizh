# Создайте файл init_db.py
import os
from app import app, db
from werkzeug.security import generate_password_hash
from models import User

with app.app_context():
    # Создаем таблицы
    db.create_all()
    print("Таблицы созданы!")
    
    # Создаем тестового пользователя
    if not User.query.filter_by(email='test@example.com').first():
        user = User(
            username='testuser',
            email='test@example.com',
            password_hash=generate_password_hash('test123'),
            is_agent=True
        )
        db.session.add(user)
        db.session.commit()
        print("Тестовый пользователь создан!")
        print("Email: test@example.com")
        print("Пароль: test123")
