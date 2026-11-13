# Makes a zip of the project to move to another computer.
# It leaves out the OpenAI key (.env), the virtual environment, node_modules and cached data.
# Run from anywhere:  powershell -ExecutionPolicy Bypass -File scripts\make_zip.ps1

$root = Split-Path -Parent $PSScriptRoot
$out = Join-Path $root 'release'
$stamp = Get-Date -Format 'yyyyMMdd-HHmm'
$stage = Join-Path $env:TEMP "reportpulse-stage-$stamp"
$zip = Join-Path $out "ReportPulse-$stamp.zip"

New-Item -ItemType Directory -Force $out, $stage | Out-Null

# /XD = folders to skip, /XF = files to skip. .env.example is kept, real key files are not.
robocopy $root $stage /E /NFL /NDL /NJH /NJS /NP `
    /XD node_modules .venv __pycache__ .pytest_cache dist release data .git .claude `
    /XF .env '*.env' '*.pyc' | Out-Null

$leaked = Get-ChildItem $stage -Recurse -Force -File | Where-Object { $_.Name -eq '.env' -or $_.Extension -eq '.env' }
if ($leaked) {
    Remove-Item $stage -Recurse -Force
    throw "Stopped: a key file would have been included: $($leaked[0].FullName)"
}

if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path (Join-Path $stage '*') -DestinationPath $zip
Remove-Item $stage -Recurse -Force

$size = [math]::Round((Get-Item $zip).Length / 1MB, 2)
Write-Host "Created $zip ($size MB). No .env, .venv, node_modules or data folders inside."
