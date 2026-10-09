import os

from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5001"))
