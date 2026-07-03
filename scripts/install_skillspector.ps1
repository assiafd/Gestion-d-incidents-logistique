param(
  [switch]$WithMcp
)

$ErrorActionPreference = "Stop"

$uv = Get-Command uv -ErrorAction SilentlyContinue
$pipx = Get-Command pipx -ErrorAction SilentlyContinue

if ($WithMcp) {
  $package = "skillspector[mcp] @ git+https://github.com/NVIDIA/skillspector.git"
}
else {
  $package = "git+https://github.com/NVIDIA/skillspector.git"
}

try {
  if ($uv) {
    if ($WithMcp) {
      uv tool install --force $package
    }
    else {
      uv tool install $package
    }
  }
  elseif ($pipx) {
    pipx install $package
  }
  else {
    Write-Error "Install uv or pipx first. SkillSpector requires Python 3.12+ and is installed from GitHub, not PyPI."
    exit 1
  }
}
catch {
  Write-Host ""
  Write-Host "SkillSpector installation failed." -ForegroundColor Red
  Write-Host "Common Windows cause: yara-python needs native build dependencies." -ForegroundColor Yellow
  Write-Host ""
  Write-Host "Recommended fixes:"
  Write-Host "1. Install Microsoft C++ Build Tools, then rerun this script."
  Write-Host "   winget install Microsoft.VisualStudio.2022.BuildTools --override `"--wait --add Microsoft.VisualStudio.Workload.VCTools --includeRecommended`""
  Write-Host ""
  Write-Host "2. Or avoid local Python builds and use Docker:"
  Write-Host "   .\scripts\run_skillspector_docker.ps1"
  Write-Host ""
  Write-Host "Original error:"
  Write-Host $_
  exit 1
}

$localBin = Join-Path $env:USERPROFILE ".local\bin"
if (Test-Path $localBin) {
  $env:Path = "$localBin;$env:Path"
}

$skillspector = Get-Command skillspector -ErrorAction SilentlyContinue
if (-not $skillspector) {
  Write-Host ""
  Write-Host "SkillSpector may be installed, but its executable is not in PATH." -ForegroundColor Yellow
  Write-Host "Add this directory to PATH if it exists:"
  Write-Host "  $localBin"
  exit 1
}

skillspector --help
