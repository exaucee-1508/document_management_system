import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")

    password = quote_plus(os.getenv("DB_PASSWORD", ""))

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:"
        f"{password}@{os.getenv('DB_HOST')}:"
        f"{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )

    BASE_DIR = Path(__file__).resolve().parent.parent

    DB_SSL_CA = str(BASE_DIR / "certificates" / "ca.pem")

    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "ssl": {
                "ca": DB_SSL_CA
            }
        }
    }

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    UPLOAD_FOLDER = str(BASE_DIR / "uploads")

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024