import hashlib
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "predictions.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            gender TEXT NOT NULL CHECK(gender IN ('male', 'female')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS predictions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            label TEXT NOT NULL,
            score REAL NOT NULL,
            user_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            summary TEXT NOT NULL,
            author TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            article_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (article_id) REFERENCES articles(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)
    _seed_articles(conn)
    conn.commit()
    conn.close()


def _seed_articles(conn):
    cur = conn.execute("SELECT COUNT(*) FROM articles")
    if cur.fetchone()[0] > 0:
        return
    articles = [
        (
            "Расписание весеннего семестра 2025",
            "Опубликовано обновлённое расписание занятий на весенний семестр. "
            "Изменения затронули группы направлений ИТ и телекоммуникаций.",
            "Деканат МТУСИ",
        ),
        (
            "Хакатон по искусственному интеллекту",
            "МТУСИ проводит открытый хакатон по AI/ML. Участники решают задачи "
            "обработки естественного языка и компьютерного зрения. Призовой фонд — 150 000 руб.",
            "Студсовет",
        ),
        (
            "Новая лаборатория кибербезопасности",
            "На факультете ИТ открылась лаборатория кибербезопасности с современным "
            "оборудованием для практических занятий по сетевой безопасности и пентесту.",
            "Пресс-служба МТУСИ",
        ),
        (
            "Результаты олимпиады по программированию",
            "Подведены итоги внутренней олимпиады. Первое место занял студент 3 курса "
            "направления «Информатика и вычислительная техника». Поздравляем победителей!",
            "Кафедра ИВТ",
        ),
        (
            "День открытых дверей — 15 марта",
            "Приглашаем абитуриентов и их родителей на день открытых дверей. "
            "Будет презентация факультетов, экскурсия по лабораториям и ответы на вопросы.",
            "Приёмная комиссия",
        ),
    ]
    conn.executemany(
        "INSERT INTO articles (title, summary, author) VALUES (?, ?, ?)",
        articles,
    )


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_user(username: str, password: str, gender: str) -> dict | None:
    conn = get_connection()
    try:
        conn.execute(
            "INSERT INTO users (username, password_hash, gender) VALUES (?, ?, ?)",
            (username, _hash_password(password), gender),
        )
        conn.commit()
        cur = conn.execute("SELECT id, username, gender FROM users WHERE username = ?", (username,))
        user = dict(cur.fetchone())
        return user
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def authenticate_user(username: str, password: str) -> dict | None:
    conn = get_connection()
    cur = conn.execute(
        "SELECT id, username, gender, password_hash FROM users WHERE username = ?",
        (username,),
    )
    row = cur.fetchone()
    conn.close()
    if row and row["password_hash"] == _hash_password(password):
        return {"id": row["id"], "username": row["username"], "gender": row["gender"]}
    return None


def save_prediction(text: str, label: str, score: float, user_id: int | None = None):
    conn = get_connection()
    conn.execute(
        "INSERT INTO predictions (text, label, score, user_id) VALUES (?, ?, ?, ?)",
        (text, label, score, user_id),
    )
    conn.commit()
    conn.close()


def get_stats() -> dict:
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM predictions")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM predictions WHERE label = 'toxic'")
    toxic_count = cur.fetchone()[0]

    neutral_count = total - toxic_count

    toxic_percent = round(toxic_count / total * 100, 1) if total > 0 else 0

    cur.execute("SELECT AVG(score) FROM predictions WHERE label = 'toxic'")
    row = cur.fetchone()
    avg_toxic_score = round(row[0], 4) if row[0] is not None else 0

    cur.execute(
        "SELECT text, label, score, created_at FROM predictions ORDER BY created_at DESC LIMIT 10"
    )
    recent = [dict(r) for r in cur.fetchall()]

    # Статистика по полу
    by_gender = []
    cur.execute("""
        SELECT u.gender,
               COUNT(*) as total,
               SUM(CASE WHEN p.label = 'toxic' THEN 1 ELSE 0 END) as toxic_count
        FROM predictions p
        JOIN users u ON p.user_id = u.id
        GROUP BY u.gender
    """)
    for row in cur.fetchall():
        gender_total = row["total"]
        gender_toxic = row["toxic_count"]
        by_gender.append({
            "gender": row["gender"],
            "total": gender_total,
            "toxic_count": gender_toxic,
            "toxic_percent": round(gender_toxic / gender_total * 100, 1) if gender_total > 0 else 0,
        })

    conn.close()

    return {
        "total_checks": total,
        "toxic_count": toxic_count,
        "neutral_count": neutral_count,
        "toxic_percent": toxic_percent,
        "avg_toxic_score": avg_toxic_score,
        "recent": recent,
        "by_gender": by_gender,
    }


def get_articles() -> list[dict]:
    conn = get_connection()
    cur = conn.execute("SELECT id, title, summary, author, created_at FROM articles ORDER BY id")
    articles = [dict(r) for r in cur.fetchall()]
    conn.close()
    return articles


def get_article(article_id: int) -> dict | None:
    conn = get_connection()
    cur = conn.execute(
        "SELECT id, title, summary, author, created_at FROM articles WHERE id = ?",
        (article_id,),
    )
    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


def save_comment(article_id: int, user_id: int, text: str) -> dict:
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO comments (article_id, user_id, text) VALUES (?, ?, ?)",
        (article_id, user_id, text),
    )
    comment_id = cur.lastrowid
    conn.commit()
    cur = conn.execute(
        """SELECT c.id, c.article_id, c.user_id, u.username, c.text, c.created_at
           FROM comments c JOIN users u ON c.user_id = u.id
           WHERE c.id = ?""",
        (comment_id,),
    )
    comment = dict(cur.fetchone())
    conn.close()
    return comment


def get_comments(article_id: int) -> list[dict]:
    conn = get_connection()
    cur = conn.execute(
        """SELECT c.id, c.article_id, c.user_id, u.username, c.text, c.created_at
           FROM comments c JOIN users u ON c.user_id = u.id
           WHERE c.article_id = ?
           ORDER BY c.created_at DESC""",
        (article_id,),
    )
    comments = [dict(r) for r in cur.fetchall()]
    conn.close()
    return comments
