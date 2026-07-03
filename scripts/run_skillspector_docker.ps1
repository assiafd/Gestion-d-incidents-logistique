param(
  [string]$OutputDir = "reports",
  [switch]$UseLlm
)

$script = Join-Path $PSScriptRoot "skillspector_scan.ps1"
if ($UseLlm) {
  & $script -Mode docker -OutputDir $OutputDir -UseLlm
}
else {
  & $script -Mode docker -OutputDir $OutputDir
}
