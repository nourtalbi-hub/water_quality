"""
prediction_routes.py
────────────────────
Blueprint Flask exposant les endpoints de prédiction Chl-a.

Endpoints :
    POST  /api/predict/upload     → upload CSV/XLSX + prédiction complète
    GET   /api/predict/levels     → tableau de référence des niveaux de pollution
    GET   /api/predict/model-info → métadonnées du modèle chargé
"""

import logging

from flask import Blueprint, jsonify, request

from app.services import prediction_service, preprocessing_service

logger = logging.getLogger(__name__)

predict_bp = Blueprint("predict", __name__, url_prefix="/api/predict")

# ── Constantes ────────────────────────────────────────────────────────────────
MAX_FILE_SIZE_MB = 10
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xlsm", "xls"}


# ─────────────────────────────────────────────────────────────────────────────
#  POST /api/predict/upload
# ─────────────────────────────────────────────────────────────────────────────

@predict_bp.route("/upload", methods=["POST"])
def upload_and_predict():
    """
    Reçoit un fichier CSV ou XLSX (multipart/form-data, champ 'file'),
    exécute le pipeline complet (prétraitement → prédiction) et retourne
    la série temporelle Chl-a avec les niveaux de pollution.

    Requête (multipart/form-data) :
        file      : fichier CSV ou XLSX
        station   : (optionnel) nom de la station — string

    Réponse 200 (JSON) :
        {
            "success":     true,
            "station":     "Station IoT",
            "predictions": [ { datetime, chl_a, niveau, couleur, inputs }, ... ],
            "summary":     { total_points, chl_a_min, chl_a_max, ... }
        }
    """
    # ── Validation de la requête ──────────────────────────────────────────────
    if "file" not in request.files:
        return jsonify({"success": False, "error": "Aucun fichier envoyé (champ 'file' manquant)"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"success": False, "error": "Nom de fichier vide"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({
            "success": False,
            "error": f"Extension '{ext}' non supportée. Formats acceptés : {', '.join(ALLOWED_EXTENSIONS)}"
        }), 415

    # Lecture des bytes
    file_bytes = file.read()
    size_mb = len(file_bytes) / (1024 * 1024)
    if size_mb > MAX_FILE_SIZE_MB:
        return jsonify({
            "success": False,
            "error": f"Fichier trop volumineux ({size_mb:.1f} Mo > {MAX_FILE_SIZE_MB} Mo max)"
        }), 413

    station_name = request.form.get("station", "Station inconnue")

    # ── Pipeline ──────────────────────────────────────────────────────────────
    try:
        # Étape 1 : Prétraitement
        logger.info("Début du prétraitement pour '%s'", file.filename)
        df_clean = preprocessing_service.preprocess_file(file_bytes, file.filename)

        if df_clean.empty:
            return jsonify({
                "success": False,
                "error": "Le fichier ne contient aucune donnée exploitable après prétraitement."
            }), 422

        # Étape 2 : Prédiction
        logger.info("Début de la prédiction (%d lignes)", len(df_clean))
        predictions = prediction_service.predict(df_clean)

        # Étape 3 : Résumé statistique
        summary = prediction_service.compute_summary(predictions)

        return jsonify({
            "success":     True,
            "station":     station_name,
            "filename":    file.filename,
            "predictions": predictions,
            "summary":     summary,
        }), 200

    except FileNotFoundError as e:
        logger.error("Modèle introuvable : %s", str(e))
        return jsonify({"success": False, "error": str(e)}), 503

    except Exception as e:
        logger.exception("Erreur lors du traitement du fichier")
        return jsonify({"success": False, "error": f"Erreur serveur : {str(e)}"}), 500


# ─────────────────────────────────────────────────────────────────────────────
#  GET /api/predict/levels
# ─────────────────────────────────────────────────────────────────────────────

@predict_bp.route("/levels", methods=["GET"])
def get_pollution_levels():
    """
    Retourne le tableau de référence des niveaux de pollution Chl-a.
    Utilisé par le frontend pour construire la légende du graphe.
    """
    return jsonify({
        "levels": [
            {
                "label":       "Faible",
                "description": "Eau propre, peu d'algues",
                "chl_a_min":   0,
                "chl_a_max":   2,
                "couleur":     "#2ECC71",
            },
            {
                "label":       "Modéré",
                "description": "Productivité moyenne",
                "chl_a_min":   2,
                "chl_a_max":   10,
                "couleur":     "#F5A623",
            },
            {
                "label":       "Élevé",
                "description": "Début d'eutrophisation",
                "chl_a_min":   10,
                "chl_a_max":   50,
                "couleur":     "#E67E22",
            },
            {
                "label":       "Très élevé",
                "description": "Pollution / prolifération d'algues",
                "chl_a_min":   50,
                "chl_a_max":   None,
                "couleur":     "#E74C3C",
            },
        ]
    }), 200


# ─────────────────────────────────────────────────────────────────────────────
#  GET /api/predict/model-info
# ─────────────────────────────────────────────────────────────────────────────

@predict_bp.route("/model-info", methods=["GET"])
def model_info():
    """
    Retourne les métadonnées du modèle chargé (features, version...).
    Utile pour le débogage et l'affichage dans le dashboard.
    """
    try:
        model = prediction_service.load_model()
        return jsonify({
            "success": True,
            "model_type": type(model).__name__,
            "features":   preprocessing_service.MODEL_FEATURES,
            "target":     "Chl-a (µg/L)",
            "model_path": str(prediction_service.MODEL_PATH),
        }), 200
    except FileNotFoundError as e:
        return jsonify({"success": False, "error": str(e)}), 503
