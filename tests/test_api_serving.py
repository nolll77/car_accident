import os
import sys
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app, write_shadow_log_async

client = TestClient(app)


@patch("requests.post")
@patch("app.main.FEATURE_STORE")
@patch("fastapi.BackgroundTasks.add_task")
def test_predict_endpoint_decoupling(
    mock_add_task, mock_feature_store, mock_requests_post
):
    # Setup mock Feast online features
    mock_features_result = MagicMock()
    mock_features_result.to_dict.return_value = {
        "usager_id": ["12345"],
        "place": [1],
        "catu": [1],
        "sexe": [1],
        "an_nais": [1980],
        "trajet": [5],
        "is_metropole": [1],
        "age_bucket": [3],
        "is_motorise": [1],
        "lum_calculee": [1],
        "atm_simplifie": [1],
        "catr_derive": [3],
        "nb_accidents_zone": [10],
        "taux_gravite_zone": [0.2],
        "risque_relatif_catr": [1.1],
    }
    mock_feature_store.get_online_features.return_value = mock_features_result

    # Setup mock MLflow Serve response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"predictions": [1]}
    mock_requests_post.return_value = mock_response

    # Call endpoint
    response = client.get("/predict/A/12345")

    assert response.status_code == 200
    assert response.json()["usager_id"] == "12345"
    assert response.json()["predicted_gravity"] == 1

    # Verify shadow logging was decoupled into BackgroundTasks
    mock_add_task.assert_called_once()
    args, kwargs = mock_add_task.call_args
    assert args[0] == write_shadow_log_async
