from pydantic import BaseModel, Field
from .base import AgentTool


class CheckDvcStatusArgs(BaseModel):
    dataset_path: str = Field(..., description="Le chemin du dataset à vérifier.")


class CheckDvcStatus(AgentTool):
    name = "check_dvc_status"
    description = (
        "Vérifie le hash DVC actuel d'un dataset pour détecter une modification."
    )
    args_schema = CheckDvcStatusArgs

    def _execute(self, dataset_path: str) -> str:
        return f"[Simulé] DVC up-to-date pour {dataset_path}. Hash: abcd123."


class ValidatePanderaSchemaArgs(BaseModel):
    table_name: str = Field(..., description="Nom de la table à valider.")


class ValidatePanderaSchema(AgentTool):
    name = "validate_pandera_schema"
    description = "Lance une validation de schéma à la volée sur une table de données."
    args_schema = ValidatePanderaSchemaArgs

    def _execute(self, table_name: str) -> str:
        return f"[Simulé] Schéma validé pour {table_name}: 0 erreur trouvée."
