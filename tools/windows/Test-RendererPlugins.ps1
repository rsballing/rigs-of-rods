# Windows preflight for OGRE renderer plugins.
# Validates the actual Windows loader dependency chain, not just file names.
# This does NOT create an OGRE scene or test GPU rendering.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [string]$DistributionDirectory
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$distribution = (Resolve-Path -LiteralPath $DistributionDirectory).Path

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class RoRWin32PluginProbe {
    [DllImport("kernel32.dll", CharSet=CharSet.Unicode, SetLastError=true, EntryPoint="LoadLibraryExW")]
    public static extern IntPtr LoadLibraryEx(string path, IntPtr file, UInt32 flags);

    [DllImport("kernel32.dll", SetLastError=true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool FreeLibrary(IntPtr module);
}
'@

# LOAD_LIBRARY_SEARCH_DLL_LOAD_DIR | LOAD_LIBRARY_SEARCH_DEFAULT_DIRS.
# LoadLibraryEx recursively resolves dependencies beside each plugin, plus
# standard Windows system DLL directories. No global PATH mutation required.
$flags = [uint32]0x1100
$renderers = @('RenderSystem_Direct3D9', 'RenderSystem_Direct3D11', 'RenderSystem_GL')
$available = @()
$failures = @()

foreach ($name in $renderers) {
    $file = Join-Path $distribution "$name.dll"
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
        $failures += "$name : DLL not packaged"
        continue
    }

    $module = [RoRWin32PluginProbe]::LoadLibraryEx($file, [IntPtr]::Zero, $flags)
    if ($module -eq [IntPtr]::Zero) {
        $code = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
        $explanation = [ComponentModel.Win32Exception]::new($code).Message
        $failures += "$name : Windows error $code ($explanation)"
        Write-Warning "Could not load $name : Windows error $code ($explanation)"
        continue
    }
    try {
        $available += $name
        Write-Host "Windows loader OK: $name"
    }
    finally {
        if (-not [RoRWin32PluginProbe]::FreeLibrary($module)) {
            Write-Warning "Could not unload $name after dependency probe"
        }
    }
}

if ($available.Count -eq 0) {
    throw "No render system DLL can be loaded by Windows. $($failures -join '; ')"
}

# Also probe common renderer support plugins. Failure is diagnosed in logs,
# without blocking the release if at least one renderer is available.
foreach ($name in @('Codec_FreeImage', 'Plugin_ParticleFX', 'Plugin_OctreeSceneManager', 'Plugin_CgProgramManager', 'Caelum')) {
    $file = Join-Path $distribution "$name.dll"
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
        Write-Warning "Optional OGRE plugin not packaged: $name"
        continue
    }
    $module = [RoRWin32PluginProbe]::LoadLibraryEx($file, [IntPtr]::Zero, $flags)
    if ($module -eq [IntPtr]::Zero) {
        $code = [System.Runtime.InteropServices.Marshal]::GetLastWin32Error()
        Write-Warning "OGRE support plugin $name could not load (Windows error $code)"
    }
    else {
        try { Write-Host "Windows loader OK: $name" }
        finally { [void][RoRWin32PluginProbe]::FreeLibrary($module) }
    }
}

Write-Host "Preflight passed: $($available.Count) of $($renderers.Count) Windows render systems load their dependencies."
