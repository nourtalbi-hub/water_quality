"""
preprocessing_service.py
────────────────────────
Compatible pandas 1.x, 2.x et 3.x — Windows et Linux

Features attendues par le modèle (ordre strict) :
    Depth | O2 | pH | salinity | Temperature |
    Total_Nitrogen | Total_Phosphorus | Station | Month | Year
"""

import io
import logging
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Features attendues par le modèle ──────────────────────────────────────────
MODEL_FEATURES = [
    "Depth", "O2", "pH", "salinity", "Temperature",
    "Total_Nitrogen", "Total_Phosphorus",
    "Station", "Month", "Year"
]

# Plages réalistes pour imputation aléatoire
IMPUTATION_RANGES = {
    "Depth":            (0.8,   2.2),
    "O2":               (57.0, 111.0),
    "salinity":         (32.0,  45.0),
    "Total_Nitrogen":   (259.0, 1467.0),
    "Total_Phosphorus": (11.0,   32.0),
}

# Correspondance colonnes station IoT → colonnes modèle
COLUMN_ALIASES = {
    "temp(c)":          "Temperature",
    "temperature":      "Temperature",
    "temp":             "Temperature",
    "o2":               "O2",
    "oxygen":           "O2",
    "oxygene":          "O2",
    "ph":               "pH",
    "salinity":         "salinity",
    "salinite":         "salinity",
    "sal":              "salinity",
    "depth":            "Depth",
    "profondeur":       "Depth",
    "total_nitrogen":   "Total_Nitrogen",
    "nitrogen":         "Total_Nitrogen",
    "azote":            "Total_Nitrogen",
    "total_phosphorus": "Total_Phosphorus",
    "phosphorus":       "Total_Phosphorus",
    "phosphore":        "Total_Phosphorus",
    "station":          "Station",
    "month":            "Month",
    "year":             "Year",
    "mois":             "Month",
    "annee":            "Year",
}

# Colonnes parasites à ignorer
COLUMNS_TO_DROP = {
    "n", "num", "numero", "index",
    "tcarte(c)", "tcarte", "t carte",
    "turb(ntu)", "turbidite", "turb", "turbidity",
    "notes", "remarques", "commentaires",
    "unnamed: 7", "unnamed: 8", "unnamed: 9",
}

# Valeur par défaut pour Station si absente du fichier
DEFAULT_STATION = 1


# ─────────────────────────────────────────────────────────────────────────────
#  Point d'entrée public
# ─────────────────────────────────────────────────────────────────────────────

def preprocess_file(file_bytes: bytes, filename: str,
                    station_id: int = DEFAULT_STATION) -> pd.DataFrame:
    """
    Prend le contenu brut d'un fichier (CSV ou XLSX) et retourne un DataFrame
    propre avec exactement les colonnes MODEL_FEATURES + un index DatetimeIndex.

    Parameters
    ----------
    file_bytes : bytes   Contenu du fichier uploadé
    filename   : str     Nom original (pour détecter l'extension)
    station_id : int     Identifiant de la station (passé depuis la route)

    Returns
    -------
    pd.DataFrame  — index DatetimeIndex (1h), colonnes MODEL_FEATURES
    """
    # 1. Lecture — SANS dtype=str pour garder les vrais types pandas
    df = _read_file(file_bytes, filename)
    logger.info("Fichier lu : %d lignes, colonnes = %s", len(df), list(df.columns))

    # 2. Reconstruction du DatetimeIndex
    df = _build_datetime_index(df)

    # 3. Supprimer les lignes avec date invalide (NaT)
    nat_count = df.index.isna().sum()
    if nat_count > 0:
        logger.warning("Suppression de %d lignes avec date invalide", nat_count)
        df = df[df.index.notna()]

    if df.empty:
        raise ValueError("Aucune ligne avec une date valide dans le fichier.")

    df.index = pd.DatetimeIndex(df.index)

    # 4. Convertir les colonnes de mesures en numérique
    for col in df.columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # 5. Tri chronologique
    df = df.sort_index()

    # 6. Resampling horaire → 24 obs/jour
    df = df.resample("1h").mean()
    logger.info("Apres resampling horaire : %d lignes", len(df))

    # 7. Renommage des colonnes connues
    df = _rename_columns(df)

    # 8. Suppression des colonnes hors-modèle
    df = _drop_irrelevant_columns(df)

    # 9. Imputation des paramètres physiques totalement absents
    df = _impute_missing_features(df)

    # 10. Interpolation des NaN résiduels
    df = df.interpolate(method="time").bfill().ffill()

    # 11. Ajout des features temporelles et station (calculées depuis l'index)
    df = _add_temporal_features(df, station_id)

    # 12. Ordonner exactement comme le modèle l'attend
    df = df[MODEL_FEATURES]

    logger.info("Pretraitement termine : %d lignes, colonnes = %s",
                len(df), list(df.columns))
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  Lecture du fichier
# ─────────────────────────────────────────────────────────────────────────────

