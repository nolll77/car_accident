"""
Training ML Pipeline BAAC (Famille A) - MLOps Phase 3
Entraînement reproductible, tracking MLflow, et versioning de modèle.
"""

import pandas as pd
import logging
import mlflow
import mlflow.sklearn
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score, accuracy_score
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BAACTrainingFamilleA")


class ModelTrainerFamilleA:
    """
    Entraînement du modèle de prédiction de gravité (Famille A).
    Gère l'intégration avec MLflow pour la traçabilité complète.
    """

    def __init__(self, experiment_name: str = "BAAC_Famille_A_Gravity"):
        self.experiment_name = experiment_name
        mlflow.set_tracking_uri("sqlite:///mlflow.db")
        mlflow.set_experiment(self.experiment_name)

    def train_and_log(self, df: pd.DataFrame):
        """
        Entraîne le RandomForest et logge les résultats dans MLflow.
        """
        logger.info("Préparation des données pour l'entraînement...")

        # Simulation simplifiée des features Feast pour l'entraînement
        # Dans un vrai cas, on ferait un `feast.get_historical_features()`
        features = ["place", "catu", "sexe", "an_nais", "is_metropole", "is_motorise"]
        target = "grav"

        # Filtre sur les colonnes nécessaires (gestion propre des NaNs)
        df_train = df[features + [target]].dropna()

        # Encodage simpliste (One-Hot) pour les variables catégorielles (ex: bools)
        X = pd.get_dummies(df_train[features], drop_first=True)
        y = df_train[target]

        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42
        )

        logger.info("Démarrage du run MLflow...")
        with mlflow.start_run(
            run_name=f"RF_Famille_A_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        ) as run:
            # Paramètres du modèle
            n_estimators = 100
            max_depth = 10

            mlflow.log_param("n_estimators", n_estimators)
            mlflow.log_param("max_depth", max_depth)
            mlflow.log_param("features", features)

            # Entraînement
            logger.info("Entraînement du RandomForestClassifier...")
            model = RandomForestClassifier(
                n_estimators=n_estimators,
                max_depth=max_depth,
                random_state=42,
                class_weight="balanced",
            )
            model.fit(X_train, y_train)

            # Prédictions et Métriques
            y_pred = model.predict(X_test)
            f1 = f1_score(y_test, y_pred, average="weighted")
            acc = accuracy_score(y_test, y_pred)

            logger.info(f"Métriques - F1 Score: {f1:.4f} | Accuracy: {acc:.4f}")

            mlflow.log_metric("f1_score", f1)
            mlflow.log_metric("accuracy", acc)

            # Log du modèle
            mlflow.sklearn.log_model(
                sk_model=model,
                artifact_path="model",
                registered_model_name="BAAC_Braking_Controller_Famille_A",
            )

            logger.info(
                f"Run MLflow terminé. Modèle versionné avec succès (Run ID: {run.info.run_id})."
            )
            return run.info.run_id


def run_sample_training():
    """
    Script de test et de démonstration de l'entraînement MLOps Famille A.
    """
    # Création d'un dataset synthétique
    data = {
        "place": [1, 2, 1, 3, 1, 2, 1, 1, 4, 1] * 10,
        "catu": [1, 2, 1, 2, 1, 2, 3, 1, 2, 1] * 10,
        "sexe": [1, 2, 1, 1, 2, 2, 1, 1, 2, 1] * 10,
        "an_nais": [1985, 1990, 1972, 2000, 1965, 1988, 1950, 1995, 2010, 1982] * 10,
        "is_metropole": [True, True, False, True, True, False, True, True, True, False]
        * 10,
        "is_motorise": [True, True, True, True, True, True, False, True, True, True]
        * 10,
        "grav": [1, 4, 3, 1, 2, 4, 3, 1, 1, 4]
        * 10,  # 1: Indemne, 2: Tué, 3: Blessé hosp., 4: Blessé léger
    }
    df = pd.DataFrame(data)

    trainer = ModelTrainerFamilleA()
    trainer.train_and_log(df)


if __name__ == "__main__":
    run_sample_training()
