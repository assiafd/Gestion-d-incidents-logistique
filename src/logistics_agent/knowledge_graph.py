import re
from typing import Any

from astrapy import DataAPIClient

from logistics_agent.config import get_settings


KNOWN_ENTITIES = {
    "Valeo Kenitra": "supplier",
    "Continental Tanger": "supplier",
    "Tanger Med": "hub",
    "Kenitra": "site",
    "Casablanca": "warehouse",
    "Usine Renault Kenitra": "factory",
    "Entrepot Casablanca": "warehouse",
    "Modules moteur": "component",
    "Capteurs electroniques": "component",
    "Responsable Achats": "role",
    "Responsable Qualite": "role",
    "Responsable Supply Chain": "role",
    "Tour de Controle Logistique": "role",
}


def extract_knowledge_graph(documents: list[dict[str, str]]) -> tuple[list[dict], list[dict]]:
    entities: dict[str, dict[str, str]] = {}
    relations: list[dict[str, str]] = []
    all_text = "\n".join(doc["content"] for doc in documents)

    for name, entity_type in KNOWN_ENTITIES.items():
        if name.lower() in all_text.lower():
            entities[name] = {"id": slug(name), "name": name, "type": entity_type}

    static_relations = [
        ("Valeo Kenitra", "fournit", "Modules moteur"),
        ("Valeo Kenitra", "fournit", "Capteurs electroniques"),
        ("Valeo Kenitra", "a_fournisseur_alternatif", "Continental Tanger"),
        ("Continental Tanger", "approvisionne_urgence", "Kenitra"),
        ("Tanger Med", "distribue_vers", "Kenitra"),
        ("Tanger Med", "distribue_vers", "Casablanca"),
        ("Casablanca", "secours_pour", "Kenitra"),
        ("Responsable Achats", "valide", "fournisseur alternatif"),
        ("Responsable Qualite", "valide", "fournisseur alternatif"),
        ("Responsable Supply Chain", "evalue", "impact production"),
    ]
    for subject, relation, obj in static_relations:
        if subject in entities or obj in entities:
            relations.append({"subject": subject, "relation": relation, "object": obj})

    for match in re.finditer(r"([A-Za-z ]+)\s+-->\s+([A-Za-z ]+)", all_text):
        relations.append(
            {
                "subject": match.group(1).strip(),
                "relation": "route_vers",
                "object": match.group(2).strip(),
            }
        )

    return list(entities.values()), relations


def query_knowledge_graph(question: str, relations: list[dict[str, str]]) -> list[dict[str, str]]:
    words = {word.lower() for word in re.findall(r"[A-Za-z]{4,}", question)}
    scored = []
    for relation in relations:
        text = f"{relation['subject']} {relation['relation']} {relation['object']}".lower()
        score = sum(1 for word in words if word in text)
        if score:
            scored.append((score, relation))
    if not scored:
        return relations[:6]
    return [item[1] for item in sorted(scored, key=lambda item: item[0], reverse=True)[:8]]


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def save_kg_to_astra(entities: list[dict], relations: list[dict]) -> dict[str, Any]:
    settings = get_settings()
    if (
        not settings.astra_db_api_endpoint
        or not settings.astra_db_application_token
        or "replace-me" in settings.astra_db_api_endpoint
        or "replace-me" in settings.astra_db_application_token
    ):
        return {
            "enabled": False,
            "status": "not_saved",
            "message": "Astra credentials missing or still set to replace-me.",
        }

    try:
        client = DataAPIClient(settings.astra_db_application_token)
        database = client.get_database(settings.astra_db_api_endpoint, keyspace=settings.astra_db_keyspace)
        collection = database.get_collection(settings.astra_kg_collection)

        documents = [
            normalize_entity_for_astra(entity)
            for entity in entities
        ] + [
            normalize_relation_for_astra(relation)
            for relation in relations
        ]
        inserted_ids = []
        if documents:
            result = collection.insert_many(documents)
            inserted_ids = [str(item) for item in getattr(result, "inserted_ids", [])]
        return {
            "enabled": True,
            "status": "saved",
            "collection": settings.astra_kg_collection,
            "documents": len(documents),
            "inserted_ids": inserted_ids,
        }
    except Exception as exc:
        return {
            "enabled": True,
            "status": "not_saved",
            "collection": settings.astra_kg_collection,
            "message": f"{exc.__class__.__name__}: {exc}",
        }


def normalize_entity_for_astra(entity: dict[str, str]) -> dict[str, str]:
    return {
        "kind": "entity",
        "entity_id": entity["id"],
        "entity_name": entity["name"],
        "entity_type": entity["type"],
        "subject": entity["name"],
        "relation": "is_a",
        "object": entity["type"],
    }


def normalize_relation_for_astra(relation: dict[str, str]) -> dict[str, str]:
    return {
        "kind": "relation",
        "subject": relation["subject"],
        "relation": relation["relation"],
        "object": relation["object"],
    }
