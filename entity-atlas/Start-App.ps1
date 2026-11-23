param([string]$Python = 'python', [string]$RuntimeDirectory = "$PSScriptRoot/runtime")
$ErrorActionPreference = 'Stop'
if (-not $PSBoundParameters.ContainsKey('RuntimeDirectory') -and (Test-Path -LiteralPath "$PSScriptRoot/.runtime-location")) {
    $RuntimeDirectory = (Get-Content -LiteralPath "$PSScriptRoot/.runtime-location" -Raw).Trim()
}
$pythonExecutable = (Get-Command $Python -ErrorAction Stop).Source
$modelFile = Join-Path $RuntimeDirectory 'qwen2.5-3b-instruct-q4_k_m.gguf'
$modelServer = Join-Path $RuntimeDirectory 'bin/llama-server.exe'
New-Item -ItemType Directory -Path "$PSScriptRoot/.logs" -Force | Out-Null
if ((Test-Path -LiteralPath $modelFile) -and (Test-Path -LiteralPath $modelServer)) {
    $env:ATLAS_LLM_BACKEND = 'llama'
    $modelHealth = $false
    try { $null = Invoke-WebRequest 'http://127.0.0.1:18080/health' -UseBasicParsing; $modelHealth = $true } catch {}
    if (-not $modelHealth) {
        $modelArguments = @('-m', ('"' + $modelFile + '"'), '--host', '127.0.0.1', '--port', '18080', '-c', '4096', '-t', '4', '-np', '1', '--jinja')
        $modelProcess = Start-Process -FilePath $modelServer -ArgumentList $modelArguments -WindowStyle Hidden -PassThru -RedirectStandardOutput "$PSScriptRoot/.logs/model.out.log" -RedirectStandardError "$PSScriptRoot/.logs/model.err.log"
        $modelProcess.Id | Set-Content "$PSScriptRoot/.logs/model.pid"
    }
}
$appReady = $false
try { $null = Invoke-WebRequest 'http://127.0.0.1:8765' -UseBasicParsing; $appReady = $true } catch {}
if (-not $appReady) {
    $appProcess = Start-Process -FilePath $pythonExecutable -ArgumentList @(('"' + "$PSScriptRoot/server.py" + '"')) -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput "$PSScriptRoot/.logs/app.out.log" -RedirectStandardError "$PSScriptRoot/.logs/app.err.log"
    $appProcess.Id | Set-Content "$PSScriptRoot/.logs/app.pid"
}
Write-Host 'Entity Atlas: http://127.0.0.1:8765'
Write-Host 'Model loading can take a minute. For Ollama instead, see README.'
Start-Process 'http://127.0.0.1:8765'
