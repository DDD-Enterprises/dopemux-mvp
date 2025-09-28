Param([int]$CovMin = $(If ($Env:HOOKS_COV_MIN) {$Env:HOOKS_COV_MIN} Else {90}))
Write-Host "[hooks] Running ruff, mypy, pytest --cov>=$CovMin% ..."
if (Get-Command ruff -ErrorAction SilentlyContinue) { ruff check . } else { Write-Host "[hooks] ruff not found" }
if (Get-Command mypy -ErrorAction SilentlyContinue) { if (Test-Path "src") { mypy src } else { try { mypy . } catch {} } } else { Write-Host "[hooks] mypy not found" }
if (Get-Command python -ErrorAction SilentlyContinue) {
  if (Test-Path "src") { python -m pytest --cov=src --cov-fail-under="$CovMin" -q } else { python -m pytest --cov=. --cov-fail-under="$CovMin" -q }
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
  if (Test-Path "src") { py -3 -m pytest --cov=src --cov-fail-under="$CovMin" -q } else { py -3 -m pytest --cov=. --cov-fail-under="$CovMin" -q }
} else { Write-Host "[hooks] Python not found" }
Write-Host "[hooks] Quality gates completed."
