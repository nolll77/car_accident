"""
Tests d'intégration de l'API de Serving (MLOps CI/CD).
"""

import os
import sys
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from app.main import app  # noqa: E402

client = TestClient(app)


def test_api_health_docs():
    """Test que l'API est debout et expose la doc."""
    response = client.get("/docs")
    assert response.status_code == 200


def test_predict_endpoint_mocked():
    """
    Test du endpoint de prédiction avec mock du Feature Store (Redis)
    et du MLflow Serve pour simuler le comportement en CI.
    """
    # 1. Mock de la réponse de l'API MLflow Serve
    with patch("requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"predictions": [1]}

        # 2. Mock du Feature Store
        with patch("app.main.FEATURE_STORE") as mock_fs:
            mock_fs.get_online_features.return_value.to_dict.return_value = {
                "usagers_features:place": [1],
                "usagers_features:catu": [1],
                "usagers_features:sexe": [1],
                "usagers_features:an_nais": [1980],
                "usagers_features:trajet": [1],
                "usagers_features:is_metropole": [True],
                "usagers_features:age_bucket": ["36-50"],
                "usagers_features:is_motorise": [True],
                "usagers_features:lum_calculee": ["Jour"],
                "usagers_features:atm_simplifie": ["Normal"],
                "usagers_features:catr_derive": ["Departementale"],
                "usagers_features:nb_accidents_zone": [150],
                "usagers_features:taux_gravite_zone": [0.15],
                "usagers_features:risque_relatif_catr": [0.12],
            }

            # 3. Empêcher l'écriture Postgres pendant le test
            with patch("pandas.DataFrame.to_sql") as _mock_to_sql:
                response = client.get("/predict/A/test_123_456")

                assert response.status_code == 200
                data = response.json()
                assert data["status"] == "success"
                assert data["usager_id"] == "test_123_456"
                assert data["predicted_gravity"] == 1
                assert data["source"] == "Redis Online Store"
