import sys
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from pymongo import MongoClient

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from logistics_agent.config import get_settings


st.set_page_config(page_title="Dashboard Monitoring - Agent IA", layout="wide")
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
        background: linear-gradient(135deg, #171d2b 0%, #23324a 48%, #344e72 100%);
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
        color: #dce7f7;
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
        font-size: 31px;
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
def load_events():
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
        <h1>Dashboard monitoring</h1>
        <p>Observabilite agentique: latence, cout, tokens, disponibilite, qualite et signaux d'attaque.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

events = load_events()
df = pd.DataFrame(events)

if df.empty:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        metric_card("Latence moyenne", "0 ms", "Aucune requete")
    with c2:
        metric_card("Cout total", "$0.0000", "Aucun cout")
    with c3:
        metric_card("Tokens", "0", "Aucun token")
    with c4:
        metric_card("Disponibilite", "0%", "Aucune mesure")
    st.info("Aucune donnee MongoDB disponible. Lance d'abord quelques requetes agent.")
    st.stop()

df["created_at"] = pd.to_datetime(df.get("created_at"), errors="coerce")
df = df.sort_values("created_at").reset_index(drop=True)
df["request_index"] = df.index + 1

latency_mean = float(df["latency_ms"].fillna(0).mean())
total_cost = float(df["estimated_cost_usd"].fillna(0).sum())
tokens_total = int(df["tokens"].fillna(0).sum())
availability = float(df["availability"].fillna(0).mean() * 100)
attacks = int(df["prompt_injection_detected"].fillna(0).sum() + df["jailbreak_detected"].fillna(0).sum())

c1, c2, c3, c4 = st.columns(4)
with c1:
    metric_card("Latence moyenne", f"{latency_mean:.0f} ms", "Temps de reponse agent")
with c2:
    metric_card("Cout total", f"${total_cost:.4f}", "Estimation cumulative")
with c3:
    metric_card("Tokens", f"{tokens_total:,}".replace(",", " "), "Volume consomme")
with c4:
    metric_card("Disponibilite", f"{availability:.1f}%", "Requetes sans erreur")

c5, c6, c7, c8 = st.columns(4)
with c5:
    metric_card("Hallucinations", str(int(df["hallucinations"].fillna(0).sum())), "Groundedness faible")
with c6:
    metric_card("Toxicite", str(int(df["toxicity"].fillna(0).sum())), "Signaux detectes")
with c7:
    metric_card("Attaques", str(attacks), "Injection + jailbreak")
with c8:
    metric_card("Erreurs", str(int((df["availability"].fillna(1) == 0).sum())), "Disponibilite degradee")

st.markdown('<div class="section-title">Graphiques temporels</div>', unsafe_allow_html=True)
g1, g2 = st.columns(2)
with g1:
    fig = px.line(df, x="request_index", y="latency_ms", markers=True, title="Latence par requete")
    fig.update_traces(line_color="#256f72")
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)
with g2:
    fig = px.area(df, x="request_index", y="tokens", title="Tokens par requete")
    fig.update_traces(line_color="#344e72", fillcolor="rgba(52, 78, 114, 0.24)")
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)

g3, g4 = st.columns(2)
with g3:
    signal_cols = ["prompt_injection_detected", "jailbreak_detected", "toxicity", "hallucinations"]
    signal_df = df[signal_cols].fillna(0).sum().reset_index()
    signal_df.columns = ["signal", "count"]
    fig = px.bar(
        signal_df,
        x="signal",
        y="count",
        color="signal",
        title="Signaux securite et qualite",
        color_discrete_sequence=["#d64545", "#f59e0b", "#7c3aed", "#256f72"],
    )
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=50, b=10), showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
with g4:
    latest_groundedness = df["groundedness"].dropna().iloc[-1] if "groundedness" in df and df["groundedness"].notna().any() else 1
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=float(latest_groundedness) * 100,
            title={"text": "Groundedness derniere requete"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#256f72"},
                "steps": [
                    {"range": [0, 55], "color": "#f8d7da"},
                    {"range": [55, 80], "color": "#fff2cc"},
                    {"range": [80, 100], "color": "#d7f3e3"},
                ],
            },
        )
    )
    fig.update_layout(height=340, margin=dict(l=10, r=10, t=50, b=10))
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div class="section-title">Logs d\'execution</div>', unsafe_allow_html=True)
log_cols = [
    "created_at",
    "question",
    "incident_type",
    "risk_level",
    "human_validation_status",
    "latency_ms",
    "tokens",
    "estimated_cost_usd",
    "prompt_injection_detected",
    "jailbreak_detected",
    "availability",
]
available_cols = [col for col in log_cols if col in df.columns]
st.dataframe(df[available_cols].sort_values("created_at", ascending=False), use_container_width=True, hide_index=True)
