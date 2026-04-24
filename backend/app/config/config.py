import os


class Config:
    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY         = os.environ.get("SECRET_KEY", "change-me-in-production")
    JWT_SECRET_KEY     = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-me")
    JWT_ACCESS_EXPIRES = 3600        # 1 heure (secondes)

    # ── SQL Server (SSMS) ─────────────────────────────────────────────────────
    # Format : mssql+pyodbc://user:password@server/database?driver=ODBC+Driver+17+for+SQL+Server
    DB_SERVER   = os.environ.get("DB_SERVER",   "localhost")
    DB_NAME     = os.environ.get("DB_NAME",     "water_quality")
    DB_USER     = os.environ.get("DB_USER",     "sa")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "YourPassword123")

    SQLALCHEMY_DATABASE_URI = (
        f"mssql+pyodbc://{DB_USER}:{DB_PASSWORD}@{DB_SERVER}/{DB_NAME}"
        f"?driver=ODBC+Driver+17+for+SQL+Server"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── CORS ──────────────────────────────────────────────────────────────────
    CORS_ORIGINS = ["http://localhost:5173"]    # URL dev Vite


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


config = {
    "development": DevelopmentConfig,
    "production":  ProductionConfig,
    "default":     DevelopmentConfig,
}
