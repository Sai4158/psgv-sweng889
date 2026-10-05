$ErrorActionPreference = 'Stop'
$projectPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $projectPython)) {
    Write-Error 'Create .venv with Python 3.11+ and install requirements.txt first. See README.md.'
    exit 1
}
& $projectPython (Join-Path $PSScriptRoot 'launch.py') @args
exit $LASTEXITCODE