def _read_file(file_bytes: bytes, filename: str) -> pd.DataFrame:
    """Lit CSV ou XLSX. Laisse pandas inférer les types (pas de dtype=str)."""
    ext = filename.rsplit(".", 1)[-1].lower()
    buf = io.BytesIO(file_bytes)

    if ext in ("xlsx", "xlsm", "xls"):
        df = pd.read_excel(buf)
    else:
        for sep in (",", ";", "\t"):
            try:
                buf.seek(0)
                df = pd.read_csv(buf, sep=sep)
                if df.shape[1] > 1:
                    break
            except Exception:
                continue
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  Construction du DatetimeIndex
# ─────────────────────────────────────────────────────────────────────────────

def _build_datetime_index(df: pd.DataFrame) -> pd.DataFrame:
    """
    Reconstruit le DatetimeIndex à partir des colonnes Date + Heure.

    Gère tous les formats possibles :
      - Date  : datetime64, Timestamp, numéro série Excel, string
      - Heure : datetime.time, fraction décimale, string HH:MM:SS
    """
    cols_lower = {c.lower(): c for c in df.columns}
    date_col  = _find_column(cols_lower, ["date"])
    heure_col = _find_column(cols_lower, ["heure", "time", "hour"])

    if date_col and heure_col:
        date_vals  = df[date_col]
        heure_vals = df[heure_col]

        # ── Conversion de la colonne Date ─────────────────────────────────────
        if pd.api.types.is_datetime64_any_dtype(date_vals):
            # Déjà datetime64 (cas le plus fréquent avec xlsx)
            date_str = date_vals.dt.strftime("%Y-%m-%d")
        elif _is_excel_serial(date_vals):
            # Numéro série Excel (ex: 46104)
            dates_conv = date_vals.apply(_excel_serial_to_date)
            date_str = pd.to_datetime(dates_conv, errors="coerce").dt.strftime("%Y-%m-%d")
        else:
            # String date
            date_str = pd.to_datetime(
                date_vals.astype(str), errors="coerce"
            ).dt.strftime("%Y-%m-%d")

        # ── Conversion de la colonne Heure ────────────────────────────────────
        # Cas A : objets datetime.time (Excel lit "10:22:17" comme time)
        if hasattr(heure_vals.iloc[0], 'hour'):
            heure_str = heure_vals.apply(
                lambda x: str(x) if hasattr(x, 'hour') else "00:00:00"
            )
        # Cas B : fraction décimale (ex: 0.4321)
        elif _is_decimal_fraction(heure_vals):
            heure_str = heure_vals.apply(_frac_to_timestr)
        # Cas C : string HH:MM ou HH:MM:SS
        else:
            heure_str = heure_vals.astype(str).str.strip()
            heure_str = heure_str.replace(["nan", "NaT", "None", ""], "00:00:00")

        # ── Combinaison finale ────────────────────────────────────────────────
        combined  = date_str.fillna("") + " " + heure_str.fillna("00:00:00")
        datetimes = pd.to_datetime(combined, errors="coerce")

        df.index = pd.DatetimeIndex(datetimes)
        df = df.drop(columns=[date_col, heure_col], errors="ignore")
        return df

    # ── Fallback : cherche une colonne déjà datetime ──────────────────────────
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df.index = pd.DatetimeIndex(df[col])
            return df.drop(columns=[col])
        converted = pd.to_datetime(df[col].astype(str), errors="coerce")
        if converted.notna().sum() > len(df) * 0.5:
            df.index = pd.DatetimeIndex(converted)
            return df.drop(columns=[col])

    # ── Dernier recours : index synthétique ──────────────────────────────────
    logger.warning("Index synthetique cree (2min d'intervalle).")
    start = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    df.index = pd.date_range(start=start, periods=len(df), freq="2min")
    return df


