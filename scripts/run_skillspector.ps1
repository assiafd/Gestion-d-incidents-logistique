param(
  [string]$OutputDir = "reports",
  [switch]$NoLlm
)

$script = Join-Path $PSScriptRoot "skillspector_scan.ps1"
if ($NoLlm) {
  & $script -Mode local -OutputDir $OutputDir
}
else {
  & $script -Mode local -OutputDir $OutputDir -UseLlm
}
