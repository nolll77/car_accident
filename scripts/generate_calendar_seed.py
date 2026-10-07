import pandas as pd
import numpy as np

dates = pd.date_range(start="2015-01-01", end="2026-12-31")
df = pd.DataFrame({"date": dates})

df["jour_semaine"] = df["date"].dt.dayofweek  # 0=Lundi, 6=Dimanche
df["is_ferie"] = np.where(
    df["jour_semaine"] == 6, True, False
)  # Fake: Sunday is ferie, plus random days
# Add some random feries
np.random.seed(42)
df.loc[np.random.choice(df.index, size=100, replace=False), "is_ferie"] = True

df["is_vacances_scolaires"] = False
# Fake: July and August are holidays
df.loc[df["date"].dt.month.isin([7, 8]), "is_vacances_scolaires"] = True

df.to_csv("dbt_warehouse/seeds/seed_calendrier.csv", index=False)
print("seed_calendrier.csv created successfully.")
