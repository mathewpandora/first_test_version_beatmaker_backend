from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, create_refresh_token
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.services.auth_service import generate_verification_code, send_verification_email
from app.models import User, VerificationCode


bp = Blueprint('auth', __name__, url_prefix='/auth')

# Регистрация нового пользователя
@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    print(email, password)
    if User.query.filter_by(email=email).first():
        return jsonify({"msg": "User already exists"}), 400

    hashed_password = generate_password_hash(password)
    new_user = User(email=email, password=hashed_password)
    db.session.add(new_user)
    db.session.commit()

    # Генерация и отправка кода подтверждения
    verification_code = generate_verification_code()
    send_verification_email(email, verification_code)

    # Сохраняем код подтверждения в базе данных
    verification_entry = VerificationCode(user_id=new_user.id, code=verification_code)
    db.session.add(verification_entry)
    db.session.commit()

    return jsonify({"msg": "User created successfully, verification code sent to email"}), 201


@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    print(email, password)
    # Проверяем, есть ли пользователь с таким email
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"message": "User not found"}), 404

    print(user.password, password)
    if not check_password_hash(user.password, password):
        return jsonify({"message": "Incorrect password"}), 401

    # Генерация access_token и refresh_token
    access_token = create_access_token(identity=str(user.id))
    refresh_token = create_refresh_token(identity=str(user.id))

    return jsonify({
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 200


# Выход из системы (удаление токена)
#типизировать и обработать отеты и оптимизировать
@bp.route('/logout', methods=['POST'])
@jwt_required()  # Требуется авторизация для выхода
def logout():
    # Токен просто удаляется на клиенте
    return jsonify({"msg": "Successfully logged out"}), 200

#типизировать и обработать отеты и оптимизировать
@bp.route('/user', methods=['GET'])
@jwt_required()  # Требуется авторизация
def get_user():
    current_user_id = get_jwt_identity()
    if current_user_id is None:
        return jsonify({"msg": "Token is invalid"}), 422
    user = User.query.get(current_user_id)
    if not user:
        return jsonify({"msg": "User not found"}), 404

    return jsonify({
        "email": user.email,
        "subscription_plan": user.subscription_plan.name,
        "total_generations": user.total_generations,
        "current_generating_beats": user.current_generating_beats,
        "successful_generated_beats":user.successful_generated_beats
    }), 200


# Роут для обновления access_token с использованием refresh_token
#типизировать и обработать отеты и оптимизировать
@bp.route('/refresh-token', methods=['POST'])
@jwt_required(refresh=True)  # Требуется свежий refresh_token
def refresh_token():
    current_user_id = get_jwt_identity()  # Получаем id из refresh токена
    access_token = create_access_token(identity=current_user_id)  # Создаем новый access token
    return jsonify({'access_token': access_token}), 200


@bp.route('/verify-email', methods=['POST'])
def verify_email():
    data = request.get_json()
    email = data.get('email')
    verification_code = data.get('verification_code')

    # Проверяем, существует ли пользователь с таким email
    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"msg": "User not found"}), 404

    # Проверяем, существует ли код подтверждения для этого пользователя
    print(user.id)
    verification_entry = VerificationCode.query.filter_by(user_id=user.id, code=verification_code).first()
    print(f'code {verification_entry}, {type(verification_entry)}')
    if not verification_entry:

        return jsonify({"msg": "Invalid or expired verification code"}), 400

    # Подтверждаем почту, устанавливаем флаг is_verified в True
    user.is_verified = True
    db.session.commit()
    return jsonify({"msg": "Successfully sent"}), 200


@bp.route('/change-password', methods=['POST'])
@jwt_required()  # Требуется авторизация
def change_password():
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')
    confirm_new_password = data.get('confirm_new_password')

    if not new_password or not confirm_new_password:
        return jsonify({"msg": "New password and confirmation are required"}), 400

    if new_password != confirm_new_password:
        return jsonify({"msg": "New passwords do not match"}), 400

    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)

    if not user:
        return jsonify({"msg": "User not found"}), 404

    if not check_password_hash(user.password, current_password):
        return jsonify({"msg": "Current password is incorrect"}), 401

    user.password = generate_password_hash(new_password)
    db.session.commit()

    return jsonify({"msg": "Password updated successfully"}), 200


@bp.route('/check-email', methods=['POST'])
def check_email():
    """
    Проверяет, существует ли пользователь с указанным email.

    Returns:
        JSON-ответ с сообщением о существовании пользователя.
    """
    try:
        # Получаем email из запроса
        data = request.get_json()
        email = data.get('email', '').strip()

        if not email:
            return jsonify({"msg": "Email is required"}), 400

        # Ищем пользователя по email
        user = User.query.filter_by(email=email).first()

        if user:
            return jsonify({"exists": True, "is_verified": user.is_verified}), 200
        else:
            return jsonify({"exists": False}), 200

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"msg": "Internal server error"}), 500


    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"msg": "Internal server error"}), 500

