from datetime import datetime, timedelta
from app.domain.remediation.policy_engine import PolicyEngine
from app.domain.observations.models import ModelDegradedEvent

def test_policy_engine_cooldown():
    engine = PolicyEngine(api_url="mock://api")
    
    # Premier event critique : Doit passer
    event1 = ModelDegradedEvent(reason="Drift", drift_score=4.0, observed_at=datetime.utcnow().isoformat())
    assert engine.evaluate(event1) == True
    
    # Deuxième event critique juste après : Doit être bloqué par le cooldown (60s)
    event2 = ModelDegradedEvent(reason="Drift 2", drift_score=5.0, observed_at=datetime.utcnow().isoformat())
    assert engine.evaluate(event2) == False
    
    # Simulation du passage du temps
    engine.last_retrain_time = datetime.utcnow() - timedelta(seconds=65)
    
    # Troisième event : Doit passer car cooldown expiré
    assert engine.evaluate(event2) == True

def test_policy_engine_threshold():
    engine = PolicyEngine(api_url="mock://api")
    # Score faible, ne doit pas déclencher
    event = ModelDegradedEvent(reason="Minor drift", drift_score=1.0, observed_at=datetime.utcnow().isoformat())
    assert engine.evaluate(event) == False
