import pytest
import pandas as pd
import pandera as pa
from src.data.contracts import raw_caracteristiques_schema

def test_raw_schema_is_permissive():
    """Vérifie que le contrat Raw accepte les colonnes inattendues (strict=False)"""
    assert not raw_caracteristiques_schema.strict
    
    df = pd.DataFrame({
        "num_acc": [202300000001],
        "jour": [1],
        "mois": [1],
        "an": [2023],
        "lum": [1],
        "dep": ["75"],
        "com": ["75056"],
        "agg": [2],
        "int": [1],
        "atm": [1],
        "col": [1],
        "lat": [48.8],
        "long": [2.3],
        "colonne_surprise": ["test"] # Doit passer car strict=False
    })
    
    # Validation
    validated_df = raw_caracteristiques_schema.validate(df)
    assert "colonne_surprise" in validated_df.columns

def test_raw_schema_types():
    """Vérifie que le contrat enforce les types requis"""
    df = pd.DataFrame({
        "num_acc": ["not_an_int"], # Erreur de type
        "jour": [1],
        "mois": [1],
        "an": [2023],
        "lum": [1],
        "dep": ["75"],
        "com": ["75056"],
        "agg": [2],
        "int": [1],
        "atm": [1],
        "col": [1],
        "lat": [48.8],
        "long": [2.3]
    })
    
    with pytest.raises(pa.errors.SchemaError):
        raw_caracteristiques_schema.validate(df)
