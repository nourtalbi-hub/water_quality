"""
prediction_service.py — CatBoost + scipy inv_boxcox
Station = string | Month/Year = int
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from catboost import CatBoostRegressor, Pool
from scipy.special import inv_boxcox

logger = logging.getLogger(__name__)

ML_DIR     = Path(__file__).parent.parent / "ml_models"
MODEL_PATH = ML_DIR / "catboost_lagune_chla.cbm"
META_PATH  = ML_DIR / "catboost_meta.json"

_model = None
_meta  = None


def load_model():
    global _model, _meta
    if _model is not None:
        return _model, _meta

    if not MODEL_PATH.exists():
        raise FileNotFoundError(
            f"Modele introuvable : {MODEL_PATH}\n"
            "Deposez 'catboost_lagune_chla.cbm' dans backend/app/ml_models/"
        )
    if not META_PATH.exists():
        raise FileNotFoundError(
            f"Metadonnees introuvables : {META_PATH}\n"
            "Deposez 'catboost_meta.json' dans backend/app/ml_models/"
        )

    _model = CatBoostRegressor()
    _model.load_model(str(MODEL_PATH))
    logger.info("Modele CatBoost charge depuis %s", MODEL_PATH)

    with open(META_PATH, "r", encoding="utf-8") as f:
        _meta = json.load(f)
    logger.info("Meta charge | features=%s | lambda=%.4f",
                _meta.get("features"), _meta.get("lambda_boxcox"))

    return _model, _meta


def predict(df: pd.DataFrame) -> list[dict]:
    model, meta = load_model()

    features      = meta["features"]          # ordre exact du modèle
    lambda_boxcox = meta["lambda_boxcox"]     # λ pour scipy inv_boxcox
    cat_idx       = meta.get("cat_feature_idx", [7])  # index de Station

    # Vérification colonnes
    missing = [f for f in features if f not in df.columns]
    if missing:
        raise ValueError(f"Colonnes manquantes : {missing}")

    # Préparer X avec les bons types
    X = df[features].copy()

    # Station = string (obligatoire pour CatBoost cat_feature)
    X["Station"] = X["Station"].astype(str)

    # Month et Year = int (pas float, pas NaN)
    X["Month"] = X["Month"].fillna(1).astype(int)
    X["Year"]  = X["Year"].fillna(2024).astype(int)

    # Pool CatBoost avec cat_features
    pool = Pool(X, cat_features=cat_idx)

    # Prédiction dans l'espace Box-Cox
    y_transformed = model.predict(pool)

    # Inversion Box-Cox avec scipy (exactement comme le notebook)
    chl_a_values = inv_boxcox(np.array(y_transformed, dtype=float), lambda_boxcox)
    chl_a_values = np.clip(chl_a_values, 0, None)

    logger.info("Prediction : %d pts | Chl-a min=%.3f max=%.3f moy=%.3f µg/L",
                len(chl_a_values),
                chl_a_values.min(), chl_a_values.max(), chl_a_values.mean())

    results = []
    for i, (timestamp, row) in enumerate(df.iterrows()):
        chl_a = float(chl_a_values[i])
        niveau, couleur = _classify(chl_a)
        results.append({
            "datetime": timestamp.isoformat(),
            "chl_a":    round(chl_a, 3),
            "niveau":   niveau,
            "couleur":  couleur,
            "inputs": {
                feat: (str(row[feat]) if feat == "Station"
                       else round(float(row[feat]), 4))
                for feat in features if feat in row.index
            }
        })

    return results


def _classify(chl_a: float) -> tuple:
    if chl_a < 2:
        return "Faible", "#2ECC71"
    elif chl_a < 10:
        return "Modéré", "#F5A623"
    elif chl_a < 50:
        return "Élevé", "#E67E22"
    else:
        return "Très élevé", "#E74C3C"


def compute_summary(predictions: list[dict]) -> dict:
    chl_values = [p["chl_a"] for p in predictions]
    niveaux    = [p["niveau"] for p in predictions]
    counts = {n: niveaux.count(n) for n in ["Faible", "Modéré", "Élevé", "Très élevé"]}
    return {
        "total_points":    len(predictions),
        "chl_a_min":       round(min(chl_values), 3),
        "chl_a_max":       round(max(chl_values), 3),
        "chl_a_moyenne":   round(float(np.mean(chl_values)), 3),
        "niveau_dominant": max(counts, key=counts.get),
        "distribution":    counts,
    }