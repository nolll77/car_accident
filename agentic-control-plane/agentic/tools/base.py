from typing import Any, Type
from pydantic import BaseModel


class AgentTool:
    """
    Interface de base pour tous les outils.
    Encapsule strictement le schéma Pydantic pour éviter les hallucinations LLM.
    """

    name: str
    description: str
    args_schema: Type[BaseModel]

    def run(self, **kwargs) -> Any:
        # Validate arguments using the schema before execution
        validated_args = self.args_schema(**kwargs)
        return self._execute(**validated_args.model_dump())

    def _execute(self, **kwargs) -> Any:
        raise NotImplementedError("Subclasses must implement _execute")
