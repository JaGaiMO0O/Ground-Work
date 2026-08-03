# Shim. The playbook's Appendix E calls this handoff; the implementation is
# handoff.py. Kept so the documented interface stays true on any platform.
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command python3 -ErrorAction SilentlyContinue).Source }
if (-not $py) { Write-Error "python 3 is required but was not found on PATH"; exit 1 }
& $py (Join-Path $PSScriptRoot "handoff.py") @args
exit $LASTEXITCODE
