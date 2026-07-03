from pathlib import Path

from logistics_agent.knowledge_graph import extract_knowledge_graph
from logistics_agent.rag import load_corpus


VAULT_DIR = Path(__file__).resolve().parents[2] / "obsidian-vault"


def export_to_obsidian() -> None:
    documents = load_corpus()
    entities, relations = extract_knowledge_graph(documents)
    VAULT_DIR.mkdir(parents=True, exist_ok=True)
    (VAULT_DIR / "README.md").write_text(
        "# Knowledge Graph Logistique\n\n"
        "Ouvrir ce dossier comme vault Obsidian pour visualiser les liens entre fournisseurs, hubs, sites et roles.\n",
        encoding="utf-8",
    )
    for entity in entities:
        links = [
            relation for relation in relations
            if relation["subject"] == entity["name"] or relation["object"] == entity["name"]
        ]
        body = [f"# {entity['name']}", "", f"Type: {entity['type']}", "", "## Relations"]
        for relation in links:
            if relation["subject"] == entity["name"]:
                body.append(f"- {relation['relation']} -> [[{relation['object']}]]")
            else:
                body.append(f"- [[{relation['subject']}]] -> {relation['relation']}")
        (VAULT_DIR / f"{entity['name']}.md").write_text("\n".join(body) + "\n", encoding="utf-8")


if __name__ == "__main__":
    export_to_obsidian()
