from typing import Dict, Tuple, Union
import requests
import dotenv
import os

dotenv.load_dotenv()
TOKEN = os.getenv("LOVEAI_API_TOKEN")


def generate_beat_by_description(token: str, description: str) -> Tuple[int, Dict[str, str]]:
    if not token:
        raise ValueError("Токен LOVEAI_API_TOKEN отсутствует или не загружен!")

    url = "https://api.loveaiapi.com/music/suno/generate2"
    payload = {
        'prompt': f"INSTRUMENTAL MUST BE ONLY IN RAP INSTRUMENTAL GENRE AND MORE THAN 60 SECONDS. TRY TO take into account DESCRIPTION: {description}",
        'title': "",
        "custom": False,
        "instrumental": True,
        "style": 'rap',
        "callback_url": 'http://127.0.0.1:5000'
    }

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()

        # Возвращаем код состояния и содержимое ответа
        return response.status_code, response.json()
    except requests.exceptions.RequestException as e:
        print(1)
        # Возвращаем код ошибки и сообщение об ошибке в виде словаря
        return 500, {"error": str(e)}


def get_beat_by_id(task_id: str) -> Union[Dict, str]:
    if not TOKEN:
        raise ValueError("Токен LOVEAI_API_TOKEN отсутствует или не загружен!")

    url = f"https://api.loveaiapi.com/music/suno/task?task_id={task_id}"

    headers = {
        'Authorization': f'Bearer {TOKEN}'
    }

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()  # Эта строка может вызвать ошибку, если ответ не в JSON
    except requests.exceptions.RequestException as e:
        return str(e)
    except ValueError as e:  # Обработка ошибки, если JSON не удается распарсить
        return f"Ошибка при разборе ответа JSON: {e}"


def generate_beat_by_genre(token: str) -> Tuple[int, Dict]:
    if not token:
        raise ValueError("Токен LOVEAI_API_TOKEN отсутствует или не загружен!")
    url = "https://api.loveaiapi.com/music/suno/generate2"
    payload = {
        'prompt': "",  # Используем текстовый промпт из базы данных
        'title': "My Song",
        "custom": True,
        "instrumental": True,
        "style": "drill",
        "callback_url": 'http://127.0.0.1:5000'
    }

    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        # Возвращаем код состояния и распарсенный JSON
        return response.status_code, response.json()  # Возвращаем статус и данные JSON
    except requests.exceptions.RequestException as e:
        return 500, {"error": str(e)}

print(get_beat_by_id("4d6af3d2-ccc9-4c18-96b3-4a066684fa00"))
