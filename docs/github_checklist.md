# Checklist GitHub

## Avant Le Commit

Verifier que `.env` n'est pas versionne:

```powershell
git status
```

Si `.env` apparait:

```powershell
git rm --cached .env
```

Verifier `.gitignore`:

```text
.env
.venv/
__pycache__/
*.pyc
reports/*.json
reports/*.sarif
reports/*.html
```

## Initialiser Le Repo

```powershell
git init
git add .
git status
git commit -m "Initial logistics incident agent project"
```

## Ajouter Le Remote

Remplacer l'URL par le lien GitHub fourni:

```powershell
git remote add origin https://github.com/<user>/<repo>.git
git branch -M main
git push -u origin main
```

## Fichiers A Inclure

- `src/`
- `dashboards/`
- `data/corpus/`
- `schemas/`
- `scripts/`
- `docs/`
- `obsidian-vault/`
- `.env.example`
- `README.md`
- `requirements.txt`
- `pyproject.toml`

## Fichiers A Ne Pas Inclure

- `.env`
- `.venv/`
- secrets;
- tokens Astra;
- URI MongoDB avec mot de passe;
- caches Python;
- fichiers temporaires.

## Verification Finale

```powershell
git status
git log --oneline -1
```
