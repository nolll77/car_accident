from pydantic import BaseModel, Field
from .base import AgentTool


class CheckDatabaseHealthArgs(BaseModel):
    db_name: str = Field(..., description="Le nom de la base de données PostgreSQL.")


class CheckDatabaseHealth(AgentTool):
    name = "check_database_health"
    description = (
        "Simule un ping sur la base de données pour vérifier son état de santé."
    )
    args_schema = CheckDatabaseHealthArgs

    def _execute(self, db_name: str) -> str:
        return f"[Simulé] Ping réussi sur {db_name}. Latence: 12ms."


class CheckDockerContainerArgs(BaseModel):
    container_name: str = Field(..., description="Le nom du conteneur Docker.")


class CheckDockerContainer(AgentTool):
    name = "check_docker_container"
    description = "Simule l'inspection de l'état d'un conteneur Docker."
    args_schema = CheckDockerContainerArgs

    def _execute(self, container_name: str) -> str:
        return f"[Simulé] Le conteneur {container_name} est 'Up 24 hours'."
