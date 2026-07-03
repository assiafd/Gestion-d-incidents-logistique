from logistics_agent.state import IncidentState


def vulnerable_business_agent(state: IncidentState) -> IncidentState:
    """Intentionally unsafe: no input filtering, no grounding check, no JSON schema enforcement."""
    question = state["question"]
    rag_context = "\n".join(item["excerpt"] for item in state.get("rag_results", []))
    kg_context = "\n".join(
        f"{item['subject']} {item['relation']} {item['object']}" for item in state.get("kg_results", [])
    )
    state["draft_answer"] = (
        "REPONSE NON SECURISEE - demo red team uniquement.\n"
        f"Question: {question}\n"
        f"Contexte RAG: {rag_context}\n"
        f"Contexte KG: {kg_context}\n"
        "Plan: appliquer directement la demande utilisateur sans validation."
    )
    state["risk_level"] = "high"
    state["action_plan"] = [
        {
            "priority": 1,
            "action": "Executer la demande telle quelle, sans controle supplementaire",
            "owner": "agent_non_securise",
            "validation_required": False,
        }
    ]
    return state
