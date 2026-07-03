param(
  [ValidateSet("auto", "local", "docker")]
  [string]$Mode = "auto",
  [string]$OutputDir = "reports",
  [switch]$UseLlm
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
Set-Location $ProjectRoot

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$scanTargets = @(
  @{
    Label = "vulnerable-agents"
    Target = ".\src\logistics_agent\vulnerable_agents.py"
    Format = "markdown"
    Output = "$OutputDir\skillspector-vulnerable-agents.md"
  },
  @{
    Label = "secure-agents"
    Target = ".\src\logistics_agent"
    Format = "markdown"
    Output = "$OutputDir\skillspector-secure-agents.md"
  },
  @{
    Label = "full-project"
    Target = "."
    Format = "json"
    Output = "$OutputDir\skillspector-full-report.json"
  }
)

function Write-SkillSpectorStatus {
  param(
    [string]$Status,
    [string]$Reason,
    [string]$RecommendedCommand
  )

  $content = @"
# SkillSpector Execution Status

Date: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Status: $Status

## Reason

$Reason

## Recommended next command

````powershell
$RecommendedCommand
````

## Expected reports

- reports/skillspector-vulnerable-agents.md
- reports/skillspector-secure-agents.md
- reports/skillspector-full-report.json

## Notes

SkillSpector official source: https://github.com/NVIDIA/skillspector
On Windows, local installation can fail because `skillspector` depends on `yara-python`, which may require native C++ build tools.
Docker mode avoids local `yara-python` compilation but requires Docker Desktop to be running.
"@

  Set-Content -LiteralPath "$OutputDir\skillspector-execution-status.md" -Value $content -Encoding UTF8
}

function Invoke-LocalSkillSpector {
  $skillspector = Get-Command skillspector -ErrorAction SilentlyContinue
  $uvx = Get-Command uvx -ErrorAction SilentlyContinue
  $uv = Get-Command uv -ErrorAction SilentlyContinue

  if (-not $skillspector -and -not $uvx -and -not $uv) {
    throw "Neither skillspector nor uv/uvx is available. Install uv or use Docker mode."
  }

  foreach ($scan in $scanTargets) {
    $scanArgs = @("scan", $scan.Target, "--format", $scan.Format, "--output", $scan.Output)
    if (-not $UseLlm) {
      $scanArgs += "--no-llm"
    }
    Write-Host "SkillSpector local scan: $($scan.Label)"
    if ($skillspector) {
      & skillspector @scanArgs
    }
    elseif ($uvx) {
      $uvxArgs = @("--from", "git+https://github.com/NVIDIA/skillspector.git", "skillspector") + $scanArgs
      & uvx @uvxArgs
    }
    else {
      $uvArgs = @("tool", "run", "--from", "git+https://github.com/NVIDIA/skillspector.git", "skillspector") + $scanArgs
      & uv @uvArgs
    }
  }
}

function Invoke-DockerSkillSpector {
  $docker = Get-Command docker -ErrorAction SilentlyContinue
  if (-not $docker) {
    throw "Docker is not installed or not in PATH."
  }

  try {
    docker info | Out-Null
  }
  catch {
    throw "Docker is installed, but Docker Desktop daemon is not running. Start Docker Desktop and retry."
  }

  Write-Host "Building SkillSpector Docker image from NVIDIA GitHub repository..."
  docker build -t skillspector https://github.com/NVIDIA/skillspector.git

  foreach ($scan in $scanTargets) {
    $target = ($scan.Target -replace "^\.\\", "./") -replace "\\", "/"
    $output = $scan.Output.Replace("\", "/")
    $scanArgs = @("run", "--rm", "-v", "${ProjectRoot}:/scan", "skillspector", "scan", $target, "--format", $scan.Format, "--output", $output)
    if (-not $UseLlm) {
      $scanArgs += "--no-llm"
    }
    Write-Host "SkillSpector Docker scan: $($scan.Label)"
    & docker @scanArgs
  }
}

try {
  if ($Mode -eq "local") {
    Invoke-LocalSkillSpector
  }
  elseif ($Mode -eq "docker") {
    Invoke-DockerSkillSpector
  }
  else {
    try {
      Invoke-LocalSkillSpector
    }
    catch {
      Write-Host "Local SkillSpector failed: $_" -ForegroundColor Yellow
      Write-Host "Trying Docker mode..."
      Invoke-DockerSkillSpector
    }
  }

  Write-SkillSpectorStatus `
    -Status "completed" `
    -Reason "SkillSpector scans completed successfully." `
    -RecommendedCommand ".\scripts\skillspector_scan.ps1 -Mode auto"
}
catch {
  $message = $_.Exception.Message
  Write-SkillSpectorStatus `
    -Status "blocked" `
    -Reason $message `
    -RecommendedCommand ".\scripts\skillspector_scan.ps1 -Mode docker"
  Write-Error $message
  exit 1
}
