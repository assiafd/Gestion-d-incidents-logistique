import argparse
import json

from logistics_agent.graph import run_workflow


def print_simple_response(result: dict) -> None:
    print("\n=== RESULTAT DU WORKFLOW ===")
    print(result["answer"])
    print(f"\nValidation humaine: {result.get('human_validation', {}).get('status', 'not_required')}")
    print("\nPlan d'action:")
    for action in result.get("action_plan", []):
        print(
            f"- P{action['priority']} {action['action']} "
            f"[{action.get('execution_status', 'recommended')}]"
        )
    db = result.get("database_status", {})
    astra = db.get("astra", {})
    astra_display = astra.get("status") or astra.get("message") or astra
    if astra.get("message") and astra.get("status") != "saved":
        astra_display = f"{astra.get('status', 'not_saved')} - {astra['message']}"
    print("\nPersistance:")
    print(f"- Astra: {astra_display}")
    print(f"- MongoDB: {db.get('mongodb', {}).get('status', 'unknown')}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the logistics incident LangGraph agent.")
    parser.add_argument("question", nargs="?", help="Question ou incident logistique a analyser.")
    parser.add_argument(
        "--vulnerable",
        action="store_true",
        help="Execute la version volontairement non securisee des agents.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Affiche la sortie JSON complete au lieu du message simple.",
    )
    args = parser.parse_args()
    question = args.question or input("Saisir votre question logistique: ").strip()
    result = run_workflow(question, secure_mode=not args.vulnerable)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print_simple_response(result)


if __name__ == "__main__":
    main()
