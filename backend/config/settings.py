import os
from dotenv import load_dotenv

# Absolute path to the directory containing this file
current_dir = os.path.dirname(os.path.abspath(__file__))
# Project root directory
BASE_DIR = os.path.dirname(current_dir)

# Load environment variables from .env file in project root
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Settings:
    # ERP Configuration
    ERP_BASE_URL = os.getenv("ERP_BASE_URL")
    ERP_API_KEY = os.getenv("ERP_API_KEY")
    ERP_API_SECRET = os.getenv("ERP_API_SECRET")
    
    # Path Configuration
    BASE_DIR = BASE_DIR
    DATA_DIR = os.path.join(BASE_DIR, "data")
    RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
    PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")

class Config(Settings):
    """Flask configuration class."""
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    DEBUG = os.getenv("FLASK_DEBUG", "True") == "True"

# Global settings instance
settings = Settings()
