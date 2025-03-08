import random
import string
from flask_mail import Message
from app import mail  # Импортируем инициализированный mail из app

def generate_verification_code():
    """Генерация случайного 6-значного кода для подтверждения почты"""
    return ''.join(random.choices(string.digits, k=6))

def send_verification_email(email, code):
    """Отправка кода на почту"""
    msg = Message("Email Verification Code", recipients=[email])
    print(msg, 'сообщшение сформироано')
    msg.body = f"Your verification code is: {code}"
    mail.send(msg)
    return


