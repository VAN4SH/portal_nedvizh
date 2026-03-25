#!/usr/bin/env python3
import os
import sys
from subprocess import check_call

def install_dependencies():
    """Установка всех зависимостей"""
    print("Устанавливаю зависимости...")
    check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    
def create_database():
    """Создание и инициализация базы данных"""
    print("Создаю базу данных...")
    from app import app, db
    with app.app_context():
        db.create_all()
        print("База данных создана!")
        
        # Добавляем тестовые данные
        from werkzeug.security import generate_password_hash
        from models import User
        
        # Создаем тестового пользователя
        if not User.query.filter_by(email='admin@example.com').first():
            admin = User(
                username='admin',
                email='admin@example.com',
                password_hash=generate_password_hash('admin123'),
                is_agent=True
            )
            db.session.add(admin)
            db.session.commit()
            print("Тестовый пользователь создан!")
            print("Email: admin@example.com")
            print("Пароль: admin123")

def main():
    """Основная функция установки"""
    print("Настройка портала недвижимости...")
    
    # Установка зависимостей
    install_dependencies()
    
    # Создание необходимых папок
    os.makedirs('static/images/properties', exist_ok=True)
    os.makedirs('instance', exist_ok=True)
    
    # Создание базы данных
    create_database()
    
    print("\n" + "="*50)
    print("Настройка завершена успешно!")
    print("Запустите приложение командой: python app.py")
    print("Откройте в браузере: http://localhost:5000")
    print("="*50)

if __name__ == "__main__":
    main()
