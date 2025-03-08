import logging
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
from app import db
from app.models import User, GenrePrompt, Beat
from app.services.beat_service import *
from typing import Dict, Any, Union
from random_word import RandomWords
import os

bp = Blueprint('beats', __name__, url_prefix='/beats')
TOKEN = os.getenv("LOVEAI_API_TOKEN")

# Настройка логирования
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@bp.route('/create-by-genre', methods=['POST'])
@jwt_required()
def create_beat_by_genre() -> Any:
    """
    Создает биты на основе указанного жанра.
    """
    print("Entering create_beat_by_genre")
    try:
        current_user_id: int = get_jwt_identity()
        print(f"Current user ID: {current_user_id}")
        user: Union[User, None] = db.session.get(User, current_user_id)
        if not user:
            print(f"User with id {current_user_id} not found.")
            logger.warning(f"User with id {current_user_id} not found.")
            return jsonify({"msg": "User not found"}), 404

        # Проверяем, есть ли у пользователя доступные генерации
        if user.available_generations <= 0:
            print(f"User with id {current_user_id} has no available generations.")
            logger.warning(f"User with id {current_user_id} has no available generations.")
            return jsonify({"msg": "No available generations left. Please purchase a generation package."}), 403

        data: Dict[str, Any] = request.get_json()
        print(f"Request data: {data}")
        genre: Union[str, None] = data.get("genre")

        if not genre:
            print("Genre is required in the request body.")
            logger.warning(f"Genre is required in the request body.")
            return jsonify({"msg": "Genre is required"}), 400

        existing_genre: Union[GenrePrompt, None] = GenrePrompt.query.filter_by(genre=genre).first()
        if not existing_genre:
            print(f"Invalid genre: {genre}")
            logger.warning(f"Invalid genre: {genre}")
            return jsonify({"msg": "Invalid genre"}), 400

        # Проверяем существующие биты без привязки к пользователю с таким жанром
        existing_beat_no_user = Beat.query.filter_by(user_id=None, genre=genre).first()

        if existing_beat_no_user:
            print(f"Existing beat found without user, status: {existing_beat_no_user.status}")
            if existing_beat_no_user.status in ["completed", "in_progress"]:
                existing_beat_no_user.user_id = user.id
                db.session.commit()
                print(f"Assigned existing beat with task_id {existing_beat_no_user.task_id} to user {current_user_id}.")
                logger.info(f"Assigned existing beat with task_id {existing_beat_no_user.task_id} to user {current_user_id}.")
                return jsonify({
                    "msg": "Beat found without user, now assigned to you.",
                    "beat_id": existing_beat_no_user.id
                }), 200

        # Генерация нового бита, если такого бита не было найдено
        print(f"Generating beat for genre: {genre}")
        status, answer = generate_beat_by_genre(TOKEN, existing_genre.prompt)
        print(f"Response from generate_beat_by_genre: {status}, {answer}")

        task_id: Union[str, None] = answer.get("task_id")

        if not task_id:
            print(f"Failed to generate beat for genre: {genre}")
            logger.error(f"Failed to generate beat for genre: {genre}")
            return jsonify({"msg": "Failed to generate beat"}), 500

        # Здесь вызываем функцию для получения статуса бита по task_id
        print(f"Fetching beat status for task_id: {task_id}")


        new_beat_user = Beat(
            user_id=user.id,
            task_id=task_id,
            genre=genre,
            status="in_progress",
            created_at=datetime.now(timezone.utc).isoformat()
        )

        new_beat_no_user = Beat(
            user_id=None,
            task_id=task_id,
            genre=genre,
            status="in_progress",
            created_at=datetime.now(timezone.utc).isoformat()
        )

        db.session.add(new_beat_user)
        db.session.add(new_beat_no_user)
        db.session.commit()

        user.available_generations -= 1
        db.session.commit()

        print(f"Started beat generation for user {current_user_id} with genre {genre}.")
        logger.info(f"Started beat generation for user {current_user_id} with genre {genre}.")
        return jsonify({
            "msg": "Beat generation started",
            "user_beat_id": new_beat_user.id,
            "no_user_beat_id": new_beat_no_user.id
        }), 201

    except Exception as e:
        print(f"Error in create_beat_by_genre: {e}")
        logger.error(f"Error in create_beat_by_genre: {e}")
        return jsonify({"msg": "Internal server error"}), 500


