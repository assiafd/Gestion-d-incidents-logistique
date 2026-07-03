import json
import time
from pathlib import Path

from jsonschema import validate
from langgraph.graph import END, StateGraph

from logistics_agent.config import SCHEMA_PATH
from logistics_agent.hitl import request_human_validation, requires_human_validation
from logistics_agent.knowledge_graph import (
    extract_knowledge_graph,
    query_knowledge_graph,
    save_kg_to_astra,
)
from logistics_agent.monitoring import MonitoringRecorder
from logistics_agent.rag import load_corpus, naive_semantic_search, synthesize_rag_answer
from logistics_agent.secure_agents import (
    secure_business_agent,
    secure_input_guard,
    security_validation_agent,
)
from logistics_agent.state import IncidentState
from logistics_agent.vulnerable_agents import vulnerable_business_agent


def load_documents_node(state: IncidentState) -> IncidentState:
    state["corpus_documents"] = load_corpus()
    return state


def rag_node(state: IncidentState) -> IncidentState:
    question = state.get("sanitized_question") or state["question"]
    state["rag_results"] = naive_semantic_search(question, state.get("corpus_documents", []))
    state["rag_answer"] = synthesize_rag_answer(question, state["rag_results"])
    return state


def knowledge_graph_node(state: IncidentState) -> IncidentState:
    entities, relations = extract_knowledge_graph(state.get("corpus_documents", []))
    state["kg_entities"] = entities
    state["kg_relations"] = relations
    state["kg_results"] = query_knowledge_graph(state.get("sanitized_question") or state["question"], relations)
    state["astra_status"] = save_kg_to_astra(entities, relations)
    return state


def human_validation_node(state: IncidentState) -> IncidentState:
    state["human_validation_required"] = requires_human_validation(
        state.get("risk_level", "medium"),
        state.get("action_plan", []),
    )
    if state["human_validation_required"]:
        state["human_validation"] = request_human_validation(
            state.get("draft_answer", ""),
            state.get("action_plan", []),
        )
    else:
        state["human_validation"] = {"status": "not_required"}
    apply_human_validation_decision(state)
    return state


def apply_human_validation_decision(state: IncidentState) -> None:
    validation = state.get("human_validation", {})
    status = validation.get("status", "not_required")

    for action in state.get("action_plan", []):
        if status == "approved":
            action["execution_status"] = "approved"
        elif status == "rejected" and action.get("validation_required"):
            action["execution_status"] = "blocked_by_human"
        elif status == "rejected":
            action["execution_status"] = "recommended_only"
        elif status == "pending_external_review" and action.get("validation_required"):
            action["execution_status"] = "pending_human_validation"
        else:
            action["execution_status"] = "recommended"

    if status == "rejected":
        state["draft_answer"] = build_final_message(state, "rejected")
    elif status == "pending_external_review":
        state["draft_answer"] = build_final_message(state, "pending_external_review")
    elif status == "approved":
        state["draft_answer"] = build_final_message(state, "approved")
    else:
        state["draft_answer"] = build_final_message(state, "not_required")


def build_final_message(state: IncidentState, hitl_status: str) -> str:
    risk = state.get("risk_level", "medium")
    incident_type = state.get("incident_type", "incident_logistique")
    rag_answer = state.get("rag_answer", "Le RAG a retrouve des informations pertinentes.")

    if hitl_status == "approved":
        return (
            f"Incident {incident_type} avec risque {risk}. {rag_answer} "
            "Le plan d'action est approuve: notifier la Tour de Controle Logistique, evaluer l'impact "
            "production et preparer les actions de continuite avec validation Achats/Qualite."
        )
    if hitl_status == "rejected":
        return (
            f"Incident {incident_type} avec risque {risk}. {rag_answer} "
            "Le validateur humain a refuse le plan: les actions critiques sont bloquees. "
            "Il faut reviser le plan, documenter le motif du refus et proposer une alternative avant execution."
        )
    if hitl_status == "pending_external_review":
        return (
            f"Incident {incident_type} avec risque {risk}. {rag_answer} "
            "La validation humaine est en attente: aucune action critique ne doit etre executee pour le moment."
        )
    return f"Incident {incident_type} avec risque {risk}. {rag_answer}"


