"""
app/config.py
-------------
Centralised application configuration for the app/ package.

Loads all runtime settings from the project .env file (via python-dotenv)
and exposes them as typed, documented attributes on a single ``AppConfig``
instance called ``cfg``.

Usage
-----
    from app.config import cfg

    # Database
    conn = sqlite3.connect(cfg.DB_PATH)       # SQLite convenience path
    url  = cfg.DATABASE_URL                   # full connection string

    # Data directories
    df = pd.read_csv(os.path.join(cfg.RAW_DATA_DIR, "sales.csv"))

    # Model artefacts
    model   = joblib.load(cfg.SALES_MODEL_PATH)
    shap_ex = joblib.load(cfg.SALES_SHAP_PATH)

    # LLM placeholder (not wired yet)
    print(cfg.LLM_PROVIDER)   # e.g. "openai" when set in .env

Design notes
------------
- ``app/config.py`` is the single source of truth for ALL path and
  connection settings inside the ``app/`` package.
- ``config/settings.py`` (the existing Flask/ERP config) is NOT imported
  here — this module is self-contained so it can be tested in isolation.
- Every attribute has a safe, development-friendly default so the app
  starts without a populated .env.
- Model artefact filenames are controlled by env vars
  (SALES_MODEL_VERSION, INVENTORY_MODEL_VERSION) so ops can swap a
  promoted model by updating .env without touching code.
"""

import os
import sys
from urllib.parse import urlparse

# --------------------------------------------------------------------------- #
# Bootstrap: project root on sys.path
# --------------------------------------------------------------------------- #
_APP_DIR      = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_APP_DIR)
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from dotenv import load_dotenv

# Load .env — override=False means already-set env vars win (12-factor friendly)
load_dotenv(os.path.join(_PROJECT_ROOT, ".env"), override=False)


# --------------------------------------------------------------------------- #
# Private helpers
# --------------------------------------------------------------------------- #

def _abs(*parts: str) -> str:
    """Return an absolute path anchored at the project root."""
    return os.path.join(_PROJECT_ROOT, *parts)


def _sqlite_file_path(database_url: str) -> str:
    """
    Derive a filesystem path from a SQLite DATABASE_URL.

    Handles both URL forms:
      sqlite:///relative.db    →  <project_root>/relative.db
      sqlite:////absolute.db   →  /absolute.db   (four slashes = absolute)

    Returns an empty string for non-SQLite backends (Postgres, MySQL …).
    Falls back to the legacy default path when *database_url* is blank.
    """
    if not database_url:
        return _abs("database", "platform.db")

    parsed = urlparse(database_url)
    if parsed.scheme != "sqlite":
        return ""   # not a local file; callers should use DATABASE_URL directly

    path = parsed.path  # "/ai_decision.db" or "//absolute"
    # Three-slash form: path starts with "/" but is relative to project root
    if path.startswith("/") and not path.startswith("//"):
        path = path.lstrip("/")   # "ai_decision.db"
        return _abs(path)
    # Four-slash form: truly absolute
    return path


def _model_stem(env_key: str, default: str) -> str:
    """Return the model filename stem from env or default."""
    return os.getenv(env_key, default)


def _model_path(stem: str) -> str:
    """Absolute path to a model .pkl file inside models/."""
    return _abs("models", f"{stem}.pkl")


def _shap_path(model_stem: str) -> str:
    """
    Derive the SHAP explainer path from the model stem.

    Convention:
      sales_rf          →  sales_shap.pkl
      sales_rf_v2       →  sales_shap_v2.pkl
      inventory_rf      →  inventory_shap.pkl
      inventory_rf_v2   →  inventory_shap_v2.pkl
    """
    shap_stem = model_stem.replace("_rf", "_shap", 1)
    if shap_stem == model_stem:           # "_rf" not in stem — append "_shap"
        shap_stem = f"{model_stem}_shap"
    return _abs("models", f"{shap_stem}.pkl")


# --------------------------------------------------------------------------- #
# Configuration class
# --------------------------------------------------------------------------- #

