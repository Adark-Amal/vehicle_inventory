import os
from dotenv import load_dotenv
import pymysql

# Load environment variables from .env file
load_dotenv()


class Config:
    """Base configuration with default settings for MySQL database."""

    # Database settings for MySQL
    DB_USER = os.getenv("DB_USER", "root")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "3306")
    DB_NAME = os.getenv("DB_NAME", "north_avenue")

    # SQLAlchemy database URI for MySQL
    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )

    # Secret key for session management (change in production)
    SECRET_KEY = os.getenv("SECRET_KEY", "your_default_secret_key")

    # Streamlit authenticator configuration
    COOKIE_NAME = "auto_dealership_auth"
    COOKIE_EXPIRY_DAYS = 1


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


# Dictionary to fetch configurations based on the environment
config = {"development": DevelopmentConfig, "production": ProductionConfig}

# Set up the current config based on the environment
current_config = config[os.getenv("ENV", "development")]
