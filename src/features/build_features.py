import pandas as pd
import numpy as np
import yaml
import logging
from pathlib import Path
from src.features.calendar_utils import is_ferie, is_vacances_scolaires

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureEngineer:
    def __init__(self, harmonized_dir="data/harmonized"):
        self.harmonized_dir = Path(harmonized_dir)
        self._load_dictionaries()

    def _load_dictionaries(self):
        dict_path = Path("config/value_dictionaries.yaml")
        if dict_path.exists():
            with open(dict_path, "r", encoding="utf-8") as f:
                self.value_dictionaries = yaml.safe_load(f)
        else:
            self.value_dictionaries = {}
            logger.warning(
                "No value_dictionaries.yaml found at config/value_dictionaries.yaml"
            )

    def load_harmonized(self) -> dict[str, pd.DataFrame]:
        """Load all 4 harmonized Parquet files, convert columns to lowercase."""
        tables = {}
        for name in ["usagers", "vehicules", "lieux", "caracteristiques"]:
            path = self.harmonized_dir / f"{name}.parquet"
            if path.exists():
                df = pd.read_parquet(path)
                df.columns = [c.lower() for c in df.columns]
                tables[name] = df
                logger.info(f"Loaded {name}: {tables[name].shape}")
            else:
                logger.warning(f"File not found: {path}")
                tables[name] = pd.DataFrame()
        return tables

    def build_feature_matrix(self) -> pd.DataFrame:
        """Master method: load, join, engineer, output."""
        tables = self.load_harmonized()

        logger.info("Joining tables...")
        df = self._join_tables(tables)

        logger.info("Building base features...")
        df = self._build_age_features(df)
        df = self._build_vehicle_flags(df)
        df = self._build_time_features(df)
        df = self._build_weather_simple(df)

        logger.info("Building use case 1 features...")
        df = self._build_temporal_features(df)

        logger.info("Building use case 2 features...")
        df = self._build_positioning_features(df)

        logger.info("Building use case 3 features...")
        df = self._build_zone_risk_features(df)

        logger.info("Building use case 4 features...")
        df = self._build_infra_features(df)

        logger.info("Building use case 5 features...")
        df = self._build_t0_features(df)

        logger.info("Building use case 6 features...")
        df = self._build_weather_alert_features(df)

        logger.info("Building target...")
        df = self._build_target(df)

        logger.info("Adding Feast timestamp...")
        df = self._add_feast_timestamp(df)

        return df

    def _join_tables(self, tables: dict) -> pd.DataFrame:
        """Join 4 tables into flat matrix at USAGER grain.
        Join order: usagers <- vehicules (on num_acc + id_vehicule) <- lieux (on num_acc) <- caracteristiques (on num_acc)
        Use LEFT joins. Handle column conflicts with suffixes."""
        df = tables.get("usagers", pd.DataFrame())

        if df.empty:
            return df

        vehicules = tables.get("vehicules", pd.DataFrame())
        if not vehicules.empty:
            df = df.merge(
                vehicules,
                on=["num_acc", "id_vehicule"],
                how="left",
                suffixes=("", "_veh"),
            )

        lieux = tables.get("lieux", pd.DataFrame())
        if not lieux.empty:
            df = df.merge(lieux, on="num_acc", how="left", suffixes=("", "_lieux"))

        carac = tables.get("caracteristiques", pd.DataFrame())
        if not carac.empty:
            df = df.merge(carac, on="num_acc", how="left", suffixes=("", "_carac"))

        return df

    # === BASE FEATURES (all families) ===
    def _build_age_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """age = current_year - an_nais. age_bucket: 0-18, 19-25, 26-35, 36-50, 51-65, 65+"""
        if "an_nais" in df.columns:
            ref_year = df["an"] if "an" in df.columns else 2024
            df["age"] = ref_year - df["an_nais"]

            bins = [-1, 18, 25, 35, 50, 65, 150]
            labels = ["0-18", "19-25", "26-35", "36-50", "51-65", "65+"]
            df["age_bucket"] = pd.cut(df["age"], bins=bins, labels=labels)
        return df

    def _build_vehicle_flags(self, df: pd.DataFrame) -> pd.DataFrame:
        """is_motorise (catv not in [1, 60] and catu != 3)
        is_deux_roues (catv in [2,4,5,6,30,31,32,33,34,50])
        is_lourd (catv in [13,14,15,16,17,37,38])"""
        if "catv" in df.columns and "catu" in df.columns:
            df["is_motorise"] = (~df["catv"].isin([1, 60])) & (df["catu"] != 3)
            df["is_deux_roues"] = df["catv"].isin([2, 4, 5, 6, 30, 31, 32, 33, 34, 50])
            df["is_lourd"] = df["catv"].isin([13, 14, 15, 16, 17, 37, 38])
        return df

    def _build_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """From hrmn (HH:MM string):
        - hour (int)
        - periode_jour: 'Nuit' (22-6), 'Matin' (6-12), 'Après-midi' (12-18), 'Soir' (18-22)
        - is_night: lum in [3,4,5]"""
        if "hrmn" in df.columns:

            def extract_hour(x):
                try:
                    if pd.isna(x):
                        return np.nan
                    if isinstance(x, str):
                        parts = x.split(":")
                        if len(parts) >= 1:
                            return int(parts[0])
                    return np.nan
                except Exception:
                    return np.nan

            df["hour"] = df["hrmn"].apply(extract_hour)

            def get_periode(h):
                if pd.isna(h):
                    return np.nan
                h = int(h)
                if h < 6 or h >= 22:
                    return "Nuit"
                elif 6 <= h < 12:
                    return "Matin"
                elif 12 <= h < 18:
                    return "Après-midi"
                else:
                    return "Soir"

            df["periode_jour"] = df["hour"].apply(get_periode)

        if "lum" in df.columns:
            df["is_night"] = df["lum"].isin([3, 4, 5])

        return df

    def _build_weather_simple(self, df: pd.DataFrame) -> pd.DataFrame:
        """atm_simplifie: 'Normal' (atm=1), 'Pluie' (atm in [2,3]), 'Autre' (rest)"""
        if "atm" in df.columns:

            def map_atm(x):
                if pd.isna(x):
                    return np.nan
                if x == 1:
                    return "Normal"
                elif x in [2, 3]:
                    return "Pluie"
                else:
                    return "Autre"

            df["atm_simplifie"] = df["atm"].apply(map_atm)
        return df

    # === USE CASE 1: Temporal Anticipation ===
    def _build_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        df = self._add_feast_timestamp(df)
        """Create date from an, mois, jour. Then:
        jour_semaine (0=Monday..6=Sunday)
        is_weekend (jour_semaine >= 5)
        is_ferie (use calendar_utils)
        is_vacances_scolaires (use calendar_utils)"""
        if all(c in df.columns for c in ["an", "mois", "jour"]):
            try:
                date_s = pd.to_datetime(
                    df[["an", "mois", "jour"]].rename(
                        columns={"an": "year", "mois": "month", "jour": "day"}
                    ),
                    errors="coerce",
                )
                df["jour_semaine"] = date_s.dt.weekday
                df["is_weekend"] = df["jour_semaine"] >= 5

                # Apply on valid dates only
                df["is_ferie"] = date_s.dt.date.apply(is_ferie)
                df["is_vacances_scolaires"] = date_s.dt.date.apply(
                    is_vacances_scolaires
                )
            except Exception as e:
                logger.error(f"Error building temporal features: {e}")
        return df

    # === USE CASE 2: Emergency Positioning ===
    def _build_positioning_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """creneau_2h: hour // 2 * 2 (e.g., 14->14, 15->14)
        [ALERTE MLOPS] grav_max_accident supprimé pour éviter la fuite temporelle
        hrmn_valide: True if hrmn is not NaN and source_year not in [2021,2022]"""
        if "hour" in df.columns:
            df["creneau_2h"] = (df["hour"] // 2) * 2

        # [ALERTE MLOPS] TARGET LEAKAGE: L'utilisation du max sur l'accident courant divulgue la cible !
        # if "num_acc" in df.columns and "grav" in df.columns:
        #     df["grav_max_accident"] = df.groupby("num_acc")["grav"].transform("max")

        if "hrmn" in df.columns and "an" in df.columns:
            df["hrmn_valide"] = (~df["hrmn"].isna()) & (~df["an"].isin([2021, 2022]))

        return df

    # === USE CASE 3: Risk Zones ===
    def _build_zone_risk_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """[ALERTE MLOPS] nb_accidents_zone et taux_gravite_zone supprimés (Target Leakage global)
        granularite_fiable: True if lat and long are not NaN"""

        # [ALERTE MLOPS] P1: Correction de la Fuite Temporelle via Fenêtres Glissantes (Time-Aware Joins)
        if (
            "dep" in df.columns
            and "event_timestamp" in df.columns
            and "grav" in df.columns
        ):
            # 1. Trier chronologiquement
            df = df.sort_values("event_timestamp")

            # 2. Calculer le taux de gravité historique *jusqu'à l'accident précédent* (shift 1)
            # On utilise expanding pour avoir tout l'historique passé de la zone
            df["is_grave"] = df["grav"].isin([2, 3]).astype(float)

            # Taux historique
            df["taux_gravite_zone"] = df.groupby("dep")["is_grave"].transform(
                lambda x: x.expanding().mean().shift(1)
            )

            # Volume historique
            df["nb_accidents_zone"] = df.groupby("dep")["is_grave"].transform(
                lambda x: x.expanding().count().shift(1)
            )

            # Nettoyage et imputation pour les premiers accidents d'une zone
            df["taux_gravite_zone"] = df["taux_gravite_zone"].fillna(
                df["taux_gravite_zone"].mean()
            )
            df["nb_accidents_zone"] = df["nb_accidents_zone"].fillna(0)
            df = df.drop(columns=["is_grave"])

        if "lat" in df.columns and "long" in df.columns:
            df["granularite_fiable"] = (~df["lat"].isna()) & (~df["long"].isna())

        return df

    # === USE CASE 4: Infrastructure Aid ===
    def _build_infra_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """[ALERTE MLOPS] risque_relatif_catr supprimé (Target Leakage)
        vma_disponible: True if vma is not NaN"""

        # [ALERTE MLOPS] TARGET LEAKAGE
        # if "catr" in df.columns and "grav" in df.columns:
        #     df["risque_relatif_catr"] = df.groupby("catr")["grav"].transform(
        #         lambda x: x.isin([2, 3]).mean()
        #     )

        if "vma" in df.columns:
            df["vma_disponible"] = ~df["vma"].isna()
            df["vma"] = df["vma"].fillna(50.0)  # P2: Default Imputation for ML

        return df

    # === USE CASE 5: T0 Emergency Aid ===
    def _build_t0_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """lum_calculee: 'Jour' if lum in [1,2], 'Nuit' if lum in [3,4,5], else 'Inconnu'
        catr_derive: Map catr code to readable name using value_dictionaries
        atm_simplifie: already built above"""
        if "lum" in df.columns:

            def map_lum(x):
                if pd.isna(x):
                    return "Inconnu"
                if x in [1, 2]:
                    return "Jour"
                elif x in [3, 4, 5]:
                    return "Nuit"
                return "Inconnu"

            df["lum_calculee"] = df["lum"].apply(map_lum)

        if "catr" in df.columns:
            catr_dict = self.value_dictionaries.get("catr", {})
            df["catr_derive"] = df["catr"].map(catr_dict).fillna("Inconnu")

        return df

    # === USE CASE 6: Weather Alert ===
    def _build_weather_alert_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """risque_historique_meteo: Map atm to risk groups:
        'Faible' (atm in [1,8]), 'Modéré' (atm in [2,7]), 'Élevé' (atm in [3,4,5,6,9])"""
        if "atm" in df.columns:

            def map_atm_risk(x):
                if pd.isna(x):
                    return np.nan
                if x in [1, 8]:
                    return "Faible"
                elif x in [2, 7]:
                    return "Modéré"
                elif x in [3, 4, 5, 6, 9]:
                    return "Élevé"
                return "Inconnu"

            df["risque_historique_meteo"] = df["atm"].apply(map_atm_risk)

        return df

    # === BINARY TARGET ===
    def _build_target(self, df: pd.DataFrame) -> pd.DataFrame:
        """grav_binary: 1 if grav in [2,3] (Grave), 0 if grav in [1,4] (Léger)"""
        if "grav" in df.columns:

            def map_grav(x):
                if pd.isna(x):
                    return np.nan
                if x in [2, 3]:
                    return 1
                elif x in [1, 4]:
                    return 0
                return np.nan

            df["grav_binary"] = df["grav"].apply(map_grav)
        return df

    # === FEAST TIMESTAMP ===
    def _add_feast_timestamp(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create event_timestamp from an, mois, jour columns as proper datetime."""
        if all(c in df.columns for c in ["an", "mois", "jour"]):
            df["event_timestamp"] = pd.to_datetime(
                df[["an", "mois", "jour"]].rename(
                    columns={"an": "year", "mois": "month", "jour": "day"}
                ),
                errors="coerce",
            )
        return df

    def save_feature_matrix(
        self, df: pd.DataFrame, output_path="data/features/feature_matrix.parquet"
    ):
        """Save to parquet."""
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out_file, index=False)
        logger.info(f"Saved feature matrix to {output_path} with shape {df.shape}")


if __name__ == "__main__":
    fe = FeatureEngineer()
    df_features = fe.build_feature_matrix()
    fe.save_feature_matrix(df_features)
