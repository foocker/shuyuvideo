$ErrorActionPreference = 'Stop'
$astraPython = Join-Path $PSScriptRoot '..\..\manimations\.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $astraPython)) {
    throw 'Missing tools\manimations\.venv\Scripts\python.exe. Create that environment first.'
}
& $astraPython -X utf8 (Join-Path $PSScriptRoot 'shuyu_astra.py') @args
exit $LASTEXITCODE
