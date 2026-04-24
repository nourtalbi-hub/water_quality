from flask import Blueprint, request, jsonify
from werkzeug.exceptions import BadRequest
from datetime import datetime, timedelta
from app import db
from app.models.user_model import User
import jwt
import os

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

SECRET = os.environ.get("JWT_SECRET_KEY", "jwt-secret-change-me")
EXPIRES = 3600  # 1 heure


def generate_token(user: User) -> str:
    payload = {
        "user_id":  user.id,
        "username": user.username,
        "role":     user.role,
        "exp":      datetime.utcnow() + timedelta(seconds=EXPIRES),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, SECRET, algorithms=["HS256"])


# ── POST /api/auth/register ───────────────────────────────────────────────────
@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    # Validation des champs obligatoires
    for field in ("username", "email", "password"):
        if not data.get(field):
            return jsonify({"error": f"Le champ '{field}' est requis."}), 400

    # Vérification unicité
    if User.query.filter_by(username=data["username"]).first():
        return jsonify({"error": "Ce nom d'utilisateur est déjà pris."}), 409
    if User.query.filter_by(email=data["email"]).first():
        return jsonify({"error": "Cette adresse email est déjà utilisée."}), 409

    # Longueur mot de passe
    if len(data["password"]) < 8:
        return jsonify({"error": "Le mot de passe doit contenir au moins 8 caractères."}), 400

    user = User(
        username=data["username"],
        email=data["email"],
        role=data.get("role", "operator"),
    )
    user.set_password(data["password"])

    db.session.add(user)
    db.session.commit()

    token = generate_token(user)

    return jsonify({
        "message": "Compte créé avec succès.",
        "token":   token,
        "user":    user.to_dict(),
    }), 201


# ── POST /api/auth/login ──────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json()

    if not data.get("username") or not data.get("password"):
        return jsonify({"error": "Identifiant et mot de passe requis."}), 400

    # Recherche par username OU email
    user = (
        User.query.filter_by(username=data["username"]).first()
        or User.query.filter_by(email=data["username"]).first()
    )

    if not user or not user.check_password(data["password"]):
        return jsonify({"error": "Identifiant ou mot de passe incorrect."}), 401

    if not user.is_active:
        return jsonify({"error": "Ce compte a été désactivé."}), 403

    # Mise à jour last_login
    user.last_login = datetime.utcnow()
    db.session.commit()

    token = generate_token(user)

    return jsonify({
        "message": "Connexion réussie.",
        "token":   token,
        "user":    user.to_dict(),
    }), 200


# ── GET /api/auth/me ──────────────────────────────────────────────────────────
@auth_bp.route("/me", methods=["GET"])
def me():
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        return jsonify({"error": "Token manquant."}), 401

    try:
        payload = decode_token(auth_header.split(" ")[1])
        user = User.query.get(payload["user_id"])
        if not user:
            return jsonify({"error": "Utilisateur introuvable."}), 404
        return jsonify({"user": user.to_dict()}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"error": "Session expirée. Reconnectez-vous."}), 401
    except jwt.InvalidTokenError:
        return jsonify({"error": "Token invalide."}), 401


# ── POST /api/auth/logout ─────────────────────────────────────────────────────
@auth_bp.route("/logout", methods=["POST"])
def logout():
    # Avec JWT stateless, le logout est géré côté client (suppression du token)
    # Pour une invalidation serveur, utiliser une blacklist Redis
    return jsonify({"message": "Déconnexion effectuée."}), 200
