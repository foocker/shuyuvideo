$ErrorActionPreference = 'Stop'
$shuyuPython = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $shuyuPython)) {
    $shuyuPython = 'python'
}
# PowerShell 5 turns redirected native stderr into ErrorRecords. Python test
# and render tools legitimately write progress there; use their exit status.
$ErrorActionPreference = 'Continue'
& $shuyuPython -X utf8 (Join-Path $PSScriptRoot 'scripts\shuyu.py') @args
$shuyuExitCode = $LASTEXITCODE
exit $shuyuExitCode
