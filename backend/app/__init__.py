from flask import Flask
from flask_cors import CORS
from app.extensions import db          # ← db vient de extensions.py
from app.config.config import config


def create_app(env: str = "default") -> Flask:
    app = Flask(__name__)
    app.config.from_object(config[env])

    # Initialise db AVEC l'app Flask
    # Pourquoi init_app ? db est créé sans app dans extensions.py,
    # donc on doit l'attacher à l'app ici.
    db.init_app(app)

    CORS(app, origins=app.config["CORS_ORIGINS"], supports_credentials=True)

    # Importer et enregistrer les routes
    from app.auth.auth_routes import auth_bp
    app.register_blueprint(auth_bp)

    # Créer les tables dans la base de données
    with app.app_context():
        db.create_all()

    return app