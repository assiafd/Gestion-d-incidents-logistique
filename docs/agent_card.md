# Agent Card

## Nom

Assistant IA de Gestion des Incidents Logistiques.

## Version

V1 - LangGraph stateful agent.

## Objectif

Analyser un incident logistique industriel, exploiter un corpus documentaire, interroger un Knowledge Graph, proposer un plan d'action et controler les decisions critiques avec un humain.

## Modele

Modele exemple:

```text
deepseek-r1-distill-llama-70b
```

Le provider est configurable via `.env`.

## Entrees

- question utilisateur;
- corpus `.txt`;
- variables `.env`;
- statut des bases Astra et MongoDB.

## Sorties

- message simple pour l'utilisateur;
- JSON complet valide par schema;
- plan d'action;
- statut HITL;
- metriques monitoring;
- documents Knowledge Graph dans Astra;
- evenements MongoDB pour dashboards.

## Capacites

- Classification incident logistique.
- RAG naif semantique.
- Synthese RAG.
- Knowledge Graph entites/relations.
- Persistance Astra.
- Validation humaine.
- Validation securite.
- Monitoring cout, tokens, latence, disponibilite, toxicite, hallucination, attaques.
- Dashboards Streamlit.
- Visualisation Obsidian.

## Limites

- Les resultats dependent du corpus fourni.
- Le RAG est volontairement simple.
- L'agent ne doit pas executer directement une action physique ou metier critique.
- Les decisions critiques exigent HITL.
- La detection de toxicite/hallucination est heuristique dans cette version.

## Risques

- Prompt injection utilisateur.
- Instruction malveillante dans le corpus.
- Mauvaise configuration `.env`.
- Token/API leak.
- Indisponibilite MongoDB/Astra.

## Mesures De Maitrise

- Input guard.
- Validation de sortie.
- JSON schema.
- HITL.
- SkillSpector.
- `.gitignore` pour `.env`.
- Logs monitoring dans MongoDB.
