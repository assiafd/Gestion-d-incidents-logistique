$ErrorActionPreference = "Stop"

$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
  Write-Error "Docker is not installed or not in PATH. Install Docker Desktop first."
  exit 1
}

try {
  docker info | Out-Null
}
catch {
  Write-Error "Docker Desktop is not running. Start Docker Desktop, then rerun this script."
  exit 1
}

$existing = docker ps -a --filter "name=incident-logistics-mongo" --format "{{.Names}}"
if ($existing -contains "incident-logistics-mongo") {
  docker start incident-logistics-mongo | Out-Null
}
else {
  docker run -d --name incident-logistics-mongo -p 27017:27017 mongo:7 | Out-Null
}

Write-Host "MongoDB is available on mongodb://localhost:27017"
