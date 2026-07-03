import re
from dataclasses import dataclass

from logistics_agent.config import get_settings


PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"ignore\s+(toutes\s+)?les\s+instructions\s+(precedentes|pr[ée]c[ée]dentes)",
    r"ignore\s+les\s+instructions",
    r"oublie\s+(toutes\s+)?les\s+instructions",
    r"system\s+prompt",
    r"prompt\s+syst[èe]me",
    r"developer\s+message",
    r"jailbreak",
    r"do\s+anything\s+now",
    r"reveal\s+.*secret",
    r"donne[-\s]?moi\s+.*secret",
    r"secrets?\s+syst[èe]me",
    r"affiche\s+.*cle",
    r"affiche\s+.*cl[ée]",
    r"exfiltrat",
]

TOXICITY_PATTERNS = [
    r"\bmenace\b",
    r"\binsulte\b",
    r"\bhaine\b",
    r"\bviolence\b",
]


@dataclass
class SecurityResult:
    passed: bool
    findings: list[str]
    sanitized_text: str


def analyze_user_input(text: str) -> SecurityResult:
    settings = get_settings()
    findings: list[str] = []
    sanitized = text.strip()

    if len(sanitized) > settings.max_input_chars:
        findings.append("Input too long; truncated to MAX_INPUT_CHARS.")
        sanitized = sanitized[: settings.max_input_chars]

    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, sanitized, flags=re.IGNORECASE):
            findings.append(f"Prompt injection pattern detected: {pattern}")

    for pattern in TOXICITY_PATTERNS:
        if re.search(pattern, sanitized, flags=re.IGNORECASE):
            findings.append(f"Potential toxicity pattern detected: {pattern}")

    sanitized = re.sub(r"(?i)ignore\s+(all\s+)?previous\s+instructions", "[blocked]", sanitized)
    sanitized = re.sub(r"(?i)system\s+prompt", "[blocked]", sanitized)
    return SecurityResult(passed=not findings, findings=findings, sanitized_text=sanitized)


def validate_output(answer: str, evidence: list[dict], kg_results: list[dict]) -> dict:
    findings: list[str] = []
    evidence_text = " ".join(item.get("excerpt", "") for item in evidence).lower()
    kg_text = " ".join(
        f"{item.get('subject', '')} {item.get('relation', '')} {item.get('object', '')}"
        for item in kg_results
    ).lower()
    answer_terms = {term for term in re.findall(r"[a-zA-Z]{5,}", answer.lower())}
    grounded_terms = set(re.findall(r"[a-zA-Z]{5,}", evidence_text + " " + kg_text))

    if answer_terms:
        groundedness = len(answer_terms & grounded_terms) / len(answer_terms)
    else:
        groundedness = 1.0

    if groundedness < get_settings().hallucination_min_groundedness:
        findings.append(f"Low groundedness score: {groundedness:.2f}")

    if re.search(r"(?i)(api[_-]?key|token|password|secret)", answer):
        findings.append("Possible secret leakage in output.")

    return {
        "passed": not findings,
        "findings": findings,
        "groundedness": round(groundedness, 3),
    }
