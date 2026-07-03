from logistics_agent.graph import run_workflow


def test_secure_workflow_returns_expected_json_shape(monkeypatch):
    monkeypatch.setenv("HITL_MODE", "external")
    result = run_workflow("Retard transport de 6 heures entre Tanger Med et Kenitra", secure_mode=True)
    assert result["risk_level"] in {"low", "medium", "high", "critical"}
    assert result["evidence"]
    assert result["knowledge_graph_evidence"]
    assert "security_validation" in result