def json_formatter_node(state: IncidentState) -> IncidentState:
    final_json = {
        "answer": state.get("draft_answer", ""),
        "incident_type": state.get("incident_type", "incident_logistique"),
        "risk_level": state.get("risk_level", "medium"),
        "evidence": state.get("rag_results", []),
        "knowledge_graph_evidence": state.get("kg_results", []),
        "action_plan": state.get("action_plan", []),
        "human_validation_required": state.get("human_validation_required", False),
        "human_validation": state.get("human_validation", {"status": "not_required"}),
        "database_status": {
            "astra": state.get("astra_status", {"enabled": False, "message": "not_executed"}),
            "mongodb": {},
        },
        "security_validation": state.get(
            "security_validation",
            {"passed": False, "findings": ["Security validation not executed."]},
        ),
        "monitoring": {},
    }
    schema = json.loads(Path(SCHEMA_PATH).read_text(encoding="utf-8"))
    validate(instance=final_json, schema=schema)
    state["final_json"] = final_json
    return state


def monitoring_node(state: IncidentState) -> IncidentState:
    recorder = MonitoringRecorder()
    security_findings = state.get("security_validation", {}).get("findings", [])
    event = recorder.finish(
        question=state["question"],
        final_json=state.get("final_json", {}),
        security_findings=security_findings,
        errors=state.get("errors", []),
        started_at=state.get("started_at"),
    )
    state["monitoring"] = event
    state["final_json"]["monitoring"] = event
    state["final_json"]["database_status"]["mongodb"] = {
        "status": event.get("mongodb_status", "saved"),
        "database": event.get("mongodb_database"),
        "collection": event.get("mongodb_collection"),
        "inserted_id": event.get("mongodb_inserted_id"),
    }
    return state


def choose_business_agent(state: IncidentState) -> str:
    return "secure_business_agent" if state.get("secure_mode", True) else "vulnerable_business_agent"


def choose_input_guard(state: IncidentState) -> str:
    return "secure_input_guard" if state.get("secure_mode", True) else "load_documents"


def choose_security_validation(state: IncidentState) -> str:
    return "security_validation_agent" if state.get("secure_mode", True) else "human_validation"


def build_graph():
    graph = StateGraph(IncidentState)
    graph.add_node("secure_input_guard", secure_input_guard)
    graph.add_node("load_documents", load_documents_node)
    graph.add_node("rag_node", rag_node)
    graph.add_node("knowledge_graph_node", knowledge_graph_node)
    graph.add_node("secure_business_agent", secure_business_agent)
    graph.add_node("vulnerable_business_agent", vulnerable_business_agent)
    graph.add_node("security_validation_agent", security_validation_agent)
    graph.add_node("human_validation", human_validation_node)
    graph.add_node("json_formatter", json_formatter_node)
    graph.add_node("monitoring", monitoring_node)

    graph.set_conditional_entry_point(
        choose_input_guard,
        {
            "secure_input_guard": "secure_input_guard",
            "load_documents": "load_documents",
        },
    )
    graph.add_edge("secure_input_guard", "load_documents")
    graph.add_edge("load_documents", "rag_node")
    graph.add_edge("rag_node", "knowledge_graph_node")
    graph.add_conditional_edges(
        "knowledge_graph_node",
        choose_business_agent,
        {
            "secure_business_agent": "secure_business_agent",
            "vulnerable_business_agent": "vulnerable_business_agent",
        },
    )
    graph.add_conditional_edges(
        "secure_business_agent",
        choose_security_validation,
        {
            "security_validation_agent": "security_validation_agent",
            "human_validation": "human_validation",
        },
    )
    graph.add_edge("vulnerable_business_agent", "human_validation")
    graph.add_edge("security_validation_agent", "human_validation")
    graph.add_edge("human_validation", "json_formatter")
    graph.add_edge("json_formatter", "monitoring")
    graph.add_edge("monitoring", END)
    return graph.compile()


def run_workflow(question: str, secure_mode: bool = True) -> dict:
    app = build_graph()
    result = app.invoke(
        {
            "question": question,
            "secure_mode": secure_mode,
            "started_at": time.perf_counter(),
            "errors": [],
        }
    )
    return result["final_json"]
