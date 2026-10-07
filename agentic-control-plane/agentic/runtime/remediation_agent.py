"""
Remediation Agent piloté par LLM via Instructor.
Coordonne le plan d'action en se basant sur le diagnostic d'un spécialiste.
"""

from __future__ import annotations

import instructor
import litellm
from agentic.core.contracts import Diagnosis, ActionProposal


class RemediationAgent:
    name = "remediation_agent_llm"

    def __init__(self, model_name: str = "gemini/gemini-1.5-pro-latest"):
        self.model_name = model_name
        self.client = instructor.from_litellm(litellm.completion)

    def plan_action(self, diagnosis: Diagnosis) -> ActionProposal:
        prompt = f"""
        Tu es le 'Remediation Agent' (Coordinateur principal).
        Un agent spécialisé ({diagnosis.agent}) a émis le diagnostic suivant pour le risque '{diagnosis.risk_id}':

        Niveau de confiance: {diagnosis.confidence}
        Trouvailles:
        {chr(10).join([f'- {f.description}' for f in diagnosis.findings])}

        Ta mission est de proposer la meilleure action de remédiation parmi les ActionType disponibles.
        Si la confiance est basse ou les trouvailles bénignes, propose INVESTIGATE.
        Si le risque est élevé, choisis CREATE_ISSUE, PROPOSE_RETRAIN, ROLLBACK_PROD, etc., selon le cas.

        Génère l'ActionProposal Pydantic. Assure-toi de paramétrer correctement le blast_radius (0-5) et la réversibilité.
        """

        proposal = self.client.chat.completions.create(
            model=self.model_name,
            response_model=ActionProposal,
            messages=[{"role": "user", "content": prompt}],
        )

        # Override fields to maintain strict security chain constraints
        proposal.requested_by = self.name
        proposal.risk_id = diagnosis.risk_id

        return proposal
