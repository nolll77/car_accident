import pandera as pa
from pandera.typing import Series
import pandas as pd


class BAACCaracteristiquesSchema(pa.DataFrameModel):
    Num_Acc: Series[str] = pa.Field(nullable=False, unique=True)
    an: Series[int] = pa.Field(ge=2005, le=2026)
    mois: Series[int] = pa.Field(ge=1, le=12)
    jour: Series[int] = pa.Field(ge=1, le=31)
    lum: Series[int] = pa.Field(isin=[1, 2, 3, 4, 5])
    dep: Series[str] = pa.Field(nullable=False)
    lat: Series[float] = pa.Field(ge=-90.0, le=90.0, nullable=True)
    long: Series[float] = pa.Field(ge=-180.0, le=180.0, nullable=True)

    class Config:
        strict = False
        coerce = True


class BAACLieuxSchema(pa.DataFrameModel):
    Num_Acc: Series[str] = pa.Field(nullable=False)
    catr: Series[int] = pa.Field(nullable=True)
    surf: Series[int] = pa.Field(nullable=True)

    class Config:
        strict = False
        coerce = True


class BAACVehiculesSchema(pa.DataFrameModel):
    Num_Acc: Series[str] = pa.Field(nullable=False)
    id_vehicule: Series[str] = pa.Field(nullable=False)
    catv: Series[int] = pa.Field(nullable=True)

    class Config:
        strict = False
        coerce = True


class BAACUsagerSchema(pa.DataFrameModel):
    Num_Acc: Series[str] = pa.Field(nullable=False)
    usager_id: Series[str] = pa.Field(nullable=False, unique=True)
    grav: Series[int] = pa.Field(isin=[1, 2, 3, 4])
    catu: Series[int] = pa.Field(isin=[1, 2, 3])
    sexe: Series[int] = pa.Field(nullable=True)
    an_nais: Series[int] = pa.Field(ge=1900, le=2026, nullable=True)

    class Config:
        strict = False
        coerce = True


def validate_caracteristiques_data(df: pd.DataFrame) -> pd.DataFrame:
    return BAACCaracteristiquesSchema.validate(df)


def validate_lieux_data(df: pd.DataFrame) -> pd.DataFrame:
    return BAACLieuxSchema.validate(df)


def validate_vehicules_data(df: pd.DataFrame) -> pd.DataFrame:
    return BAACVehiculesSchema.validate(df)


def validate_usager_data(df: pd.DataFrame) -> pd.DataFrame:
    return BAACUsagerSchema.validate(df)
