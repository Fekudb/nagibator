from config import FLASK_PORT
from web.app import app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=FLASK_PORT, debug=True)
