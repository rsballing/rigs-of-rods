# Validate the OGRE14 application-local Windows distribution.
# File/resource/PE checks only; this is NOT a GPU or shadow-rendering test.
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Directory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($Directory)

function Assert-File([string]$Relative) {
    if (-not (Test-Path -LiteralPath (Join-Path $root $Relative) -PathType Leaf)) {
        throw "Incomplete Windows package: missing $Relative"
    }
}

# The shader and UI packs may be shipped as ZIP archives or directories.
function Assert-ResourcePack([string]$Pack) {
    $folder = Join-Path $root "resources/$Pack"
    $zip = Join-Path $root "resources/$Pack.zip"
    if (-not ((Test-Path -LiteralPath $folder -PathType Container) -or
              (Test-Path -LiteralPath $zip -PathType Leaf))) {
        throw "Incomplete Windows package: missing resource pack $Pack (ZIP or folder)"
    }
}

function Assert-ResourceEntry([string]$Pack, [string]$Entry) {
    $folder = Join-Path $root "resources/$Pack"
    $unpacked = Join-Path $folder $Entry
    if (Test-Path -LiteralPath $unpacked -PathType Leaf) { return }

    $zip = Join-Path $root "resources/$Pack.zip"
    if (-not (Test-Path -LiteralPath $zip -PathType Leaf)) {
        throw "Missing resource: $Pack/$Entry"
    }

    # ZIP creators differ: entries may be stored with or without the pack
    # directory prefix. Match only a complete terminal path component.
    $archive = [System.IO.Compression.ZipFile]::OpenRead($zip)
    try {
        $target = $Entry.Replace('\', '/').TrimStart('/').ToLowerInvariant()
        $found = $false
        foreach ($item in $archive.Entries) {
            $name = $item.FullName.Replace('\', '/').ToLowerInvariant()
            if ($name -eq $target -or $name.EndsWith("/$target")) {
                $found = $true
                break
            }
        }
        if (-not $found) { throw "ZIP $Pack.zip missing required shader $Entry" }
    }
    finally {
        $archive.Dispose()
    }
}

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
            throw "$FileName is not Windows x64 (PE machine=0x$($machine.ToString('X4')))"
        }
    }
    finally {
        $reader.Dispose()
    }
}

foreach ($file in @('RoR.exe', 'plugins.cfg', 'OgreMain.dll')) {
    Assert-File $file
}
Assert-X64PortableExecutable 'RoR.exe'
Assert-X64PortableExecutable 'OgreMain.dll'

# Reject missing renderer plugins, but do not hardcode OGRE1.11's list.
# OGRE14 distributions may provide GL3Plus instead of legacy OpenGL or D3D9.
$config = @(Get-Content -LiteralPath (Join-Path $root 'plugins.cfg'))
$pluginFolder = @($config | Where-Object { $_ -match '^\s*PluginFolder\s*=' })
if ($pluginFolder.Count -ne 1) {
    throw 'Expected exactly one PluginFolder entry in plugins.cfg'
}
$enabledPlugins = @($config | Where-Object { $_ -match '^\s*Plugin\s*=\s*([^#;\s]+)\s*$' } |
    ForEach-Object { ($_ -split '=', 2)[1].Trim() })
$renderers = @($enabledPlugins | Where-Object { $_ -like 'RenderSystem_*' })
if ($renderers.Count -lt 1) { throw 'No enabled renderer plugin in plugins.cfg' }
foreach ($plugin in $enabledPlugins) {
    $file = "$plugin.dll"
    Assert-File $file
    Assert-X64PortableExecutable $file
}

# Legacy D3D9 plugins need the signed Microsoft helper DLLs that the workflow
# bundles. Do not require them if only D3D11 or GL3Plus are enabled.
if ($enabledPlugins -contains 'RenderSystem_Direct3D9') {
    foreach ($file in @('D3DX9_43.dll', 'D3DCompiler_43.dll')) {
        Assert-File $file
        Assert-X64PortableExecutable $file
    }
}

foreach ($pack in @('OgreCore', 'rtshader', 'managed_materials',
                    'fonts', 'mygui', 'wallpapers', 'icons')) {
    Assert-ResourcePack $pack
}

# Verify new OGRE14 RTShaderSystem terrain/cascade resources in both the
# uncompressed developer tree and the packed distribution.
foreach ($shader in @(
    'Shadow.material',
    'ShadowVolumeExtude.program',
    'TerrainSurface.glsl',
    'TerrainTransforms.glsl',
    'OgreUnifiedShader.h',
    'ShadowBlend.vert',
    'ShadowBlend.frag'
)) {
    Assert-ResourceEntry 'OgreCore' $shader
}
foreach ($shader in @(
    'SGXLib_IntegratedPSSM.glsl',
    'SGXLib_NormalMap.glsl',
    'FFPLib_Transform.glsl',
    'FFPLib_AlphaTest.glsl'
)) {
    Assert-ResourceEntry 'rtshader' $shader
}

# The existing managed vehicle materials still rely on their own legacy
# programs during migration. Never silently ship an empty resource pack.
Assert-ResourceEntry 'managed_materials' 'shadows/pssm/on/pssm.cg'

Write-Host "PASS: OGRE14 Windows x64 package, $($renderers.Count) renderers, $($enabledPlugins.Count) plugins, UI and shadow resources."
