# SkillSpector

Cette integration suit l'outil NVIDIA SkillSpector:

https://github.com/NVIDIA/skillspector

SkillSpector sert a scanner les agents, prompts, skills et configurations afin de detecter des risques:

- prompt injection;
- data exfiltration;
- privilege escalation;
- dangerous code;
- YARA signatures;
- tool misuse;
- system prompt leakage;
- output handling issues.

## Script principal du projet

Utiliser le wrapper:

```powershell
.\scripts\skillspector_scan.ps1 -Mode auto
```

Ce script produit:

- `reports/skillspector-vulnerable-agents.md`
- `reports/skillspector-secure-agents.md`
- `reports/skillspector-full-report.json`
- `reports/skillspector-execution-status.md`

## Mode local

Le mode local utilise une installation existante de `skillspector`, ou `uvx` / `uv` depuis GitHub.

```powershell
.\scripts\skillspector_scan.ps1 -Mode local
```

Installation manuelle possible:

```powershell
uv tool install git+https://github.com/NVIDIA/skillspector.git
```

Avec MCP:

```powershell
uv tool install --force 'skillspector[mcp] @ git+https://github.com/NVIDIA/skillspector.git'
```

## Mode Docker

Le mode Docker evite la compilation locale de `yara-python`.

```powershell
.\scripts\skillspector_scan.ps1 -Mode docker
```

Prerequis:

- Docker Desktop installe;
- Docker Desktop demarre;
- daemon Linux actif.

Si l'erreur mentionne `dockerDesktopLinuxEngine`, Docker Desktop n'est pas demarre.

## Mode sans LLM

Par defaut, le wrapper lance un scan statique sans LLM.

```powershell
.\scripts\skillspector_scan.ps1 -Mode auto
```

## Mode avec LLM

Pour activer l'analyse semantique LLM:

```powershell
.\scripts\skillspector_scan.ps1 -Mode auto -UseLlm
```

Configurer les variables selon le provider choisi par SkillSpector. Exemple NVIDIA:

```powershell
$env:SKILLSPECTOR_PROVIDER="nv_build"
$env:NVIDIA_INFERENCE_KEY="nvapi-..."
```

## Interpretation dans le projet

Le scan compare volontairement:

- `src/logistics_agent/vulnerable_agents.py`: agents de l'etape 1, non securises;
- `src/logistics_agent`: agents securises de l'etape 3;
- `.`: projet complet pour un rapport JSON.

Le rapport attendu doit montrer que la version securisee reduit les risques grace aux controles:

- input guard;
- validation de sortie;
- schema JSON;
- Human in the loop;
- monitoring;
- separation RAG / Knowledge Graph / agent metier.
