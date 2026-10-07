from pydantic import BaseModel, Field
from .base import AgentTool


class GetPrometheusMetricArgs(BaseModel):
    metric_name: str = Field(
        ..., description="Le nom de la métrique Prometheus à interroger."
    )
    query_window: str = Field(
        default="5m", description="La fenêtre de temps, ex: 5m, 1h."
    )


class GetPrometheusMetric(AgentTool):
    name = "get_prometheus_metric"
    description = "Interroge une métrique Prometheus pour vérifier l'état du système."
    args_schema = GetPrometheusMetricArgs

    def _execute(self, metric_name: str, query_window: str) -> str:
        # Simulation
        return f"[Simulé] Valeur pour {metric_name} sur {query_window}: 42.0"


class GetEvidentlyReportArgs(BaseModel):
    model_version: str = Field(..., description="Version du modèle.")


class GetEvidentlyReport(AgentTool):
    name = "get_evidently_report"
    description = "Récupère le dernier rapport Evidently pour détecter un data drift."
    args_schema = GetEvidentlyReportArgs

    def _execute(self, model_version: str) -> str:
        # Simulation
        return f"[Simulé] Aucun drift majeur pour le modèle {model_version}."
