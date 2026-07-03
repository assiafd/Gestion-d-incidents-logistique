from typing import Any, Literal, TypedDict


RiskLevel = Literal["low", "medium", "high", "critical"]


class IncidentState(TypedDict, total=False):
    question: str
    secure_mode: bool
    started_at: float
    sanitized_question: str
    input_security_findings: list[str]
    incident_type: str
    risk_level: RiskLevel
    corpus_documents: list[dict[str, str]]
    rag_results: list[dict[str, Any]]
    rag_answer: str
    kg_entities: list[dict[str, str]]
    kg_relations: list[dict[str, str]]
    kg_results: list[dict[str, str]]
    astra_status: dict[str, Any]
    draft_answer: str
    action_plan: list[dict[str, Any]]
    human_validation_required: bool
    human_validation: dict[str, Any]
    security_validation: dict[str, Any]
    database_status: dict[str, Any]
    final_json: dict[str, Any]
    monitoring: dict[str, Any]
    errors: list[str]
