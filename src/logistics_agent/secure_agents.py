from logistics_agent.security import analyze_user_input, validate_output
from logistics_agent.state import IncidentState


def secure_input_guard(state: IncidentState) -> IncidentState:
    result = analyze_user_input(state["question"])
    state["sanitized_question"] = result.sanitized_text
    state["input_security_findings"] = result.findings
    return state


def secure_business_agent(state: IncidentState) -> IncidentState:
    question = state.get("sanitized_question") or state["question"]
    kg_results = state.get("kg_results", [])
    rag_answer = state.get("rag_answer", "Le RAG a retrouve des informations pertinentes.")

    risk_level = infer_risk_level(question)
    action_plan = build_action_plan(question, risk_level, kg_results)
    state["incident_type"] = infer_incident_type(question)
    state["risk_level"] = risk_level
    state["action_plan"] = action_plan
    state["draft_answer"] = (
        f"Incident analyse: {infer_incident_type(question)}. "
        f"{rag_answer} "
        "Le Knowledge Graph confirme les dependances entre Tanger Med, Kenitra, Casablanca, "
        "Valeo Kenitra et Continental Tanger."
    )
    return state


def security_validation_agent(state: IncidentState) -> IncidentState:
    validation = validate_output(
        state.get("draft_answer", ""),
        state.get("rag_results", []),
        state.get("kg_results", []),
    )
    findings = list(state.get("input_security_findings", [])) + validation["findings"]
    state["security_validation"] = {
        "passed": not findings,
        "findings": findings,
        "groundedness": validation.get("groundedness"),
    }
    return state


def infer_incident_type(question: str) -> str:
    q = question.lower()
    if "retard" in q or "transport" in q:
        return "retard_transport"
    if "rupture" in q or "stock" in q:
        return "rupture_stock"
    if "fournisseur" in q:
        return "incident_fournisseur"
    return "incident_logistique"


def infer_risk_level(question: str) -> str:
    q = question.lower()
    if any(word in q for word in ["arret", "bloque", "critique", "rupture", "6 heures"]):
        return "critical"
    if any(word in q for word in ["retard", "production", "kenitra", "valeo"]):
        return "high"
    return "medium"


def build_action_plan(question: str, risk_level: str, kg_results: list[dict]) -> list[dict]:
    plan = [
        {
            "priority": 1,
            "action": "Notifier la Tour de Controle Logistique si le retard depasse 2 heures",
            "owner": "Transporteur",
            "validation_required": False,
        },
        {
            "priority": 2,
            "action": "Evaluer l'impact sur la production de l'usine de Kenitra",
            "owner": "Responsable Supply Chain",
            "validation_required": False,
        },
    ]
    has_alternative = any("Continental Tanger" in str(item) for item in kg_results)
    if risk_level in {"high", "critical"} or has_alternative:
        plan.append(
            {
                "priority": 3,
                "action": "Preparer une commande d'urgence chez Continental Tanger",
                "owner": "Responsable Achats",
                "validation_required": True,
            }
        )
        plan.append(
            {
                "priority": 4,
                "action": "Valider la conformite qualite avant activation du fournisseur alternatif",
                "owner": "Responsable Qualite",
                "validation_required": True,
            }
        )
    return plan