@bp.route('/list', methods=['GET'])
@jwt_required()
def get_beats_list():
    """
    Возвращает список битов пользователя.
    """
    print("Entering get_beats_list")
    try:
        current_user_id = get_jwt_identity()
        print(f"Current user ID: {current_user_id}")
        user = db.session.get(User, current_user_id)

        if not user:
            print(f"User with id {current_user_id} not found.")
            logger.warning(f"User with id {current_user_id} not found.")
            return jsonify({"msg": "User not found"}), 404

        user_beats = Beat.query.filter_by(user_id=user.id).all()
        print(f"User beats: {user_beats}")

        completed_beats = [
            {
                "id": beat.id,
                "genre": beat.genre,
                "url": beat.url,
                "name": beat.title,
                "created_at": beat.created_at.isoformat(),
                "img_url": beat.image_url,
            }
            for beat in user_beats if beat.status == "completed"
        ]

        in_progress_beats = [
            {
                "id": beat.id,
                "genre": beat.genre,
                "created_at": beat.created_at.isoformat()
            }
            for beat in user_beats if beat.status == "in_progress"
        ]

        print(f"Completed beats: {completed_beats}")
        print(f"In-progress beats: {in_progress_beats}")

        logger.info(f"Fetched beats list for user {current_user_id}.")
        return jsonify({
            "completed": completed_beats,
            "in_progress": in_progress_beats
        }), 200

    except Exception as e:
        print(f"Error in get_beats_list: {e}")
        logger.error(f"Error in get_beats_list: {e}")
        return jsonify({"msg": "Internal server error"}), 500


@jwt_required()
@bp.route('/genres', methods=['GET'])
def get_genres():
    """
    Возвращает список всех жанров из таблицы GenrePrompt.
    """
    print("Entering get_genres")
    try:
        genres = GenrePrompt.query.all()
        print(f"Genres found: {genres}")

        genre_list = [{"id": genre.id, "genre": genre.genre} for genre in genres]

        print(f"Genre list: {genre_list}")
        logger.info("Fetched genres list.")
        return jsonify(genre_list), 200

    except Exception as e:
        print(f"Error in get_genres: {e}")
        logger.error(f"Error in get_genres: {e}")
        return jsonify({"msg": "Internal server error"}), 500



def generate_random_word() -> str:
    try:
        r = RandomWords()
        word = r.get_random_word()
        logger.info(f"Generated random word: {word}")
        return word
    except Exception as e:
        logger.error(f"Error generating random word: {e}")
        return "default"

# Endpoint для получения всех битов с статусом "in_progress" для текущего пользователя
@bp.route('/update-beats', methods=['GET'])
@jwt_required()  # Требуется JWT токен
def update_beats():
    current_user_id = get_jwt_identity()  # Извлекаем ID текущего пользователя
    logger.info(f"Current user ID: {current_user_id}")

    user = db.session.get(User, current_user_id)  # Получаем пользователя из базы данных

    if not user:
        logger.warning(f"User with ID {current_user_id} not found.")
        return jsonify({"msg": "User not found"}), 404

    beats = Beat.query.filter_by(user_id=current_user_id, status='in_progress').all()  # Все биты с таким статусом
    logger.info(f"Found {len(beats)} beats with status 'in_progress' for user {current_user_id}")

    if not beats:
        logger.info(f"No beats found in progress for user {current_user_id}")
        return jsonify({"msg": "No beats found in progress"}), 404

    for beat in beats:
        logger.info(f"Processing beat with task_id: {beat.task_id}")

        # Получаем информацию по каждому биту через API
        beat_info = get_beat_by_id(beat.task_id)

        if isinstance(beat_info, dict) and 'output_data' in beat_info:
            output_data = beat_info['output_data']
            logger.info(f"Received output_data for beat {beat.task_id}: {output_data}")

            if output_data.get('msg') == 'All generated successfully.' and output_data.get('data'):
                data = output_data['data']
                logger.info(f"Generated data for beat {beat.task_id}: {data}")

                # Проверка, что ссылки на аудио и изображения не пустые и длина больше 1 символа
                if (len(data[0]['audio_url']) > 1 and len(data[1]['audio_url']) > 1 and
                    len(data[0]['image_url']) > 1 and len(data[1]['image_url']) > 1):

                    # Генерация случайного осмысленного существительного
                    random_word = generate_random_word()
                    logger.info(f"Using random word '{random_word}' for updating beat data")

                    # Обновляем данные о бите в базе
                    beat.title = data[0]['title']
                    beat.url = data[0]['audio_url']
                    beat.image_url = data[0]['image_url']
                    beat.status = 'completed'
                    logger.info(f"Updated beat {beat.task_id} with title '{beat.title}' and status 'complete'")

                    # Для бита без привязки к пользователю (если существует)
                    beat_without_user = Beat.query.filter_by(task_id=beat.task_id, user_id=None).first()
                    if beat_without_user:
                        beat_without_user.title = data[1]['title']
                        beat_without_user.url = data[1]['audio_url']
                        beat_without_user.image_url = data[1]['image_url']
                        beat_without_user.status = 'completed'
                        logger.info(f"Updated beat without user (task_id: {beat.task_id}) with title '{beat_without_user.title}'")

                    # Сохраняем изменения
                    db.session.commit()
                    logger.info(f"Committed changes to database for beat {beat.task_id}")

    logger.info("Beats update process completed successfully.")
    return jsonify({"msg": "Beats updated successfully"}), 200
