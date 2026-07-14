# LM Studio Setup Script for Qwen2.5-Coder-3B
# Run this after the GGUF download completes
$ErrorActionPreference = 'Stop'

$gguf = "$env:USERPROFILE\Downloads\Qwen2.5-Coder-3B-Instruct-Q4_K_M.gguf"
$lms = "C:\Users\enock\AppData\Local\Programs\LM Studio\resources\app\.webpack\lms.exe"

if (-not (Test-Path $gguf)) {
    Write-Error "GGUF file not found at $gguf"
    exit 1
}

Write-Output "Importing model into LM Studio..."
& $lms import -y --user-repo bartowski/Qwen2.5-Coder-3B-Instruct-GGUF $gguf 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Import may have issues. Listing models..."
}
Write-Output "`nAvailable models:"
& $lms ls 2>&1 | Out-String

Write-Output "`nLoading model (try common names)..."
$possibleKeys = @("Qwen2.5-Coder-3B-Instruct", "qwen2.5-coder-3b-instruct", "bartowski/Qwen2.5-Coder-3B-Instruct-GGUF")
$loaded = $false
foreach ($key in $possibleKeys) {
    Write-Output "Trying key: $key"
    $result = & $lms load $key --yes 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Output "Loaded model with key: $key"
        $loaded = $true
        break
    }
}
if (-not $loaded) {
    Write-Error "Could not load model automatically. Open LM Studio UI and load manually."
    exit 1
}

Write-Output "`nModel is loaded. LM Studio local server should be at http://localhost:1234/v1"
Write-Output "Configure Continue.dev to use http://localhost:1234 as apiBase with provider lmstudio"
