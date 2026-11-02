# Start the local agent on Windows. Never expose port 8765 to the internet.
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)
if (-not (Get-Command py -ErrorAction SilentlyContinue)) {
  throw "Python launcher 'py' not found. Install Python 3.10+ first."
}
py -m pip install -r requirements.txt
if (-not $env:DESKTOP_CONTROL_TOKEN -or $env:DESKTOP_CONTROL_TOKEN.Length -lt 24) {
  $bytes = New-Object byte[] 32
  $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
  try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
  $env:DESKTOP_CONTROL_TOKEN = [BitConverter]::ToString($bytes).Replace("-", "")
  Write-Host "Generated temporary token (copy into the ESP32 sketch; keep it private):"
  Write-Host $env:DESKTOP_CONTROL_TOKEN
}
if (-not $env:DESKTOP_CONTROL_HOST) { $env:DESKTOP_CONTROL_HOST = "127.0.0.1" }
Write-Host "Agent binding to $env:DESKTOP_CONTROL_HOST port 8765"
py windows_agent/server.py
