# Portable diagnostic for an extracted Rigs of Rods Windows graphics preview.
# Read-only by default. Never sends data over the network and never changes
# the user's graphics settings. Use -SaveReport to write a local text report.
[CmdletBinding()]
param(
    [string]$GameDirectory = $PSScriptRoot,
    [switch]$TestBinaryLoad,
    [switch]$SaveReport
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = [IO.Path]::GetFullPath($GameDirectory)
$report = [System.Collections.Generic.List[string]]::new()
function Note([string]$line) {
    $report.Add($line)
    Write-Host $line
}
function Check([string]$name, [bool]$isPresent) {
    if ($isPresent) { Note "[PASS] $name" }
    else { Note "[FAIL] $name" }
}

Note 'Rigs of Rods - Windows graphics preview diagnostics'
Note "Run date: $((Get-Date).ToUniversalTime().ToString('yyyy-MM-dd HH:mm:ss')) UTC"
Note "Game folder: $root"

$buildInfo = Join-Path $root 'GRAPHICS_BUILD_INFO.txt'
if (Test-Path $buildInfo -PathType Leaf) {
    foreach ($line in (Get-Content -LiteralPath $buildInfo)) { Note $line }
} else { Note 'Build metadata: not included in this older preview' }

$expected = @(
    'RoR.exe', 'plugins.cfg', 'OgreMain.dll',
    'RenderSystem_Direct3D9.dll', 'RenderSystem_Direct3D11.dll',
    'RenderSystem_GL.dll', 'D3DX9_43.dll', 'D3DCompiler_43.dll',
    'resources/managed_materials.zip'
)
foreach ($file in $expected) {
    Check "File: $file" (Test-Path -LiteralPath (Join-Path $root $file) -PathType Leaf)
}

$configPath = Join-Path $root 'plugins.cfg'
if (Test-Path $configPath -PathType Leaf) {
    $config = @(Get-Content -LiteralPath $configPath)
    $pluginDir = @($config | Where-Object { $_ -match '^\s*PluginFolder\s*=' })
    Note ("Plugin folder setting: " + $(if ($pluginDir.Count -eq 1) { $pluginDir[0].Trim() } else { 'INVALID (expected one)' }))
    $configured = @($config | Where-Object {
        $_ -match '^\s*Plugin\s*=\s*RenderSystem_[^#;\s]+\s*$'
    } | ForEach-Object { ($_ -split '=', 2)[1].Trim() })
    foreach ($renderer in @('RenderSystem_Direct3D9', 'RenderSystem_Direct3D11', 'RenderSystem_GL')) {
        Check "Enabled renderer: $renderer" ($renderer -in $configured)
    }
}

try {
    $adapters = @(Get-CimInstance Win32_VideoController -ErrorAction Stop)
    foreach ($adapter in $adapters) {
        Note ("Graphics adapter: {0} (driver version {1})" -f $adapter.Name, $adapter.DriverVersion)
    }
} catch {
    Note 'Graphics adapter details: unavailable via Windows Management Instrumentation'
}

$mods = Join-Path ([Environment]::GetFolderPath('MyDocuments')) 'My Games\Rigs of Rods\mods'
if (Test-Path $mods -PathType Container) {
    $packages = @(Get-ChildItem $mods -File -Filter '*.zip' -ErrorAction SilentlyContinue)
    Note "User mods: $($packages.Count) ZIP packages found under Documents\My Games\Rigs of Rods\mods"
} else {
    Note 'User mods directory: not found in Documents (may be stored elsewhere)'
}

if ($TestBinaryLoad) {
    $exe = Join-Path $root 'RoR.exe'
    if (Test-Path -LiteralPath $exe -PathType Leaf) {
        try {
            Note 'Testing executable static imports (no graphics window created)...'
            $proc = Start-Process -FilePath $exe -ArgumentList '--ci-load-check' -WorkingDirectory $root -PassThru -Wait
            Check "RoR.exe --ci-load-check exit code 0" ($proc.ExitCode -eq 0)
        } catch {
            Note "[FAIL] Could not start RoR.exe: $($_.Exception.Message)"
        }
    }
}

Note 'Note: Static package checks cannot verify rendering or GPU shader output.'
Note 'For a visual test, enable the experimental preset, restart the map, and compare identical scenes.'
if ($SaveReport) {
    $reportPath = Join-Path ([Environment]::GetFolderPath('Desktop')) 'RoR-Graphics-Diagnostics.txt'
    $report | Set-Content -LiteralPath $reportPath -Encoding UTF8
    Note "Local report saved to Desktop: RoR-Graphics-Diagnostics.txt"
}
