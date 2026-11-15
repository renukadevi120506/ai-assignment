import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "evaluator-tp10-development-secret-key-3.12")
    
    # SQLite configuration - on Vercel / serverless, filesystem is read-only except /tmp
    is_vercel = os.environ.get("VERCEL") or os.environ.get("NOW_REGION")
    default_sqlite_path = "/tmp/evaluator.db" if is_vercel else str(BASE_DIR / "evaluator.db")
    
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL") or f"sqlite:///{default_sqlite_path}"
    # In case someone provides postgresql URI
    if SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Uploads - use /tmp/uploads on Vercel
    default_upload_folder = "/tmp/uploads" if is_vercel else str(BASE_DIR / "uploads")
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", default_upload_folder)
    MAX_CONTENT_LENGTH = int(os.environ.get("MAX_CONTENT_LENGTH", 16 * 1024 * 1024)) # 16 MB
    ALLOWED_EXTENSIONS = {"pdf", "docx", "txt"}
    
    # LLM Settings
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
    DEFAULT_LLM_PROVIDER = os.environ.get("DEFAULT_LLM_PROVIDER", "gemini") # gemini or ollama
    
    OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3")
    
    # Vector DB (Qdrant) - supports in-memory (:memory:) or remote URL
    QDRANT_URL = os.environ.get("QDRANT_URL", "") # empty means in-memory / local
    QDRANT_API_KEY = os.environ.get("QDRANT_API_KEY", "")
    QDRANT_COLLECTION = os.environ.get("QDRANT_COLLECTION", "educational_documents")

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False

config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
    "default": DevelopmentConfig
}
