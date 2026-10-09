from unittest.mock import patch, MagicMock
from src.models.sre_engine import ContinuousTrainingEngine

@patch("src.models.sre_engine.subprocess.run")
@patch("src.models.drift_monitor.DriftMonitor.detect_drift")
def test_sre_engine_triggers_on_drift(mock_detect, mock_subproc):
    engine = ContinuousTrainingEngine(psi_threshold=0.2)
    
    # Simuler un drift critique
    mock_detect.return_value = {"an_nais": 0.25, "sexe": 0.05}
    mock_subproc.return_value = MagicMock(returncode=0)
    
    engine.run_sre_loop()
    
    # Vérifie que subprocess (retrain) a été appelé
    mock_subproc.assert_called_once()
    
@patch("src.models.sre_engine.subprocess.run")
@patch("src.models.drift_monitor.DriftMonitor.detect_drift")
def test_sre_engine_ignores_stable_data(mock_detect, mock_subproc):
    engine = ContinuousTrainingEngine(psi_threshold=0.2)
    
    # Simuler des données stables
    mock_detect.return_value = {"an_nais": 0.15, "sexe": 0.05}
    
    engine.run_sre_loop()
    
    # Vérifie que le réentraînement n'a PAS été déclenché
    mock_subproc.assert_not_called()
