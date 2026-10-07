import requests
from sqlalchemy import create_engine
import pandas as pd

payload = {"usager_id": "202300000001_155Â 680Â 557_A01_0"}
try:
    res = requests.get(f"http://localhost:8000/predict/A/{payload['usager_id']}")
    print(f"API HTTP Status: {res.status_code}")
    print(f"API Response: {res.json()}")
except Exception as e:
    print(f"API Error: {e}")

engine = create_engine("postgresql://mlops:mlops_password@localhost:5432/mlops_db")
try:
    df = pd.read_sql("SELECT * FROM production_shadow_log", engine)
    print(f"✅ Lignes dans Postgres shadow log : {len(df)}")
except Exception as e:
    print(f"❌ Erreur DB: {e}")
