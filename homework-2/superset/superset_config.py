import os

SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "change-me")
SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset_home/superset.db"

FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_NATIVE_FILTERS": True,
}

CSV_EXTENSIONS = {"csv", "tsv"}
ALLOWED_EXTENSIONS = {"csv", "tsv", "xlsx", "xls"}

PREVENT_UNSAFE_DB_CONNECTIONS = False

CACHE_CONFIG = {
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
}

WTF_CSRF_ENABLED = False
