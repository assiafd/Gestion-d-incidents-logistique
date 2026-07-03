from logistics_agent.config import get_settings


def requires_human_validation(risk_level: str, action_plan: list[dict]) -> bool:
    if risk_level in {"high", "critical"}:
        return True
    return any(action.get("validation_required") for action in action_plan)


def request_human_validation(summary: str, action_plan: list[dict]) -> dict:
    settings = get_settings()
    if settings.hitl_mode != "console":
        return {
            "status": "pending_external_review",
            "validator": "external",
            "comment": "HITL mode is not console; route this decision to workflow UI or ticketing.",
        }

    print("\n=== HUMAN IN THE LOOP VALIDATION ===")
    print(summary)
    print("\nActions proposees:")
    for action in action_plan:
        marker = "validation requise" if action.get("validation_required") else "information"
        print(f"- P{action['priority']} {action['action']} ({action['owner']}, {marker})")
    decision = input("Approuver le plan d'action ? [yes/no]: ").strip().lower()
    return {
        "status": "approved" if decision in {"y", "yes", "oui", "o"} else "rejected",
        "validator": "console_user",
        "comment": "Manual validation captured from console.",
    }
