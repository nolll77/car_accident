import pandas as pd
import numpy as np
import logging
import os

logger = logging.getLogger(__name__)


class DriftMonitor:
    def __init__(
        self,
        reference_path="data/harmonized/usagers.parquet",
        prod_log_path="data/production_logs/shadow_log.csv",
    ):
        self.reference_path = reference_path
        self.prod_log_path = prod_log_path

    def calculate_psi(
        self, reference: pd.Series, production: pd.Series, n_bins=10
    ) -> float:
        """Calculate Population Stability Index between two distributions.
        PSI < 0.1 = no shift, 0.1-0.2 = moderate, > 0.2 = significant drift.
        """
        if len(reference) == 0 or len(production) == 0:
            return 0.0

        ref_array = np.array(reference)
        prod_array = np.array(production)

        # Check if numeric
        if pd.api.types.is_numeric_dtype(reference):
            # create bins
            bins = np.linspace(np.min(ref_array), np.max(ref_array), n_bins + 1)
            bins[0] = -np.inf
            bins[-1] = np.inf

            ref_percents = np.histogram(ref_array, bins)[0] / len(ref_array)
            prod_percents = np.histogram(prod_array, bins)[0] / len(prod_array)
        else:
            # categorical — force str pour éviter les comparaisons mixed-type int/str
            ref_array = ref_array.astype(str)
            prod_array = prod_array.astype(str)
            categories = np.unique(np.concatenate((ref_array, prod_array)))
            ref_percents = np.array(
                [np.sum(ref_array == val) for val in categories]
            ) / len(ref_array)
            prod_percents = np.array(
                [np.sum(prod_array == val) for val in categories]
            ) / len(prod_array)

        def sub_psi(e_perc, a_perc):
            # Avoid division by zero and log(0)
            e_perc = np.maximum(e_perc, 0.0001)
            a_perc = np.maximum(a_perc, 0.0001)
            return (a_perc - e_perc) * np.log(a_perc / e_perc)

        psi_value = np.sum(sub_psi(ref_percents, prod_percents))
        return float(psi_value)

    def detect_drift(self, features_to_monitor=None) -> dict:
        """Monitor drift on specified features. Returns dict with per-feature PSI."""
        if not os.path.exists(self.reference_path):
            logger.warning(f"Reference data not found at {self.reference_path}")
            return {}
        if not os.path.exists(self.prod_log_path):
            logger.warning(f"Production log not found at {self.prod_log_path}")
            return {}

        if self.reference_path.endswith(".parquet"):
            ref_df = pd.read_parquet(self.reference_path)
        else:
            ref_df = pd.read_csv(self.reference_path)

        if self.prod_log_path.endswith(".parquet"):
            prod_df = pd.read_parquet(self.prod_log_path)
        else:
            prod_df = pd.read_csv(self.prod_log_path)

        if features_to_monitor is None:
            features_to_monitor = [c for c in ref_df.columns if c in prod_df.columns]

        results = {}
        for feature in features_to_monitor:
            if feature in ref_df.columns and feature in prod_df.columns:
                ref_series = ref_df[feature].dropna()
                prod_series = prod_df[feature].dropna()
                if not ref_series.empty and not prod_series.empty:
                    psi = self.calculate_psi(ref_series, prod_series)
                    results[feature] = psi
                else:
                    results[feature] = None

        return results
