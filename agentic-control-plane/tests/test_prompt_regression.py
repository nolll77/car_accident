import json
from pathlib import Path


def test_prompt_quality_gates():
    ledger_path = Path(__file__).parent.parent / "trust_ledger.json"

    # If the ledger isn't there, we can't pass the gate.
    assert (
        ledger_path.exists()
    ), "Trust Ledger absent. Exécutez le pipeline d'évaluation en mode Shadow d'abord."

    with open(ledger_path, "r", encoding="utf-8") as f:
        ledger = json.load(f)

    accuracy = ledger["metrics"]["accuracy"]
    fn = ledger["metrics"]["false_negatives_sev5"]

    # Gate 1: Accord >= 90%
    assert (
        accuracy >= 0.90
    ), f"Gate échoué: L'exactitude du LLM ({accuracy*100}%) est inférieure au seuil de 90%."

    # Gate 2: 0 Faux Négatif sur Sévérité 5
    assert (
        fn == 0
    ), f"Gate échoué: {fn} Faux Négatifs détectés sur des risques critiques (Sévérité 5)."
