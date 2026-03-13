# Deactivate any active virtual environment
if (Get-Command deactivate -ErrorAction SilentlyContinue) {
    deactivate
}
# Check if .venv already exists
if (-Not (Test-Path ".venv")) {
    Write-Host "Creating Python virtual environment..."
    python -m venv .venv
}
else {
    Write-Host ".venv already exists. Skipping creation."
}

./.venv/Scripts/Activate.ps1
$env:UV_INSECURE_HOST="pypi.org files.pythonhosted.org"
python -m pip install --upgrade pip
pip install uv
uv sync
cd ..
docker compose --profile deploy up -d --build
cd agent

$env:HTTPS_PROXY = "proxysg2.hydro.qc.ca:8081"