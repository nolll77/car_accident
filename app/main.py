"""
Serving API BAAC - MLOps Phase 4
FastAPI exposant le modèle (via MLflow) et consommant le Feature Store en temps réel (Feast Redis).
"""

import logging
import os

import pandas as pd
from fastapi import BackgroundTasks, FastAPI, HTTPException
from feast import FeatureStore
from pydantic import BaseModel

# from prometheus_fastapi_instrumentator import Instrumentator # Pour le monitoring SRE

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BAAC_Serving_API")

# [ALERTE MLOPS] P1: Rate-Limiting délégué à l'Ingress (Nginx/Traefik) ou Redis via gateway
app = FastAPI(
    title="BAAC Gravity Prediction API (Famille A)",
    description="API MLOps Temps Réel - Connectée à Feast et MLflow",
    version="1.0.0",
)

# Initialisation SRE Monitoring (Prometheus)
# Instrumentator().instrument(app).expose(app)

# Configuration MLflow Server
MLFLOW_SERVE_URL = os.environ.get(
    "MLFLOW_SERVE_URL", "http://mlflow-serve:5002/invocations"
)

# Initialisation du Feature Store connecté au Repo
repo_path = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "feature_repo", "feature_repo"
)
try:
    FEATURE_STORE = FeatureStore(repo_path=repo_path)
    logger.info("✅ Feast Feature Store connecté avec succès.")
except Exception as e:
    logger.error(f"❌ Erreur lors de l'initialisation de Feast: {e}")
    FEATURE_STORE = None


class PredictionRequest(BaseModel):
    usager_id: str


def write_shadow_log_async(X_dict, usager_id, predicted_class, db_url):
    import logging
    import os

    import pandas as pd
    from sqlalchemy import create_engine

    logger = logging.getLogger("api")
    try:
        engine = create_engine(db_url)
        # Reconstruct single row dataframe
        log_entry = pd.DataFrame([X_dict])
        log_entry["usager_id"] = usager_id
        log_entry["predicted_gravity"] = predicted_class
        log_entry["event_timestamp"] = pd.to_datetime("now")

        # Écriture native dans PostgreSQL
        log_entry.to_sql(
            "production_shadow_log", engine, if_exists="append", index=False
        )
        logger.info(f"✅ Shadow log asynchrone enregistré pour {usager_id}")

    except Exception as db_e:
        logger.error(f"❌ Échec de l'écriture asynchrone du shadow log : {db_e}")
        # Fallback
        log_dir = "data/production_logs"
        os.makedirs(log_dir, exist_ok=True)
        log_file = os.path.join(log_dir, "shadow_log_fallback.csv")
        try:
            log_entry.to_csv(
                log_file, mode="a", header=not os.path.exists(log_file), index=False
            )
        except Exception as disk_e:
            logger.critical(f"❌ Échec fatal du fallback CSV : {disk_e}")


@app.on_event("startup")
async def startup_event():
    logger.info("Démarrage de l'API avec Inférence temps réel.")


@app.get("/")
def read_root():
    return {"message": "API de Serving MLOps - En ligne (100% Real Feast Mode)"}


