import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from pymongo import MongoClient

from logistics_agent.config import get_settings


@dataclass
class MonitoringRecorder:
    started_at: float = field(default_factory=time.perf_counter)
    metrics: dict[str, Any] = field(default_factory=dict)

    def finish(
        self,
        question: str,
        final_json: dict[str, Any],
        security_findings: list[str],
        errors: list[str] | None = None,
        started_at: float | None = None,
    ) -> dict[str, Any]:
        effective_started_at = started_at or self.started_at
        latency_ms = round((time.perf_counter() - effective_started_at) * 1000, 2)
        answer = final_json.get("answer", "")
        approx_tokens = max(1, int((len(question) + len(answer)) / 4))
        finding_text = " ".join(security_findings).lower()
        prompt_injection_detected = int(
            any(
                marker in finding_text
                for marker in [
                    "prompt injection",
                    "ignore",
                    "instructions",
                    "system prompt",
                    "prompt systeme",
                    "prompt système",
                    "secret",
                    "exfiltrat",
                ]
            )
        )
        security_validation = final_json.get("security_validation", {})
        groundedness = security_validation.get("groundedness", 1.0)
        hallucination_flag = int(
            groundedness is not None
            and isinstance(groundedness, (int, float))
            and groundedness < get_settings().hallucination_min_groundedness
        )
        event = {
            "created_at": datetime.now(timezone.utc).isoformat(),
            "question": question,
            "incident_type": final_json.get("incident_type"),
            "risk_level": final_json.get("risk_level"),
            "human_validation_status": final_json.get("human_validation", {}).get("status"),
            "latency_ms": latency_ms,
            "response_time_ms": latency_ms,
            "tokens": approx_tokens,
            "estimated_cost_usd": round((approx_tokens / 1_000_000) * 0.70, 6),
            "hallucinations": hallucination_flag,
            "groundedness": groundedness,
            "toxicity": int(any("toxicity" in finding.lower() for finding in security_findings)),
            "prompt_injection_detected": prompt_injection_detected,
            "jailbreak_detected": int("jailbreak" in finding_text),
            "availability": 0 if errors else 1,
            "request_count": 1,
            "errors": errors or [],
        }
        self.save_to_mongodb(event)
        return event

    def save_to_mongodb(self, event: dict[str, Any]) -> None:
        settings = get_settings()
        try:
            if "replace-me" in settings.mongodb_uri:
                raise ValueError("MONGODB_URI still contains replace-me. Configure your online MongoDB URI in .env.")
            client = MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=1200)
            client.admin.command("ping")
            db = client[settings.mongodb_database]
            result = db[settings.mongodb_monitoring_collection].insert_one(event.copy())
            event["mongodb_status"] = "saved"
            event["mongodb_database"] = settings.mongodb_database
            event["mongodb_collection"] = settings.mongodb_monitoring_collection
            event["mongodb_inserted_id"] = str(result.inserted_id)
        except Exception as exc:
            event["mongodb_status"] = f"not_saved: {exc.__class__.__name__}: {exc}"
            event["mongodb_database"] = settings.mongodb_database
            event["mongodb_collection"] = settings.mongodb_monitoring_collection
