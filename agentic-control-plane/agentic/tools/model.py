from pydantic import BaseModel, Field
from .base import AgentTool


class GetMLflowModelInfoArgs(BaseModel):
    model_name: str = Field(..., description="Le nom du modèle MLflow.")
    stage: str = Field(
        default="Production", description="L'environnement (Production, Staging)."
    )


class GetMLflowModelInfo(AgentTool):
    name = "get_mlflow_model_info"
    description = "Récupère les métadonnées d'un modèle enregistré dans MLflow."
    args_schema = GetMLflowModelInfoArgs

    def _execute(self, model_name: str, stage: str) -> str:
        return f"[Simulé] Modèle {model_name} en {stage}. F1-Score: 0.88."
