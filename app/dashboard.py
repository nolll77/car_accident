import streamlit as st
import json
import glob
from pathlib import Path
import pandas as pd

st.set_page_config(page_title="Control Plane Observability", layout="wide")

st.title("🤖 Agentic Control Plane - Observability")
st.markdown(
    "Ce dashboard lit directement les **Evidences MLOps** (JSON) générées par notre flotte d'agents pour auditer leurs décisions de remédiation."
)

# Chemin vers les évidences
evidence_dir = Path("agentic-control-plane/evidence")

files = glob.glob(str(evidence_dir / "*.json"))

if not files:
    st.info("Aucun épisode d'évidence trouvé. Lancez le Control Plane.")
else:
    # Charger tous les épisodes
    episodes = []
    for f in files:
        with open(f, "r", encoding="utf-8") as file:
            try:
                episodes.append(json.load(file))
            except json.JSONDecodeError:
                pass

    # Trier par timestamp décroissant (les plus récents en premier)
    episodes.sort(key=lambda x: x.get("timestamp_utc", ""), reverse=True)

    st.subheader("Historique des Épisodes de Remédiation")

    # Créer un DataFrame pour le tableau récapitulatif
    df_data = []
    for ep in episodes:
        df_data.append(
            {
                "Episode ID": ep.get("episode_id"),
                "Timestamp": ep.get("timestamp_utc"),
                "Risk ID": ep.get("risk_id"),
                "Signal": ep.get("signal", {}).get("signal_id"),
                "Action Planifiée": ep.get("action_proposal", {}).get("type", "N/A"),
                "Décision Policy": ep.get("policy_evaluation", {}).get(
                    "decision", "N/A"
                ),
            }
        )
    st.dataframe(pd.DataFrame(df_data), use_container_width=True)

    st.divider()

    # Affichage détaillé de l'épisode sélectionné
    selected_ep_id = st.selectbox(
        "Sélectionnez un épisode pour voir le détail (Chain of Thought)",
        [ep["episode_id"] for ep in episodes],
    )
    selected_ep = next(ep for ep in episodes if ep["episode_id"] == selected_ep_id)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown(f"### 📡 Signal ({selected_ep.get('risk_id')})")
        signal = selected_ep.get("signal", {})
        st.metric(
            "Drift Value",
            f"{signal.get('value', 0):.2f}",
            f"Threshold: {signal.get('threshold')}",
        )
        st.json(signal)

        st.markdown("### 🩺 Diagnostic (Data Specialist)")
        diagnosis = selected_ep.get("diagnosis", {})
        findings = diagnosis.get("findings", [])
        for finding in findings:
            st.info(f"**Trouvaille** : {finding.get('description')}")

    with col2:
        st.markdown("### 🗺️ Plan (Remediation Agent)")
        action = selected_ep.get("action_proposal", {})
        st.warning(f"**Action proposée** : {action.get('type')}")
        if "parameters" in action:
            st.json(action.get("parameters"))

        st.markdown("### ⚖️ Décision (Policy Engine)")
        policy = selected_ep.get("policy_evaluation", {})
        decision = policy.get("decision")
        if decision == "ALLOW":
            st.success(f"Action Autorisée ! Règle: {policy.get('matched_rule')}")
        else:
            st.error(f"Action Bloquée : {decision}")

        st.markdown("### 🛤️ State Trace")
        trace = selected_ep.get("state_trace", [])
        st.markdown(" ➔ ".join([f"`{state}`" for state in trace]))
