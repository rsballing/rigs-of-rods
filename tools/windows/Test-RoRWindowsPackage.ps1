# Validate the application-local Windows distribution before uploading it.
# This is a FILE/PACKAGING smoke test, not a GPU rendering test.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Directory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($Directory)

$mandatoryFiles = @(
    'RoR.exe',
    'plugins.cfg',
    'OgreMain.dll',
    'RenderSystem_Direct3D9.dll',
    'RenderSystem_Direct3D11.dll',
    'RenderSystem_GL.dll',
    'Codec_FreeImage.dll',
    'Plugin_CgProgramManager.dll',
    'Plugin_OctreeSceneManager.dll',
    'Plugin_ParticleFX.dll',
    'Caelum.dll',
    'D3DX9_43.dll',
    'D3DCompiler_43.dll',
    'resources/managed_materials.zip',
    'resources/managed_materials/shadows/pssm/on/pssm.cg',
    'resources/rtshader.zip'
)

foreach ($relative in $mandatoryFiles) {
    $fullPath = Join-Path $root $relative
    if (-not (Test-Path -LiteralPath $fullPath -PathType Leaf)) {
        throw "Incomplete Windows package: $relative not found"
    }
}

# Reject x86 binaries copied from the NuGet package's other architecture.
# The x64 game cannot load an x86 renderer or x86 DirectX runtime, and
# a file-existence check alone would mistakenly accept that distribution.
function Assert-X64PortableExecutable([string]$FileName) {
    $fullPath = Join-Path $root $FileName
    $stream = [System.IO.File]::OpenRead($fullPath)
    $reader = [System.IO.BinaryReader]::new($stream)
    try {
        if ($reader.ReadUInt16() -ne 0x5A4D) { throw "$FileName is not a DOS MZ executable" }
        $stream.Position = 0x3c
        $peOffset = $reader.ReadInt32()
        if ($peOffset -lt 0x40 -or $peOffset -ge $stream.Length - 6) {
            throw "$FileName has an invalid PE header offset"
        }
        $stream.Position = $peOffset
        if ($reader.ReadUInt32() -ne 0x00004550) {
            throw "$FileName is missing the PE signature"
        }
        $machine = $reader.ReadUInt16()
        if ($machine -ne 0x8664) {
            throw "$FileName is not a Windows x64 executable (PE machine=0x$($machine.ToString('X4')))"
        }
    }
    finally {
        $reader.Dispose()
    }
}
foreach ($file in @('RoR.exe', 'RenderSystem_Direct3D9.dll',
                   'RenderSystem_Direct3D11.dll', 'RenderSystem_GL.dll',
                   'D3DX9_43.dll', 'D3DCompiler_43.dll')) {
    Assert-X64PortableExecutable $file
}
Write-Host "Windows PE validation passed: game, renderers and legacy DirectX DLLs are all x64."

$config = Get-Content -LiteralPath (Join-Path $root 'plugins.cfg')
$pluginFolder = @($config | Where-Object { $_ -match '^\s*PluginFolder\s*=' })
if ($pluginFolder.Count -ne 1) { throw 'Expected exactly one PluginFolder entry in plugins.cfg' }
$requiredRenderers = @('RenderSystem_Direct3D9', 'RenderSystem_Direct3D11', 'RenderSystem_GL')
foreach ($plugin in $requiredRenderers) {
    $exactPattern = '^\s*Plugin\s*=\s*' + [regex]::Escape($plugin) + '\s*$'
    if (-not @($config | Where-Object { $_ -match $exactPattern }).Count) {
        throw "Missing or disabled renderer in plugins.cfg: $plugin"
    }
}

# Verify that each explicitly enabled plugin has its DLL in the same directory,
# which is the application-local plugin directory for the Windows distribution.
$enabledPlugins = @($config | Where-Object { $_ -match '^\s*Plugin\s*=\s*([^#;\s]+)\s*$' } |
    ForEach-Object { ($_ -split '=', 2)[1].Trim() })
foreach ($plugin in $enabledPlugins) {
    if (-not (Test-Path -LiteralPath (Join-Path $root "$plugin.dll") -PathType Leaf)) {
        throw "Enabled plugin in plugins.cfg has no matching DLL: $plugin.dll"
    }
}
Write-Host "Windows package validated: $($mandatoryFiles.Count) required files; $($enabledPlugins.Count) configured plugins."
