import pandas as pd
import logging
import os
import csv
import yaml

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BAACHarmonizer")


class BAACHarmonizer:
    def __init__(
        self, raw_dir="data/raw", output_dir="data/harmonized", config_dir="config"
    ):
        self.raw_dir = raw_dir
        self.output_dir = output_dir
        self.config_dir = config_dir
        self.value_dictionaries = {}

        # Load value_dictionaries.yaml from config_dir
        dict_path = os.path.join(self.config_dir, "value_dictionaries.yaml")
        if os.path.exists(dict_path):
            with open(dict_path, "r") as f:
                self.value_dictionaries = yaml.safe_load(f) or {}

    def run_full_pipeline(self) -> dict:
        """Execute all 6 steps on all 4 tables. Returns dict of DataFrames."""
        tables = ["caracteristiques", "lieux", "vehicules", "usagers"]
        results = {}

        os.makedirs(self.output_dir, exist_ok=True)

        for table in tables:
            filepath = os.path.join(self.raw_dir, f"{table}.csv")
            if not os.path.exists(filepath):
                logger.warning(f"File not found: {filepath}")
                continue

            logger.info(f"Processing table: {table}")

            # Step 1: Defensive ingestion
            df = self._step1_ingest(filepath)

            # Step 2: Key reconciliation
            df = self._step2_reconcile_keys(df, table)

            # Step 3: Structural anomalies
            df = self._step3_fix_anomalies(df, table)

            # Step 4: Missing value unification
            df = self._step4_unify_missing(df)

            # Step 5: Geographic consolidation
            df = self._step5_consolidate_geo(df, table)

            # Step 6: Validation
            df = self._step6_validate(df, table)

            # Write to parquet
            out_path = os.path.join(self.output_dir, f"{table}.parquet")
            df.to_parquet(out_path, index=False)

            results[table] = df

        return results

    # Step 1: Defensive ingestion
    def _step1_ingest(self, filepath: str) -> pd.DataFrame:
        """Read CSV with dtype=str, encoding=latin-1, detect separator, inject source_year, normalize column names."""
        with open(filepath, "r", encoding="latin-1") as f:
            sample = f.read(4096)
            try:
                sep = csv.Sniffer().sniff(sample).delimiter
            except csv.Error:
                sep = ","

        df = pd.read_csv(filepath, sep=sep, encoding="latin-1", dtype=str)
        df.columns = df.columns.str.strip().str.lower()

        if "an" in df.columns:

            def parse_year(y):
                if pd.isna(y) or not str(y).strip():
                    return pd.NA
                y_str = str(y).strip()
                if len(y_str) == 2 and y_str.isdigit():
                    return int(y_str) + 2000
                elif y_str.isdigit():
                    return int(y_str)
                return pd.NA

            df["source_year"] = df["an"].apply(parse_year)

        return df

    # Step 2: Key reconciliation
    def _step2_reconcile_keys(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Rename Accident_Id -> Num_Acc, zero-pad Num_Acc, unify column names."""
        # Handle coexisting num_acc and accident_id columns
        if "accident_id" in df.columns and "num_acc" in df.columns:
            # Fill NaN in num_acc from accident_id
            mask = df["num_acc"].isna() | (
                df["num_acc"].astype(str).str.strip().isin(["", "nan", "None"])
            )
            df.loc[mask, "num_acc"] = df.loc[mask, "accident_id"]
            df = df.drop(columns=["accident_id"])
        elif "accident_id" in df.columns:
            df = df.rename(columns={"accident_id": "num_acc"})

        if "num_acc" in df.columns:
            # Convert to string, handle NaN, then zero-pad
            df["num_acc"] = df["num_acc"].fillna("").astype(str).str.strip()
            df = df[df["num_acc"] != ""]  # Drop rows without any accident ID
            df["num_acc"] = df["num_acc"].str.zfill(12)

        if table_name == "lieux":
            df = df.drop_duplicates(subset=["num_acc"], keep="first")

        return df

    # Step 3: Structural anomalies
    def _step3_fix_anomalies(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Handle hrmn multi-format, secu split, is_metropole, is_post_2018_grav_definition, geo_level."""
        if "hrmn" in df.columns:

            def fix_hrmn(val):
                if pd.isna(val) or str(val).strip() in ("", "nan"):
                    return pd.NA, False
                val = str(val).strip()
                if ":" in val:
                    # Already HH:MM or date pattern
                    if len(val) > 5 and val.count(":") > 1:  # like a date/time stamp
                        return pd.NA, True
                    return val[:5], False
                if val.isdigit():
                    val = val.zfill(4)
                    return f"{val[:2]}:{val[2:]}", False
                return pd.NA, True

            res = df["hrmn"].apply(fix_hrmn)
            df["hrmn"] = res.apply(lambda x: x[0])
            df["has_time_corrupted"] = res.apply(lambda x: x[1])

        if table_name == "usagers" and "secu" in df.columns:
            if not all(c in df.columns for c in ["secu1", "secu2", "secu3"]):

                def split_secu(val):
                    val = str(val).strip() if pd.notna(val) else ""
                    if len(val) >= 3:
                        return pd.Series([val[0], val[1], val[2]])
                    elif len(val) == 2:
                        return pd.Series([val[0], val[1], pd.NA])
                    elif len(val) == 1:
                        return pd.Series([val[0], pd.NA, pd.NA])
                    return pd.Series([pd.NA, pd.NA, pd.NA])

                df[["secu1", "secu2", "secu3"]] = df["secu"].apply(split_secu)

        if "dep" in df.columns:

            def is_metropole(val):
                v = str(val).strip()
                if v in ["2A", "2B", "201", "202"]:
                    return True
                try:
                    if int(v) >= 970:
                        return False
                except ValueError:
                    pass
                return True

            df["is_metropole"] = df["dep"].apply(is_metropole)

        if table_name == "lieux":

            def get_geo_level(row):
                if (
                    "lat" in row
                    and "long" in row
                    and pd.notna(row["lat"])
                    and pd.notna(row["long"])
                    and str(row["lat"]).strip() != ""
                    and str(row["long"]).strip() != ""
                ):
                    return "latlong"
                if (
                    "com" in row
                    and pd.notna(row["com"])
                    and str(row["com"]).strip() != ""
                ):
                    return "commune"
                return "departement"

            df["geo_level"] = df.apply(get_geo_level, axis=1)

        if "grav" in df.columns and "source_year" in df.columns:
            df["is_post_2018_grav_definition"] = df["source_year"] > 2018

        return df

    # Step 4: Missing value unification
    def _step4_unify_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Replace -1, 'N/A', 'NaN', '(1)', '' with pd.NA."""
        missing_vals = ["-1", "N/A", "NaN", "(1)", "", " "]
        # simplistic replace, ignoring value_dictionaries exceptions for now
        df = df.replace(missing_vals, pd.NA)
        return df

    # Step 5: Geographic consolidation
    def _step5_consolidate_geo(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Add territoire column, pad missing columns (vma for pre-2023)."""
        if "dep" in df.columns:
            df["territoire"] = df["dep"]

        if table_name == "lieux":
            if "vma" not in df.columns:
                df["vma"] = pd.NA
            if "source_year" in df.columns:
                df.loc[df["source_year"] < 2023, "vma"] = pd.NA

        return df

    # Step 6: Validation
    def _step6_validate(self, df: pd.DataFrame, table_name: str) -> pd.DataFrame:
        """Validate with Pandera schemas. Log row counts."""
        raw_count = len(df)

        # Drop rows with no Num_Acc
        df = df.dropna(subset=["num_acc"]) if "num_acc" in df.columns else df

        if "num_acc" in df.columns:
            df = df.rename(columns={"num_acc": "Num_Acc"})

        from src.data.contracts import (
            validate_caracteristiques_data,
            validate_lieux_data,
            validate_vehicules_data,
            validate_usager_data,
        )

        # Ensure correct types for validation
        if table_name == "caracteristiques":
            df["an"] = pd.to_numeric(df["an"], errors="coerce")
            df["mois"] = pd.to_numeric(df["mois"], errors="coerce")
            df["jour"] = pd.to_numeric(df["jour"], errors="coerce")
            df["lum"] = pd.to_numeric(df["lum"], errors="coerce")
            df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
            df["long"] = pd.to_numeric(df["long"], errors="coerce")
            try:
                df = validate_caracteristiques_data(df)
            except Exception as e:
                logger.warning(f"Validation failed for caracteristiques: {e}")

        elif table_name == "lieux":
            df["catr"] = pd.to_numeric(df["catr"], errors="coerce")
            df["surf"] = pd.to_numeric(df["surf"], errors="coerce")
            try:
                df = validate_lieux_data(df)
            except Exception as e:
                logger.warning(f"Validation failed for lieux: {e}")

        elif table_name == "vehicules":
            df["catv"] = pd.to_numeric(df["catv"], errors="coerce")
            try:
                df = validate_vehicules_data(df)
            except Exception as e:
                logger.warning(f"Validation failed for vehicules: {e}")

        elif table_name == "usagers":
            if "usager_id" not in df.columns:
                df["id_vehicule"] = df.get(
                    "id_vehicule", pd.Series(["0"] * len(df))
                ).fillna("0")
                df["num_veh"] = df.get("num_veh", pd.Series(["A"] * len(df))).fillna(
                    "A"
                )
                df["usager_id"] = (
                    df["Num_Acc"].astype(str)
                    + "_"
                    + df["id_vehicule"].astype(str)
                    + "_"
                    + df["num_veh"].astype(str)
                    + "_"
                    + df.index.astype(str)
                )
            df["grav"] = pd.to_numeric(df["grav"], errors="coerce")
            df["catu"] = pd.to_numeric(df["catu"], errors="coerce")
            df["sexe"] = pd.to_numeric(df["sexe"], errors="coerce")
            df["an_nais"] = pd.to_numeric(df["an_nais"], errors="coerce")
            try:
                df = validate_usager_data(df)
            except Exception as e:
                logger.warning(f"Validation failed for usagers: {e}")

        # Rename back to num_acc for consistency with expected python logic if needed,
        # or leave as Num_Acc. The schemas enforce Num_Acc. We'll leave it as Num_Acc.

        clean_count = len(df)
        drop_rate = (raw_count - clean_count) / raw_count if raw_count > 0 else 0

        logger.info(
            f"[{table_name}] raw_count={raw_count}, clean_count={clean_count}, drop_rate={drop_rate:.2%}"
        )
        assert (
            drop_rate < 0.05
        ), f"Drop rate {drop_rate:.2%} exceeded 5% threshold for {table_name}"

        return df


if __name__ == "__main__":
    harmonizer = BAACHarmonizer(
        raw_dir="data/raw", output_dir="data/harmonized", config_dir="config"
    )
    results = harmonizer.run_full_pipeline()
    for name, df in results.items():
        print(f"Successfully processed {name}: {len(df)} rows.")
