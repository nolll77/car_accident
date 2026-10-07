from sqlalchemy import create_engine
import pandas as pd

engine = create_engine("postgresql://mlops:mlops_password@localhost:5432/mlops_db")
df = pd.read_sql(
    "SELECT table_name FROM information_schema.tables WHERE table_schema='public'",
    engine,
)
print(df[df["table_name"].str.contains("dim|fct|feature|usager|acc|carac")])
