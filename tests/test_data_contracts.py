"""
Tests automatisés des contrats de données Pandera (MLOps CI/CD).
Vérifie que la corruption de la donnée est bien bloquée.
"""

import pytest
import pandas as pd
import pandera as pa
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from src.data.contracts import BAACUsagerSchema


def test_valid_usager_data():
    """Test qu'un dataframe valide passe le contrat."""
    df = pd.DataFrame(
        {
            "usager_id": ["123_456"],
            "Num_Acc": [123456789],
            "id_vehicule": ["A01"],
            "num_veh": ["1"],
            "place": [1],
            "catu": [1],
            "grav": [3],
            "sexe": [1],
            "an_nais": [1985],
            "trajet": [1],
        }
    )

    # Doit passer sans exception
    validated_df = BAACUsagerSchema.validate(df)
    assert not validated_df.empty


def test_invalid_usager_data_age():
    """Test qu'un âge aberrant (hors bornes) échoue."""
    df = pd.DataFrame(
        {
            "usager_id": ["123_456"],
            "Num_Acc": [123456789],
            "id_vehicule": ["A01"],
            "num_veh": ["1"],
            "place": [1],
            "catu": [1],
            "grav": [3],
            "sexe": [1],
            "an_nais": [1850],  # Erreur ici (Trop vieux)
            "trajet": [1],
        }
    )

    with pytest.raises(pa.errors.SchemaError):
        BAACUsagerSchema.validate(df)


def test_invalid_usager_data_grav():
    """Test qu'une gravité non répertoriée échoue (ex: 5)."""
    df = pd.DataFrame(
        {
            "usager_id": ["123_456"],
            "Num_Acc": [123456789],
            "id_vehicule": ["A01"],
            "num_veh": ["1"],
            "place": [1],
            "catu": [1],
            "grav": [5],  # Erreur ici (Seulement -1, 1, 2, 3, 4 autorisés)
            "sexe": [1],
            "an_nais": [1985],
            "trajet": [1],
        }
    )

    with pytest.raises(pa.errors.SchemaError):
        BAACUsagerSchema.validate(df)
