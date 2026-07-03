import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from pymongo import MongoClient

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from logistics_agent.config import get_settings
from logistics_agent.graph import run_workflow


st.set_page_config(page_title="Dashboard Metier - Incidents Logistiques", layout="wide")
settings = get_settings()


st.markdown(
    """
    <style>
    .stApp {
        background: #f6f7fb;
        color: #172033;
    }
    [data-testid="stHeader"] {
        background: rgba(246, 247, 251, 0.86);
        backdrop-filter: blur(10px);
    }
    .block-container {
        padding-top: 2.2rem;
        padding-bottom: 2rem;
        max-width: 1280px;
    }
    .hero {
        background: linear-gradient(135deg, #102033 0%, #174457 54%, #256f72 100%);
        border-radius: 8px;
        padding: 28px 32px;
        color: white;
        margin-bottom: 22px;
        box-shadow: 0 18px 45px rgba(20, 40, 60, 0.18);
    }
    .hero h1 {
        font-size: 34px;
        margin: 0 0 8px 0;
        letter-spacing: 0;
    }
    .hero p {
        margin: 0;
        color: #d9edf0;
        font-size: 15px;
    }
    .kpi-card {
        background: white;
        border: 1px solid #e6e9f0;
        border-radius: 8px;
        padding: 18px 18px 16px 18px;
        box-shadow: 0 10px 28px rgba(20, 40, 60, 0.06);
        min-height: 116px;
    }
    .kpi-label {
        color: #607086;
        font-size: 13px;
        margin-bottom: 10px;
    }
    .kpi-value {
        color: #172033;
        font-size: 32px;
        font-weight: 760;
        line-height: 1;
    }
    .kpi-foot {
        color: #7a8797;
        font-size: 12px;
        margin-top: 10px;
    }
    .section-title {
        font-size: 18px;
        font-weight: 760;
        color: #172033;
        margin: 18px 0 8px 0;
    }
    div[data-testid="stDataFrame"] {
        border: 1px solid #e6e9f0;
        border-radius: 8px;
        overflow: hidden;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(ttl=1)
def load_business_events():
    try:
        client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=1500)
        client.admin.command("ping")
        collection = client[settings.mongodb_database][settings.mongodb_monitoring_collection]
        return list(collection.find({}, {"_id": 0}).sort("_id", -1).limit(500))
    except Exception:
        return []


def metric_card(label: str, value: str, foot: str = "") -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">{label}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-foot">{foot}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.markdown(
    """
    <div class="hero">
        <h1>Dashboard metier</h1>
        <p>Suivi operationnel des incidents logistiques, validations HITL et risques supply chain.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

events = load_business_events()
df = pd.DataFrame(events)

question = st.chat_input("Decrire un incident logistique...")
if question:
    with st.spinner("Analyse de l'incident en cours..."):
        result = run_workflow(question, secure_mode=True)
    st.session_state.setdefault("history", []).append(result)
    st.cache_data.clear()
    st.rerun()

if df.empty:
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Incidents", "0", "Aucune donnee MongoDB")
    with col2:
        metric_card("Risque critique", "0", "En attente de requetes")
    with col3:
        metric_card("Validations HITL", "0", "Aucune decision")
    with col4:
        metric_card("Cout estime", "$0.0000", "Monitoring vide")
    st.info("Aucune donnee metier dans MongoDB. Lance une requete agent depuis le terminal ou le chat.")
else:
    df["created_at"] = pd.to_datetime(df.get("created_at"), errors="coerce")
    critical_count = int((df["risk_level"] == "critical").sum()) if "risk_level" in df else 0
    hitl_count = int(df["human_validation_status"].notna().sum()) if "human_validation_status" in df else 0
    total_cost = float(df["estimated_cost_usd"].fillna(0).sum()) if "estimated_cost_usd" in df else 0.0

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        metric_card("Incidents", str(len(df)), "Evenements enregistres")
    with col2:
        metric_card("Risque critique", str(critical_count), "Incidents a prioriser")
    with col3:
        metric_card("Validations HITL", str(hitl_count), "Decisions humaines")
    with col4:
        metric_card("Cout estime", f"${total_cost:.4f}", "Cumul des requetes")

    st.markdown('<div class="section-title">Vue operationnelle</div>', unsafe_allow_html=True)
    display_cols = [
        "created_at",
        "question",
        "incident_type",
        "risk_level",
        "human_validation_status",
        "tokens",
        "estimated_cost_usd",
    ]
    available_cols = [col for col in display_cols if col in df.columns]
    st.dataframe(df[available_cols], use_container_width=True, hide_index=True)

    st.markdown('<div class="section-title">Statistiques metier</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        risk_counts = df["risk_level"].fillna("unknown").value_counts().reset_index()
        risk_counts.columns = ["risk_level", "count"]
        fig = px.bar(
            risk_counts,
            x="risk_level",
            y="count",
            color="risk_level",
            color_discrete_map={
                "critical": "#d64545",
                "high": "#f59e0b",
                "medium": "#256f72",
                "low": "#4f8f5f",
                "unknown": "#8a94a6",
            },
            title="Incidents par niveau de risque",
        )
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10), showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        hitl_counts = df["human_validation_status"].fillna("not_required").value_counts().reset_index()
        hitl_counts.columns = ["human_validation_status", "count"]
        fig = px.pie(
            hitl_counts,
            names="human_validation_status",
            values="count",
            title="Statut des validations humaines",
            color_discrete_sequence=["#256f72", "#d64545", "#f59e0b", "#8a94a6"],
        )
        fig.update_layout(height=360, margin=dict(l=10, r=10, t=50, b=10))
        st.plotly_chart(fig, use_container_width=True)

    if st.session_state.get("history"):
        st.markdown('<div class="section-title">Dernieres reponses du chat</div>', unsafe_allow_html=True)
        for item in st.session_state.get("history", [])[-3:]:
            with st.chat_message("assistant"):
                st.write(item["answer"])
