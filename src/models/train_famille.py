import logging
import os
import random
from datetime import datetime
import numpy as np

# [ALERTE MLOPS] P1: Fixation totale des seeds
SEED = 42
np.random.seed(SEED)
random.seed(SEED)
os.environ['PYTHONHASHSEED'] = str(SEED)

import mlflow
import mlflow.pyfunc
import mlflow.sklearn
import numpy as np
import pandas as pd
import psycopg2
import requests
from feast import FeatureStore
from mlflow.tracking import MlflowClient
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    mean_absolute_error,
    mean_absolute_percentage_error,
    mean_squared_error,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder

# Configure logger
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


class WeatherHybridModel(mlflow.pyfunc.PythonModel):
    """Famille C: Pipeline hybride (API Open-Meteo -> Modèle Famille A)"""

    def __init__(self, model_a_uri):
        self.model_a_uri = model_a_uri
        self.model_a = None

    def load_context(self, context):
        self.model_a = mlflow.pyfunc.load_model(self.model_a_uri)

    def predict(self, context, model_input):
        import pandas as pd

        df = model_input.copy()

        # Mapping des codes WMO (Open-Meteo) vers la nomenclature BAAC (atm_simplifie)
        # 0-3: Ciel dégagé à nuageux -> Normal
        # >3: Pluie, Neige, Brouillard -> Intemperies
        def map_wmo_to_baac(wmo_code):
            if pd.isna(wmo_code):
                return "Autre"
            if wmo_code <= 3:
                return "Normal"
            return "Intemperies"

        # Si l'API Gateway nous fournit les coordonnées temporelles et spatiales de l'accident
        if all(col in df.columns for col in ["lat", "long", "event_timestamp"]):
            atm_list = []
            for _, row in df.iterrows():
                try:
                    lat = float(row["lat"])
                    lon = float(row["long"])
                    date_str = str(row["event_timestamp"])[:10]  # Format YYYY-MM-DD

                    # Appel HTTP temps réel vers l'API Open-Meteo (Archive)
                    url = f"https://archive-api.open-meteo.com/v1/archive?latitude={lat}&longitude={lon}&start_date={date_str}&end_date={date_str}&daily=weather_code&timezone=Europe%2FParis"
                    res = requests.get(url, timeout=3)

                    if res.status_code == 200:
                        data = res.json()
                        wmo = data.get("daily", {}).get("weather_code", [None])[0]
                        atm_list.append(map_wmo_to_baac(wmo))
                    else:
                        atm_list.append("Autre")
                except Exception as e:
                    logger.error(f"Erreur API Open-Meteo: {e}")
                    atm_list.append("Autre")

            # Remplacement de la feature mockée par la vraie donnée météo
            df["atm_simplifie"] = atm_list
            # Nettoyage avant de passer au modèle sklearn
            df = df.drop(columns=["lat", "long", "event_timestamp"])

        elif "meteo_externe" in df.columns:
            # Fallback legacy si le payload utilise l'ancienne nomenclature
            mapping = {
                "pluie_forte": "Intemperies",
                "neige": "Intemperies",
                "brouillard": "Intemperies",
                "soleil": "Normal",
            }
            df["atm_simplifie"] = df["meteo_externe"].map(mapping).fillna("Autre")
            df = df.drop(columns=["meteo_externe"])

        return self.model_a.predict(df)


