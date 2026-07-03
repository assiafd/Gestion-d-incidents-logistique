# MongoDB Online

Le projet utilise MongoDB en ligne pour stocker les evenements de monitoring.

## 1. Creer le fichier `.env`

```powershell
Copy-Item .env.example .env
notepad .env
```

## 2. Configurer MongoDB Atlas

Dans `.env`, remplacer:

```text
MONGODB_URI=mongodb+srv://replace-me:replace-me@replace-me.mongodb.net/incident_logistics_ai?retryWrites=true&w=majority
```

par l'URI MongoDB Atlas reelle:

```text
MONGODB_URI=mongodb+srv://<username>:<password>@<cluster-url>/incident_logistics_ai?retryWrites=true&w=majority
```

Garder ou adapter:

```text
MONGODB_DATABASE=incident_logistics_ai
MONGODB_MONITORING_COLLECTION=monitoring_events
```

## 3. Autoriser la connexion

Dans MongoDB Atlas:

- creer un database user;
- autoriser votre IP dans Network Access;
- copier l'URI de connexion Python;
- verifier que le mot de passe ne contient pas de caracteres non encodes dans l'URL.

## 4. Tester

```powershell
.\scripts\check_databases.ps1
```

## 5. Lancer le workflow

```powershell
python -m logistics_agent.main --json
```

Dans la sortie, verifier:

```json
"database_status": {
  "mongodb": {
    "status": "saved"
  }
}
```
