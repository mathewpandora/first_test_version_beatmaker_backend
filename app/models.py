from datetime import datetime
from app import db
# Модель пользователя

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    subscription_plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False, default=1)  # Связь с тарифом
    subscription_plan = db.relationship('SubscriptionPlan', backref='users')  # Объект подписки
    total_generations = db.Column(db.Integer, default=0)  # Всего сгенерированных битов
    current_generating_beats = db.Column(db.JSON, default=[])  # Список ID битов, которые сейчас генерируются
    successful_generated_beats = db.Column(db.JSON, default=[])  # Список ID успешно сгенерированных битов
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<User id={self.id}, email={self.email}, subscription_plan={self.subscription_plan.name}>"

# Модель подписки
class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'

    id = db.Column(db.Integer, primary_key=True)  # Уникальный идентификатор тарифа
    name = db.Column(db.String(50), unique=True, nullable=False)  # Название подписки (free, premium, pro)
    max_generations = db.Column(db.Integer, nullable=False, default=2)  # Максимальное количество генераций
    price_per_month = db.Column(db.Float, nullable=True)  # Цена подписки в месяц
    description = db.Column(db.Text, nullable=True)  # Описание тарифа
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Дата создания подписки

    def __repr__(self):
        return f"<SubscriptionPlan id={self.id}, name={self.name}, max_generations={self.max_generations}>"

# Модель бита
class Beat(db.Model):
    __tablename__ = 'beats'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # Владелец бита
    task_id = db.Column(db.String(120), unique=True, nullable=False)  # ID задачи в API генерации
    genre = db.Column(db.String(50), nullable=False)  # Жанр бита
    status = db.Column(db.String(50), nullable=False, default='in_progress')  # Статус (in_progress, completed, failed)
    url = db.Column(db.String(255), nullable=True)  # Ссылка на сгенерированный бит
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Время создания бита

    def __repr__(self):
        return f"<Beat id={self.id}, user_id={self.user_id}, genre={self.genre}, status={self.status}>"



class GenrePrompt(db.Model):
    """
    Модель для хранения жанров и длинных промптов
    """
    __tablename__ = 'genre_prompts'

    id = db.Column(db.Integer, primary_key=True)
    genre = db.Column(db.String(100), unique=True, nullable=False)  # Название жанра
    prompt = db.Column(db.Text, nullable=False)  # Длинный текстовый промпт
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # Дата создания

    def __repr__(self):
        return f"<GenrePrompt id={self.id}, genre={self.genre}, prompt={self.prompt[:50]}...>"


class VerificationCode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    code = db.Column(db.String(6), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('verification_codes', lazy=True))