class ModelFactory:
    """Usine d'entraînement générique MLOps pour les familles A, B, et C."""

    FAMILY_CONFIGS = {
        "A": {
            "name": "baac-gravity-classifier",
            "registry_name": "BAAC_Model_Famille_A",
            "type": "classification",
            "target": "is_grave",
            "features_t0": [
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
            ],
            "hyperparams": {
                "n_estimators": 150,
                "max_depth": 12,
                "min_samples_split": 5,
                "class_weight": "balanced",
                "random_state": 42,
            },
        },
        "B": {
            "name": "baac-temporal-forecast",
            "registry_name": "BAAC_Model_Famille_B",
            "type": "regression",
            "target": "nb_accidents",
            "features_t0": ["jour_semaine", "is_ferie", "is_vacances_scolaires"],
            "hyperparams": {"n_estimators": 100, "max_depth": 8, "random_state": 42},
        },
        "C": {
            "name": "baac-weather-hybrid",
            "registry_name": "BAAC_Model_Famille_C",
            "type": "hybrid_pipeline",
        },
    }

    def __init__(self, famille: str, tracking_uri: str = "http://localhost:5001"):
        self.famille = famille.upper()
        self.config = self.FAMILY_CONFIGS.get(self.famille, self.FAMILY_CONFIGS["A"])

        mlflow.set_tracking_uri(tracking_uri)
        mlflow.set_experiment(f"BAAC_Famille_{self.famille}")

        # Initialisation du Feature Store
        repo_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
            "feature_repo",
            "feature_repo",
        )
        self.store = FeatureStore(repo_path=repo_path)

    def train(self) -> str:
        """Train the model family using Feast Historical Features and register in MLflow."""
        if self.famille == "A":
            df = self._get_historical_features()
            return self._train_classifier(df)
        elif self.famille == "B":
            df = self._get_historical_features()
            return self._train_regressor(df)
        elif self.famille == "C":
            return self._register_hybrid_pipeline()
        else:
            raise ValueError(f"Famille {self.famille} inconnue.")

    def _get_historical_features(self) -> pd.DataFrame:
        logger.info("Connexion à PostgreSQL pour récupérer l'Entity DataFrame...")
        conn = psycopg2.connect(
            host="localhost",
            database="mlops_db",
            user="mlops",
            password="mlops_password",
        )

        query = "SELECT * FROM feature_matrix WHERE event_timestamp IS NOT NULL"
        df = pd.read_sql(query, conn)
        conn.close()

        df["event_timestamp"] = pd.to_datetime(df["event_timestamp"], utc=True)
        logger.info(f"Features brutes chargées : {len(df)} lignes.")
        return df

    def _train_classifier(self, df_train: pd.DataFrame) -> str:
        available_features = [
            f for f in self.config["features_t0"] if f in df_train.columns
        ]
        target = self.config["target"]

        # [ALERTE MLOPS] On intègre 'event_timestamp' pour permettre le découpage temporel
        cols_to_keep = available_features + [target]
        if "event_timestamp" in df_train.columns:
            cols_to_keep.append("event_timestamp")

        df_clean = df_train[cols_to_keep].dropna()

        if "event_timestamp" in df_clean.columns:
            # [ALERTE MLOPS] Remplacement du split aléatoire par un Split Temporel
            split_date = pd.to_datetime("2023-01-01", utc=True)
            train_mask = df_clean["event_timestamp"] < split_date
            test_mask = df_clean["event_timestamp"] >= split_date

            X_train = df_clean[train_mask][available_features]
            y_train = df_clean[train_mask][target].astype(int)
            X_test = df_clean[test_mask][available_features]
            y_test = df_clean[test_mask][target].astype(int)
            logger.info(f"Split Temporel: Train={len(X_train)}, Test={len(X_test)}")
        else:
            X = df_clean[available_features]
            y = df_clean[target].astype(int)
            # [ALERTE MLOPS] P0: Remplacement du split aléatoire par une Validation Temporelle !
            # Si 'an' est présent, on utilise les années passées pour l'entraînement et 2023+ pour le test
            if "an" in df_clean.columns:
                train_mask = df_clean["an"] < 2023
                test_mask = df_clean["an"] >= 2023
                X_train, X_test = X[train_mask], X[test_mask]
                y_train, y_test = y[train_mask], y[test_mask]
                logger.info(f"Split Temporel: Train={len(X_train)} (avant 2023), Test={len(X_test)} (2023+)")
            else:
                # Fallback sécurisé en cas d'absence temporelle
                # Attention, ce chemin ne devrait plus être emprunté en prod !
                X_train, X_test, y_train, y_test = train_test_split(
                    X, y, test_size=0.2, random_state=42, stratify=y
                )

        cat_cols = X_train.select_dtypes(
            include=["object", "category", "bool"]
        ).columns.tolist()
        num_cols = X_train.select_dtypes(
            exclude=["object", "category", "bool"]
        ).columns.tolist()

        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "cat",
                    OrdinalEncoder(
                        handle_unknown="use_encoded_value", unknown_value=-1
                    ),
                    cat_cols,
                ),
                ("num", "passthrough", num_cols),
            ]
        )

        with mlflow.start_run(
            run_name=f"FamilleA_{datetime.now().strftime('%Y%m%d_%H%M')}"
        ) as run:
            hp = self.config["hyperparams"]
            mlflow.log_params(hp)

            clf = RandomForestClassifier(**hp)
            model = Pipeline(
                steps=[("preprocessor", preprocessor), ("classifier", clf)]
            )

            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)
            y_proba = model.predict_proba(X_test)

            metrics = {
                "accuracy": accuracy_score(y_test, y_pred),
                "f1_weighted": f1_score(y_test, y_pred, average="weighted"),
                "precision": precision_score(
                    y_test, y_pred, average="weighted", zero_division=0
                ),
                "recall_grave": recall_score(
                    y_test, y_pred, pos_label=1, zero_division=0
                ),
            }
            if len(np.unique(y_test)) == 2 and y_proba.shape[1] == 2:
                metrics["auc_roc"] = roc_auc_score(y_test, y_proba[:, 1])

            mlflow.log_metrics(metrics)

            # [ALERTE MLOPS] Model Evaluation Gate : Champion vs Challenger
            model_info = mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="model",
                serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_PICKLE,
            )
            
            # Enregistrement "brouillon"
            reg_model_name = self.config["registry_name"]
            new_version = mlflow.register_model(model_info.model_uri, reg_model_name)
            
            # Évaluation automatique
            client = MlflowClient()
            try:
                champion_version = client.get_model_version_by_alias(reg_model_name, "Champion")
                champion_run = client.get_run(champion_version.run_id)
                champion_score = champion_run.data.metrics.get("f1_weighted", 0.0)
            except Exception:
                # Aucun champion existant (premier run)
                champion_score = -1.0
                
            challenger_score = metrics["f1_weighted"]
            
            if challenger_score > champion_score:
                logger.info(f"🏆 Promotion: Challenger (F1={challenger_score:.4f}) bat le Champion (F1={champion_score:.4f})")
                client.set_registered_model_alias(reg_model_name, "Champion", new_version.version)
            else:
                logger.warning(f"❌ Rejet: Challenger (F1={challenger_score:.4f}) n'a pas battu le Champion (F1={champion_score:.4f})")
                client.set_registered_model_alias(reg_model_name, "Challenger_Rejected", new_version.version)

            logger.info(f"Family A trained. Metrics: {metrics}")
            return run.info.run_id

    def _train_regressor(self, df_raw: pd.DataFrame) -> str:
        # Agrégation temporelle pour la Famille B
        df_raw["date"] = df_raw["event_timestamp"].dt.date
        df_raw["is_ferie"] = df_raw["is_ferie"].fillna(False).astype(bool)
        df_raw["is_vacances_scolaires"] = (
            df_raw["is_vacances_scolaires"].fillna(False).astype(bool)
        )

        df_agg = (
            df_raw.groupby("date")
            .agg(
                nb_accidents=("num_acc", "nunique"),
                jour_semaine=("jour_semaine", "first"),
                is_ferie=("is_ferie", "first"),
                is_vacances_scolaires=("is_vacances_scolaires", "first"),
            )
            .reset_index()
        )

        available_features = self.config["features_t0"]
        target = self.config["target"]

        X = df_agg[available_features]
        y = df_agg[target]

        # Chronological split for time series
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]

        cat_cols = X_train.select_dtypes(
            include=["object", "category", "bool"]
        ).columns.tolist()
        num_cols = X_train.select_dtypes(
            exclude=["object", "category", "bool"]
        ).columns.tolist()

        preprocessor = ColumnTransformer(
            transformers=[
                (
                    "cat",
                    OrdinalEncoder(
                        handle_unknown="use_encoded_value", unknown_value=-1
                    ),
                    cat_cols,
                ),
                ("num", "passthrough", num_cols),
            ]
        )

        with mlflow.start_run(
            run_name=f"FamilleB_{datetime.now().strftime('%Y%m%d_%H%M')}"
        ) as run:
            hp = self.config["hyperparams"]
            mlflow.log_params(hp)

            reg = RandomForestRegressor(**hp)
            model = Pipeline(steps=[("preprocessor", preprocessor), ("regressor", reg)])

            model.fit(X_train, y_train)

            y_pred = model.predict(X_test)

            metrics = {
                "mae": mean_absolute_error(y_test, y_pred),
                "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),
                "mape": mean_absolute_percentage_error(y_test, y_pred),
            }

            mlflow.log_metrics(metrics)

            # [ALERTE MLOPS] Model Evaluation Gate : Champion vs Challenger
            model_info = mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="model",
                serialization_format=mlflow.sklearn.SERIALIZATION_FORMAT_PICKLE,
            )
            
            # Enregistrement "brouillon"
            reg_model_name = self.config["registry_name"]
            new_version = mlflow.register_model(model_info.model_uri, reg_model_name)
            
            # Évaluation automatique
            client = MlflowClient()
            try:
                champion_version = client.get_model_version_by_alias(reg_model_name, "Champion")
                champion_run = client.get_run(champion_version.run_id)
                champion_score = champion_run.data.metrics.get("f1_weighted", 0.0)
            except Exception:
                # Aucun champion existant (premier run)
                champion_score = -1.0
                
            challenger_score = metrics["f1_weighted"]
            
            if challenger_score > champion_score:
                logger.info(f"🏆 Promotion: Challenger (F1={challenger_score:.4f}) bat le Champion (F1={champion_score:.4f})")
                client.set_registered_model_alias(reg_model_name, "Champion", new_version.version)
            else:
                logger.warning(f"❌ Rejet: Challenger (F1={challenger_score:.4f}) n'a pas battu le Champion (F1={champion_score:.4f})")
                client.set_registered_model_alias(reg_model_name, "Challenger_Rejected", new_version.version)

            logger.info(f"Family B trained. Metrics: {metrics}")
            return run.info.run_id

    def _register_hybrid_pipeline(self) -> str:
        # Famille C dépend de Famille A. On récupère la dernière version de Famille A.
        client = mlflow.tracking.MlflowClient()
        try:
            model_a_info = client.get_latest_versions(
                "BAAC_Model_Famille_A", stages=["None"]
            )[0]
            model_a_uri = f"models:/BAAC_Model_Famille_A/{model_a_info.version}"
        except Exception as e:
            logger.error("Modèle Famille A introuvable. Entraînez Famille A d'abord.")
            raise e

        with mlflow.start_run(
            run_name=f"FamilleC_{datetime.now().strftime('%Y%m%d_%H%M')}"
        ) as run:
            mlflow.log_param("hybrid_type", "weather_mapper")
            mlflow.log_param("dependency", "BAAC_Model_Famille_A")

            # On log le modèle PyFunc custom
            mlflow.pyfunc.log_model(
                artifact_path="hybrid_model",
                python_model=WeatherHybridModel(model_a_uri=model_a_uri),
                registered_model_name=self.config["registry_name"],
            )
            logger.info("Family C (Hybrid Pipeline) registered successfully.")
            return run.info.run_id


def train_all_families():
    results = {}
    for famille in ["A", "B", "C"]:
        logger.info(f"\\n{'='*60}")
        logger.info(f"Training Family {famille}...")
        logger.info(f"{'='*60}")
        try:
            factory = ModelFactory(famille=famille)
            run_id = factory.train()
            results[famille] = {"status": "success", "run_id": run_id}
            logger.info(f"Family {famille} ✅ run_id={run_id}")
        except Exception as e:
            results[famille] = {"status": "error", "error": str(e)}
            logger.error(f"Family {famille} ❌ {e}")
    return results


if __name__ == "__main__":
    results = train_all_families()
    print("\\n=== Training Results ===")
    for fam, res in results.items():
        print(f"  Family {fam}: {res}")
