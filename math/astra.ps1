$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot '..\shuyu.ps1') math @args
exit $LASTEXITCODE
