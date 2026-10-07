from datetime import timedelta
from feast import Entity, FeatureView, Field
from feast.infra.offline_stores.contrib.postgres_offline_store.postgres_source import (
    PostgreSQLSource,
)
from feast.types import Int64, String, Bool, Float64

# Entité Principale (L'usager accidenté) avec clé composite
usager = Entity(name="usager", join_keys=["usager_id"])

# Source de données PostgreSQL (Table contenant les features calculées)
usagers_source = PostgreSQLSource(
    name="usagers_harmonized_source",
    query="SELECT * FROM feature_matrix",
    timestamp_field="event_timestamp",
)

# Feature View
usagers_fv = FeatureView(
    name="usagers_features",
    entities=[usager],
    ttl=timedelta(days=3650),
    schema=[
        # Variables de base
        Field(name="place", dtype=Int64),
        Field(name="catu", dtype=Int64),
        Field(name="grav", dtype=Int64),
        Field(name="sexe", dtype=Int64),
        Field(name="an_nais", dtype=Int64),
        Field(name="trajet", dtype=Int64),
        # Variables calculées (Feature Engineering)
        Field(name="is_metropole", dtype=Bool),
        Field(name="age_bucket", dtype=String),
        Field(name="is_motorise", dtype=Bool),
        Field(name="lum_calculee", dtype=String),
        Field(name="atm_simplifie", dtype=String),
        Field(name="catr_derive", dtype=String),
        Field(name="nb_accidents_zone", dtype=Int64),
        Field(name="taux_gravite_zone", dtype=Float64),
        Field(name="risque_relatif_catr", dtype=Float64),
    ],
    online=True,
    source=usagers_source,
    tags={"domain": "car_acc"},
)