class AppConfig:
    """
    Runtime configuration for the ``app/`` package.

    All values are resolved at import time from environment variables
    (loaded from .env).  Every attribute has a documented default that is
    safe for local development.

    Attributes — Database
    ----------------------
    DATABASE_URL : str
        Full connection string, e.g. ``sqlite:///ai_decision.db`` or
        ``postgresql://user:pass@host:5432/dbname``.
        Env var: ``DATABASE_URL``   Default: ``sqlite:///ai_decision.db``

    DB_PATH : str
        Absolute filesystem path derived from DATABASE_URL when the scheme
        is ``sqlite``.  Empty string for non-SQLite backends.

    Attributes — Data directories
    ------------------------------
    BASE_DIR, DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR : str
        Absolute paths to the project root and data sub-directories.

    Attributes — Model artefacts
    -----------------------------
    SALES_MODEL_PATH : str
        Absolute path to models/<SALES_MODEL_VERSION>.pkl
        Env var: ``SALES_MODEL_VERSION``   Default stem: ``sales_rf``

    SALES_SHAP_PATH : str
        Absolute path to models/<sales_shap_stem>.pkl
        (derived from SALES_MODEL_VERSION with "_rf" → "_shap")

    INVENTORY_MODEL_PATH : str
        Absolute path to models/<INVENTORY_MODEL_VERSION>.pkl
        Env var: ``INVENTORY_MODEL_VERSION``  Default stem: ``inventory_rf``

    INVENTORY_SHAP_PATH : str
        Absolute path to models/<inventory_shap_stem>.pkl

    Attributes — LLM (placeholder, not used yet)
    ---------------------------------------------
    LLM_PROVIDER : str | None
        Provider name, e.g. ``"openai"``, ``"anthropic"``, ``"google"``,
        ``"ollama"``.  Loaded from .env but wired to no code yet.
        Env var: ``LLM_PROVIDER``

    LLM_API_KEY : str | None
        API key for the configured LLM provider.
        Loaded from .env but wired to no code yet.
        Env var: ``LLM_API_KEY``
    """

    # ----------------------------------------------------------------------- #
    # Database
    # ----------------------------------------------------------------------- #
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///ai_decision.db")
    DB_PATH:      str = _sqlite_file_path(
                            os.getenv("DATABASE_URL", "sqlite:///ai_decision.db")
                        )

    # ----------------------------------------------------------------------- #
    # Data directories
    # ----------------------------------------------------------------------- #
    BASE_DIR:            str = _PROJECT_ROOT
    DATA_DIR:            str = _abs("data")
    RAW_DATA_DIR:        str = _abs("data", "raw")
    PROCESSED_DATA_DIR:  str = _abs("data", "processed")

    # ----------------------------------------------------------------------- #
    # Model artefact paths
    # ----------------------------------------------------------------------- #
    _sales_stem:     str = _model_stem("SALES_MODEL_VERSION",     "sales_rf")
    _inventory_stem: str = _model_stem("INVENTORY_MODEL_VERSION", "inventory_rf")

    SALES_MODEL_PATH:     str = _model_path(_model_stem("SALES_MODEL_VERSION",     "sales_rf"))
    SALES_SHAP_PATH:      str = _shap_path( _model_stem("SALES_MODEL_VERSION",     "sales_rf"))
    INVENTORY_MODEL_PATH: str = _model_path(_model_stem("INVENTORY_MODEL_VERSION", "inventory_rf"))
    INVENTORY_SHAP_PATH:  str = _shap_path( _model_stem("INVENTORY_MODEL_VERSION", "inventory_rf"))

    # ----------------------------------------------------------------------- #
    # LLM — placeholder only, no implementation yet
    # ----------------------------------------------------------------------- #
    LLM_PROVIDER: str | None = os.getenv("LLM_PROVIDER")  # e.g. "openai"
    LLM_API_KEY:  str | None = os.getenv("LLM_API_KEY")   # secret; never log


# --------------------------------------------------------------------------- #
# Module-level singleton — import this everywhere
# --------------------------------------------------------------------------- #
cfg = AppConfig()


# --------------------------------------------------------------------------- #
# CLI inspection helper
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    _MASK = {"LLM_API_KEY"}

    print("=" * 64)
    print("  app/config.py — resolved configuration")
    print("=" * 64)
    for _attr in [
        "DATABASE_URL", "DB_PATH",
        "BASE_DIR", "RAW_DATA_DIR", "PROCESSED_DATA_DIR",
        "SALES_MODEL_PATH", "SALES_SHAP_PATH",
        "INVENTORY_MODEL_PATH", "INVENTORY_SHAP_PATH",
        "LLM_PROVIDER", "LLM_API_KEY",
    ]:
        _val = getattr(cfg, _attr)
        if _attr in _MASK and _val:
            _val = _val[:6] + "…(masked)"
        print(f"  {_attr:<28}: {_val}")
    print("=" * 64)
