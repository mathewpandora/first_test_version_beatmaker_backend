from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from .config import Config
from flask_migrate import Migrate
from flask_cors import CORS
from flask_mail import Mail

# Инициализация объектов
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()
mail = Mail()  # Объект почты инициализируется здесь

def create_app():
    # Создаем экземпляр Flask приложения
    app = Flask(__name__)

    # Разрешаем CORS для всех источников (по желанию, можно настроить для конкретных источников)
    CORS(app)

    # Загружаем конфигурацию из config.py
    app.config.from_object(Config)

    # Инициализация Mail с приложением
    mail.init_app(app)  # Инициализация почтового сервиса с приложением

    # Инициализация SQLAlchemy с приложением
    db.init_app(app)

    # Инициализация JWTManager с приложением
    jwt.init_app(app)

    # Регистрируем миграции
    migrate.init_app(app, db)

    # Импортируем маршруты (Blueprints)
    from .routes import auth, beats, subscription

    # Регистрируем Blueprint для аутентификации
    app.register_blueprint(auth.bp)

    # (Закомментированные) Пример добавления других Blueprint:
    app.register_blueprint(beats.bp)
    # app.register_blueprint(subscription.bp)

    return app
