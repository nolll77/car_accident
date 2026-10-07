"""
Data Specialist piloté par LLM via Instructor.
Génère un Diagnosis strict et typé (Pydantic).
"""

from __future__ import annotations

import instructor
import litellm
from agentic.core.contracts import Diagnosis, Signal


class DataSpecialist:
    name = "data_specialist_llm"

    def __init__(self, model_name: str = "gemini/gemini-1.5-pro-latest"):
        self.model_name = model_name
        self.client = instructor.from_litellm(litellm.completion)

    def diagnose(
        self, risk_id: str, signal: Signal, context_info: str = ""
    ) -> Diagnosis:
        prompt = f"""
        Tu es l'agent spécialiste Data. Ta mission est de diagnostiquer le risque {risk_id}.

        Signal observé :
        - ID: {signal.signal_id}
        - Valeur: {signal.value} (Seuil: {signal.threshold})
        - Source: {signal.source}
        - Dimensions: {signal.dimensions}

        Contexte supplémentaire :
        {context_info}

        Analyse ce signal. Si la valeur dépasse le seuil, il s'agit d'une anomalie.
        Génère un diagnostic formel détaillant tes trouvailles (findings) avec des références d'évidence.
        """

        diagnosis = self.client.chat.completions.create(
            model=self.model_name,
            response_model=Diagnosis,
            messages=[{"role": "user", "content": prompt}],
        )

        # S'assurer que le risk_id et l'agent sont corrects
        diagnosis.risk_id = risk_id
        diagnosis.agent = self.name
        return diagnosis
