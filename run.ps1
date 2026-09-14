$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$projectPython = Join-Path $PSScriptRoot '.venv/Scripts/python.exe'
if (Test-Path -LiteralPath $projectPython) {
    & $projectPython -m streamlit run app.py --server.address 127.0.0.1
} else {
    python -m streamlit run app.py --server.address 127.0.0.1
}