@app.get("/predict/{famille}/{usager_id}")
def predict_gravity(famille: str, usager_id: str, background_tasks: BackgroundTasks):
    """
    Prédiction de gravité pour un usager donné via Redis et MLflow.
    """
    famille = famille.upper()

    if famille != "A":
        raise HTTPException(
            status_code=400,
            detail="Seule la Famille A est migrée en mode Réel pour l'instant.",
        )

    if FEATURE_STORE is None:
        raise HTTPException(status_code=500, detail="Feature Store non initialisé.")

    # -----------------------------------------------------
    # FEAST : Récupération des features en temps réel (O(1)) via Redis
    # -----------------------------------------------------
    logger.info(f"Interrogation de Feast (Redis) pour l'usager: {usager_id}")
    try:
        # On définit les features qu'on souhaite récupérer de l'Online Store
        features_to_fetch = [
            "usagers_features:place",
            "usagers_features:catu",
            "usagers_features:sexe",
            "usagers_features:an_nais",
            "usagers_features:trajet",
            "usagers_features:is_metropole",
            "usagers_features:age_bucket",
            "usagers_features:is_motorise",
            "usagers_features:lum_calculee",
            "usagers_features:atm_simplifie",
            "usagers_features:catr_derive",
            "usagers_features:nb_accidents_zone",
            "usagers_features:taux_gravite_zone",
            "usagers_features:risque_relatif_catr",
        ]

        feature_vector = FEATURE_STORE.get_online_features(
            features=features_to_fetch, entity_rows=[{"usager_id": usager_id}]
        ).to_dict()

        # Transformation en DataFrame pour l'inférence Sklearn
        online_features = pd.DataFrame(feature_vector)

        # On retire la clé d'entité pour l'inférence
        if "usager_id" in online_features.columns:
            online_features = online_features.drop(columns=["usager_id"])

        # Clean prefix "usagers_features__" that might be added by Feast
        online_features.columns = [
            col.replace("usagers_features__", "")
            if "usagers_features__" in col
            else col
            for col in online_features.columns
        ]

        # Ensure we have data
        if online_features.iloc[0].isnull().all():
            logger.warning(
                f"Aucune feature trouvée dans Redis pour l'usager {usager_id}. Avez-vous exécuté 'feast materialize' ?"
            )
            raise HTTPException(
                status_code=404,
                detail="Usager introuvable dans le Feature Store (Redis).",
            )

    except Exception as e:
        logger.error(f"Echec Feast : {e}")
        raise HTTPException(
            status_code=500, detail=f"Erreur d'accès au Feature Store: {e!s}"
        )

    # -----------------------------------------------------
    # API GATEWAY : Envoi vers le conteneur MLflow Serve
    # -----------------------------------------------------
    logger.info(f"Appel de l'API MLflow Serve pour la famille {famille}...")
    try:
        # Ré-aligner l'ordre des colonnes
        expected_features = [
            "place",
            "catu",
            "sexe",
            "an_nais",
            "trajet",
            "is_metropole",
            "age_bucket",
            "is_motorise",
            "lum_calculee",
            "atm_simplifie",
            "catr_derive",
            "nb_accidents_zone",
            "taux_gravite_zone",
            "risque_relatif_catr",
        ]
        missing = [f for f in expected_features if f not in online_features.columns]
        if missing:
            logger.warning(f"Colonnes manquantes dans Feast: {missing}")
            for m in missing:
                online_features[m] = 0  # Fallback

        X = online_features[expected_features]

        import requests

        payload = {
            "dataframe_split": {
                "columns": X.columns.tolist(),
                "data": X.values.tolist(),
            }
        }

        response = requests.post(MLFLOW_SERVE_URL, json=payload, timeout=3.0)  # P1: Added explicit timeout

        if response.status_code != 200:
            raise Exception(
                f"Erreur MLflow Serve ({response.status_code}): {response.text}"
            )

        prediction = response.json().get("predictions", [0])
        predicted_class = int(prediction[0])

        # [ALERTE MLOPS] Shadow Logging Asynchrone : Découplé du chemin critique !
        DB_URL = os.environ.get("DATABASE_URL", "postgresql://mlops:${POSTGRES_PASSWORD}@db:5432/mlops_db")
        if os.environ.get("ENV") == "test" or not os.environ.get("FEAST_REDIS_HOST"):
            DB_URL = os.environ.get("DATABASE_URL_LOCAL", "postgresql://mlops:mock@localhost:5432/mlops_db")

        background_tasks.add_task(
            write_shadow_log_async,
            X.iloc[0].to_dict(),
            usager_id,
            predicted_class,
            DB_URL,
        )

        return {
            "usager_id": usager_id,
            "predicted_gravity": predicted_class,
            "model_version": "latest",
            "source": "Redis Online Store",
            "status": "success",
        }
    except Exception as e:
        logger.error(f"Echec Inférence : {e}")
        raise HTTPException(
            status_code=500, detail=f"Erreur lors de l'inférence: {e!s}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
