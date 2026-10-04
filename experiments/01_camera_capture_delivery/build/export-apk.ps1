[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateScript({ (Test-Path -LiteralPath $_ -PathType Leaf) -and ([IO.Path]::GetExtension($_) -eq '.apk') })]
    [string] $ApkPath,

    [Parameter(Mandatory = $true)]
    [ValidateScript({ (Test-Path -LiteralPath $_ -PathType Leaf) -and ([IO.Path]::GetFileName($_) -eq 'verification.json') })]
    [string] $ReceiptPath,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[A-Za-z0-9][A-Za-z0-9_-]{0,79}$')]
    [string] $RunId,

    [string] $Distribution = 'Ubuntu'
)

$ErrorActionPreference = 'Stop'
$buildDirectory = $PSScriptRoot
$exporter = (Join-Path $buildDirectory 'export.py').Replace('\', '/')
$sourcePath = Join-Path $buildDirectory '..\app\main.py'
$apkLinux = (& wsl.exe -d $Distribution -- wslpath -u (Resolve-Path -LiteralPath $ApkPath).Path).Trim()
$receiptLinux = (& wsl.exe -d $Distribution -- wslpath -u (Resolve-Path -LiteralPath $ReceiptPath).Path).Trim()
$sourceLinux = (& wsl.exe -d $Distribution -- wslpath -u (Resolve-Path -LiteralPath $sourcePath).Path).Trim()
$outputRoot = (Join-Path (Resolve-Path (Join-Path $buildDirectory '..\..\..')).Path 'mobile deployment')
$outputLinux = (& wsl.exe -d $Distribution -- wslpath -u $outputRoot).Trim()
$arguments = @($exporter, $apkLinux, $receiptLinux, $sourceLinux, $outputLinux, $RunId)
& wsl.exe -d $Distribution -- python3 @arguments
if ($LASTEXITCODE -ne 0) {
    throw "APK verification or handoff failed with WSL exit code $LASTEXITCODE"
}