# ─────────────────────────────────────────────────────────────────────────────
#  Features temporelles + Station
# ─────────────────────────────────────────────────────────────────────────────

def _add_temporal_features(df: pd.DataFrame, station_id: int) -> pd.DataFrame:
    """
    Ajoute Month, Year (depuis l'index DatetimeIndex) et Station.
    Ces 3 features sont requises par le modèle.
    """
    # Station : utilise la colonne existante ou la valeur par défaut
    if "Station" not in df.columns:
        df["Station"] = float(station_id)
        logger.info("Feature 'Station' absente -> valeur par defaut = %d", station_id)

    # Month et Year : toujours recalculés depuis l'index (fiables)
    df["Month"] = df.index.month.astype(float)
    df["Year"]  = df.index.year.astype(float)

    return df


# ─────────────────────────────────────────────────────────────────────────────
#  Helpers internes
# ─────────────────────────────────────────────────────────────────────────────

def _rename_columns(df: pd.DataFrame) -> pd.DataFrame:
    rename_map = {}
    for col in df.columns:
        alias = COLUMN_ALIASES.get(col.strip().lower())
        if alias and col != alias:
            rename_map[col] = alias
    return df.rename(columns=rename_map)


def _drop_irrelevant_columns(df: pd.DataFrame) -> pd.DataFrame:
    # Garder les colonnes qui sont dans MODEL_FEATURES OU qui seront ajoutées après
    keep = set(MODEL_FEATURES) - {"Month", "Year", "Station"}
    to_drop = [
        col for col in df.columns
        if col.strip().lower() in COLUMNS_TO_DROP or col not in keep
    ]
    return df.drop(columns=to_drop, errors="ignore")


def _impute_missing_features(df: pd.DataFrame) -> pd.DataFrame:
    rng = np.random.default_rng(seed=42)
    for feature, (low, high) in IMPUTATION_RANGES.items():
        if feature not in df.columns:
            logger.warning(
                "Parametre '%s' absent -> imputation aleatoire [%.1f - %.1f]",
                feature, low, high
            )
            df[feature] = rng.uniform(low, high, size=len(df))
    return df


def _find_column(cols_lower: dict, candidates: list):
    for name in candidates:
        if name in cols_lower:
            return cols_lower[name]
    return None


def _is_excel_serial(series: pd.Series) -> bool:
    """Détecte les numéros série Excel (entiers entre 40000 et 60000)."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return False
    try:
        numeric = pd.to_numeric(series, errors="coerce").dropna()
        if len(numeric) == 0:
            return False
        return bool(
            (numeric > 40_000).mean() > 0.8 and
            (numeric < 60_000).mean() > 0.8
        )
    except Exception:
        return False


def _is_decimal_fraction(series: pd.Series) -> bool:
    """Détecte les fractions décimales [0, 1)."""
    try:
        numeric = pd.to_numeric(series, errors="coerce").dropna()
        if len(numeric) == 0:
            return False
        return bool(((numeric >= 0) & (numeric < 1)).mean() > 0.8)
    except Exception:
        return False


def _frac_to_timestr(x) -> str:
    """Convertit une fraction décimale en string HH:MM:SS."""
    try:
        td = timedelta(days=float(x))
        total_sec = int(td.total_seconds())
        h = total_sec // 3600
        m = (total_sec % 3600) // 60
        s = total_sec % 60
        return f"{h:02d}:{m:02d}:{s:02d}"
    except Exception:
        return "00:00:00"


def _excel_serial_to_date(serial) -> datetime:
    """Convertit un numéro série Excel en datetime."""
    try:
        return datetime(1899, 12, 30) + timedelta(days=float(serial))
    except Exception:
        return pd.NaT