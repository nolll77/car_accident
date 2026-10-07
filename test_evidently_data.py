import pandas as pd
from evidently.legacy.metric_preset import DataDriftPreset
from evidently.legacy.report import Report

ref = pd.read_parquet("data/features/feature_matrix.parquet")
prod = pd.read_csv("data/production_logs/shadow_log.csv")

common = [
    f
    for f in [
        "place",
        "catu",
        "sexe",
        "an_nais",
        "trajet",
        "nb_accidents_zone",
        "is_metropole",
        "age_bucket",
        "is_motorise",
        "lum_calculee",
        "atm_simplifie",
        "catr_derive",
    ]
    if f in ref.columns and f in prod.columns
]
print("Common:", common)
ref_common = ref[common].copy()
prod_common = prod[common].copy()

# Cast both to float
for c in common:
    ref_common[c] = ref_common[c].astype(float)
    prod_common[c] = prod_common[c].astype(float)

report = Report(metrics=[DataDriftPreset()])
report.run(reference_data=ref_common, current_data=prod_common)
print("Success!")
