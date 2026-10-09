import requests

from config import API_URL


def register_user(username: str, password: str, gender: str) -> dict:
    try:
        response = requests.post(
            f"{API_URL}/register",
            json={"username": username, "password": password, "gender": gender},
            timeout=10,
        )
        if response.status_code == 409:
            return {"error": "Пользователь с таким именем уже существует"}
        if response.status_code != 200:
            data = response.json()
            return {"error": data.get("detail", "Ошибка регистрации")}
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Не удалось подключиться к API."}
    except Exception as e:
        return {"error": str(e)}


def login_user(username: str, password: str) -> dict:
    try:
        response = requests.post(
            f"{API_URL}/login",
            json={"username": username, "password": password},
            timeout=10,
        )
        if response.status_code == 401:
            return {"error": "Неверное имя пользователя или пароль"}
        if response.status_code != 200:
            data = response.json()
            return {"error": data.get("detail", "Ошибка входа")}
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Не удалось подключиться к API."}
    except Exception as e:
        return {"error": str(e)}


def analyze_text(text: str, user_id: int | None = None) -> dict:
    try:
        payload = {"text": text}
        if user_id is not None:
            payload["user_id"] = user_id
        response = requests.post(
            f"{API_URL}/predict",
            json=payload,
            timeout=30,
        )
        if response.status_code != 200:
            error_data = response.json()
            return {"error": error_data.get("detail", "Ошибка сервера")}
        data = response.json()
        label = data["label"]
        score = data["score"]
        if label == "toxic":
            toxicity_percent = round(score * 100, 1)
        else:
            toxicity_percent = round((1 - score) * 100, 1)
        return {
            "label": label,
            "score": score,
            "toxicity_percent": toxicity_percent,
        }
    except requests.exceptions.ConnectionError:
        return {"error": "Не удалось подключиться к API. Убедитесь, что сервер запущен."}
    except requests.exceptions.Timeout:
        return {"error": "Превышено время ожидания ответа от API."}
    except Exception as e:
        return {"error": str(e)}


def get_stats() -> dict:
    try:
        response = requests.get(f"{API_URL}/stats", timeout=10)
        if response.status_code != 200:
            return {"error": "Не удалось получить статистику"}
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Не удалось подключиться к API."}
    except Exception as e:
        return {"error": str(e)}


def get_articles() -> list[dict]:
    try:
        response = requests.get(f"{API_URL}/articles", timeout=10)
        if response.status_code != 200:
            return []
        return response.json()
    except Exception:
        return []


def get_article(article_id: int) -> dict | None:
    try:
        response = requests.get(f"{API_URL}/articles/{article_id}", timeout=10)
        if response.status_code != 200:
            return None
        return response.json()
    except Exception:
        return None


def post_comment(article_id: int, text: str, user_id: int) -> dict:
    try:
        response = requests.post(
            f"{API_URL}/articles/{article_id}/comments",
            json={"article_id": article_id, "text": text, "user_id": user_id},
            timeout=30,
        )
        if response.status_code == 403:
            return {"blocked": True, "error": response.json().get("detail", "Токсичный контент")}
        if response.status_code != 200:
            data = response.json()
            return {"error": data.get("detail", "Ошибка сервера")}
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": "Не удалось подключиться к API."}
    except Exception as e:
        return {"error": str(e)}


def get_comments(article_id: int) -> list[dict]:
    try:
        response = requests.get(f"{API_URL}/articles/{article_id}/comments", timeout=10)
        if response.status_code != 200:
            return []
        return response.json()
    except Exception:
        return []


def check_api_health() -> bool:
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        return response.status_code == 200
    except Exception:
        return False
