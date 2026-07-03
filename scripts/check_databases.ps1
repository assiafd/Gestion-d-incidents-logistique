Write-Host "Checking MongoDB from .env..."
python -c "from dotenv import load_dotenv; import os; from pymongo import MongoClient; load_dotenv(); uri=os.getenv('MONGODB_URI'); assert uri and 'replace-me' not in uri, 'MONGODB_URI is missing or still contains replace-me'; c=MongoClient(uri, serverSelectionTimeoutMS=5000); c.admin.command('ping'); print('MongoDB OK:', os.getenv('MONGODB_DATABASE', 'incident_logistics_ai'))"

Write-Host "Astra is checked at runtime. Make sure .env contains:"
Write-Host "ASTRA_DB_API_ENDPOINT=https://<db-id>-<region>.apps.astra.datastax.com"
Write-Host "ASTRA_DB_APPLICATION_TOKEN=AstraCS:..."
