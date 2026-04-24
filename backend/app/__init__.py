from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from app.config.config import config

db = SQLAlchemy()


def create_app(env: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[env])

    db.init_app(app)
    CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)

    # ── Blueprints ─────────────────────────────────────────────────────────────
    from app.auth.auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    # Nouveau : routes de prédiction Chl-a
    from app.routes.prediction_routes import predict_bp
    app.register_blueprint(predict_bp)

    # ── Base de données ────────────────────────────────────────────────────────
    with app.app_context():
        db.create_all()

        # Préchargement du modèle ML au démarrage (évite le délai à la 1ère requête)
        try:
            from app.services.prediction_service import load_model
            load_model()
        except FileNotFoundError:
            app.logger.warning(
                "⚠️  Fichiers ML introuvables au démarrage. "
                "Déposez 'catboost_lagune_chla.cbm' et 'catboost_meta.json' "
                "dans backend/app/ml_models/"
            )

    return app
