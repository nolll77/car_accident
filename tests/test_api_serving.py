from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Import de l'app (on mocke MLflow et Feast au niveau de l'app pour éviter de les contacter)
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app, write_shadow_log_async

client = TestClient(app)

@patch("app.main.mlflow.pyfunc.load_model")
@patch("app.main.redis.Redis")
@patch("app.main.BackgroundTasks.add_task")
def test_predict_endpoint_decoupling(mock_add_task, mock_redis, mock_load_model):
    # Setup des mocks
    mock_model = MagicMock()
    mock_model.predict.return_value = [1]
    mock_load_model.return_value = mock_model
    
    mock_r = MagicMock()
    mock_r.hgetall.return_value = {
        b"catu": b"1", b"sexe": b"1", b"an_nais": b"1980", b"trajet": b"5",
        b"is_metropole": b"1", b"age_bucket": b"3", b"is_motorise": b"1",
        b"lum_calculee": b"1", b"atm_simplifie": b"1", b"catr_derive": b"3",
        b"nb_accidents_zone": b"10"
    }
    mock_redis.return_value = mock_r
    
    # Appel de l'API
    response = client.get("/predict/A/12345")
    
    assert response.status_code == 200
    assert response.json()["usager_id"] == "12345"
    
    # Vérifie que le shadow logging a bien été déporté en BackgroundTask
    mock_add_task.assert_called_once()
    args, kwargs = mock_add_task.call_args
    assert args[0] == write_shadow_log_async
    
