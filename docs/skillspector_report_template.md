# Rapport Skillspector

Ce document est rempli automatiquement par:

```powershell
.\scripts\run_skillspector.ps1
```

Rapports attendus:

- `reports/skillspector-vulnerable-agents.md`
- `reports/skillspector-secure-agents.md`
- `reports/skillspector-full-report.json`

## Lecture attendue

La version vulnerable doit faire apparaitre des faiblesses liees aux instructions agentiques et au manque de garde-fous.
La version securisee doit reduire ces risques grace aux validations d'entree, de sortie, HITL et schema JSON.
