# Add the Microsoft-approved application-local x64 D3DX redistributables.
# Source: Microsoft.DXSDK.D3DX 9.29.952.8 (NuGet, published by Microsoft).
# These proprietary DLLs belong in the release ZIP beside RoR.exe, NOT in
# the GPL-licensed source tree. See the Microsoft package LICENSE and NOTICE.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$DestinationDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$version = '9.29.952.8'
$packageId = 'microsoft.dxsdk.d3dx'
$uri = "https://api.nuget.org/v3-flatcontainer/$packageId/$version/$packageId.$version.nupkg"
$destination = [System.IO.Path]::GetFullPath($DestinationDirectory)
if (-not (Test-Path (Join-Path $destination 'RoR.exe'))) {
    throw "RoR.exe must already exist in the install directory: $destination"
}

$work = Join-Path ([System.IO.Path]::GetTempPath()) ("ror-directx-" + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $work -Force | Out-Null
try {
    $nupkg = Join-Path $work 'Microsoft.DXSDK.D3DX.nupkg'
    $extracted = Join-Path $work 'package'
    Write-Host "Downloading official Microsoft.DXSDK.D3DX $version package..."
    Invoke-WebRequest -Uri $uri -OutFile $nupkg
    [System.IO.Compression.ZipFile]::ExtractToDirectory($nupkg, $extracted)

    $runtimeFolder = Join-Path $extracted 'build/native/release/bin/x64'
    foreach ($dll in @('D3DX9_43.dll', 'D3DCompiler_43.dll')) {
        $source = Join-Path $runtimeFolder $dll
        if (-not (Test-Path $source -PathType Leaf)) {
            throw "Official package is missing $dll in the x64 release folder"
        }
        $signature = Get-AuthenticodeSignature -FilePath $source
        if ($signature.Status -ne [System.Management.Automation.SignatureStatus]::Valid -or
            -not $signature.SignerCertificate -or
            $signature.SignerCertificate.Subject -notmatch 'Microsoft') {
            throw "Expected valid Microsoft Authenticode signature for $dll; actual status: $($signature.Status)"
        }
        Copy-Item -Path $source -Destination (Join-Path $destination $dll) -Force
        Write-Host "Added $dll from the official x64 release package."
    }

    $legalDir = Join-Path $destination 'licenses/Microsoft.DXSDK.D3DX'
    New-Item -ItemType Directory -Path $legalDir -Force | Out-Null
    foreach ($legalName in @('LICENSE', 'NOTICE')) {
        $source = Join-Path $extracted $legalName
        if (Test-Path $source -PathType Leaf) {
            Copy-Item $source (Join-Path $legalDir $legalName) -Force
        }
    }
    @(
        'Microsoft.DXSDK.D3DX 9.29.952.8',
        'Copyright Microsoft Corporation. The DLLs are redistributed unmodified, application-local, with RoR.exe.',
        'See the package license and notices; package source:',
        'https://www.nuget.org/packages/Microsoft.DXSDK.D3DX/9.29.952.8',
        'These DLLs are not licensed as part of Rigs of Rods GPL source code.'
    ) | Set-Content -Path (Join-Path $legalDir 'README.txt') -Encoding UTF8

    foreach ($dll in @('D3DX9_43.dll', 'D3DCompiler_43.dll')) {
        if (-not (Test-Path (Join-Path $destination $dll) -PathType Leaf)) {
            throw "Packaging verification failed: $dll is missing"
        }
    }
}
finally {
    Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
}
