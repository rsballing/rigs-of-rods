# Windows graphics-preview build: installation and contents

The `graphics-overhaul` branch is **experimental**. It builds against the original OGRE renderer; it is **not** an OGRE-Next port, an HDR/PBR lighting overhaul, or a verified improvement across every map.

## Windows dependencies

### Visual C++ runtime requirement

The portable GitHub ZIP does not bundle the MSVC runtime. A binary import
audit of the compiled Windows release found `MSVCP140.dll`,
`VCRUNTIME140.dll`, and `VCRUNTIME140_1.dll` are required by `RoR.exe`
and its OGRE renderer plugins.

If Windows reports a missing `MSVCP140.dll` or `VCRUNTIME140*.dll`,
install Microsoft's latest supported **Visual C++ Redistributable x64**:

https://learn.microsoft.com/en-us/cpp/windows/latest-supported-vc-redist

Do **not** download individual MSVC DLLs from unofficial DLL websites.
The itch.io package declares the prerequisite in `tools/windows/.itch.toml`,
but a direct GitHub ZIP installation may need it installed separately.


Windows GitHub Actions builds now use `tools/windows/Add-LegacyDirectX.ps1` **after** installing the game but **before** packaging the portable release. That script downloads the official `Microsoft.DXSDK.D3DX` **9.29.952.8** NuGet package and copies the four unmodified, Microsoft-signed 64-bit release libraries directly beside `RoR.exe`:

- `D3DX9_43.dll` — legacy Direct3D9 utility API
- `D3DCompiler_43.dll` — shader compiler used by the D3DX family
- `d3dx10_43.dll` — required by `cgD3D10.dll`
- `d3dx11_43.dll` — required by `cgD3D11.dll`

An import-table audit of the Windows release also found `D3DCOMPILER_47.dll` (Windows 11 normally provides it) and the Microsoft Visual C++ runtime dependencies, which are handled through the regular system redistributable rather than bundled here.

It also includes the available Microsoft package LICENSE/NOTICE and a source attribution under `licenses/Microsoft.DXSDK.D3DX`. Microsoft permits these particular binaries to be distributed *application-local* with the application, not relicensed under GPL. **Do not commit extracted third-party DLL binaries to the source repository** or substitute debug/x86 DLLs.

Official source and legal terms: https://www.nuget.org/packages/Microsoft.DXSDK.D3DX/9.29.952.8

For existing older builds without the DLLs, install the official DirectX End-User Runtimes (June 2010):
https://www.microsoft.com/en-us/download/details.aspx?id=8109

## Why the preview contains fewer maps and vehicles

The CMake/CI build uses `CREATE_CONTENT_FOLDER=ON` and includes only repository *starter content* (for example `agora.zip`, `dafsemi.zip`, and `simple2-terrain.zip`). It does **not** include third-party vehicle and map collections or the separate official content packs. The preview is therefore not meant to replace your existing mod library.

On Windows, keep existing custom `*.zip` vehicle/terrain mods under:

```text
Documents\My Games\Rigs of Rods\mods
```

If needed, obtain additional content packs from the RoR official repository/forums, extract the **outer content-pack archive** into the `mods` directory, and restart RoR. Do not unpack individual vehicle ZIPs unless the mod author explicitly instructs it. See https://docs.rigsofrods.org/gameplay/installing-content/

## Optional offline diagnostic (no upload)

The new ZIP includes `RoR-Graphics-Diagnostics.ps1` and
`GRAPHICS_BUILD_INFO.txt` beside `RoR.exe`. To examine renderer configuration,
DLL presence, graphics driver version and installed mod ZIP count, open Windows
PowerShell **in the extracted game directory** and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\RoR-Graphics-Diagnostics.ps1
```

This script reads local settings but **does not launch the game, change
settings, or transmit personal data**. Optional `-SaveReport` writes a
local `RoR-Graphics-Diagnostics.txt` on your Desktop. Optional
`-TestBinaryLoad` runs the new no-window binary dependency check;
it is skipped automatically when the extracted preview predates that feature.
Do not run scripts from untrusted downloads.

## Testing the experimental graphics

1. Extract the *entire* Windows release ZIP, not just `RoR.exe`.
2. Choose Direct3D9 if that is the known working renderer for your GPU. The branch also enables available Direct3D11 and OpenGL render plugins in `plugins.cfg`. You should not need to edit `plugins.cfg` for the new release if all files are present and the fix is working.
3. In **Settings > Graphics**, press **Apply experimental graphics preset**. This sets PSSM shadows, High shadow quality (3×3 PCF), 700-unit shadow distance, and disables Shadow optimizations. On a terrain already using SkyX, it also turns on experimental natural sunlight; it intentionally does not force SkyX on incompatible maps. **Reload the terrain or restart RoR** to recreate its PSSM cascade textures and generated materials. (The preview build containing this button must have compiled successfully.)
4. For smoother shadows, select **Ultra** quality (5×5 PCF, 25 depth samples). This costs substantially more GPU time than **High** (3×3, 9 samples) and Low/Medium (2×2, 4 samples). Try High first.
5. On a SkyX-enabled terrain, toggle **Experimental natural sunlight (SkyX)** ON versus OFF, especially near sunset. The effect is optional and will not be apparent on maps that use another sky mode.
6. Compare the **same terrain, vehicle, time of day, renderer, and camera angle** with the official version. Some custom terrain shaders bypass the built-in PSSM receiver and cannot receive dynamic shadows without changes to those materials. The content pack itself does not contain upgraded lighting code.
7. Report rendering glitches, missing shadows, shader compiler errors, and FPS differences with screenshots and `RoR.log`.

### Renderer tests and limitations

The Windows GitHub Actions workflow compiles and links the complete C++ game and produces a portable release. The independent renderer regression workflow compiles pure C++ policy tests on Windows/Linux and runs static checks for shadow-source invariants; these do **not** compile all generated Cg/HLSL shaders on a GPU.

The branch now includes fixes for projected shadow-depth comparisons, cascade far-limit clipping, stale shadow-split setup, vehicle shadow-state restoration, and point-sampled manual PCF. These are incremental corrections to OGRE 1.x, **not** complete physically based rendering, global illumination, or a new engine. In-game visual quality and performance still require direct testing on representative maps and hardware.

## Reproducible A/B benchmark procedure

The preview now has two buttons in **Settings > Graphics**:
**Apply experimental graphics preset** and **Restore stock graphics preset**.
The latter resets the archived shadow technique to PSSM, shadow quality to 2,
shadow distance to 350, shadow optimizations ON, and experimental sunlight OFF.
The experimental preset selects PSSM, quality 2, 700-unit shadow distance,
optimizations OFF, and SkyX sunlight ON when supported by that terrain.

**Restart terrain after changing the PSSM settings**. An old terrain still has
old cascade splits, textures, and shaders until it is reloaded. Compare the
same game build, same map, same vehicle, same location and camera, same time
of day and resolution in both states. Do not use different content packs for
the comparison.

| Scenario | Expected result | What to check |
| --- | --- | --- |
| Daytime, stock terrain material, PSSM ON | Stronger ground shadows and longer range | Tree trunks, buildings, wheels and vehicle contact shadows |
| 700-unit preview PSSM vs 350-unit stock PSSM | More distant shadow coverage | Shadow cutoff in the distance; FPS cost |
| SkyX noon with natural sunlight toggled | Directional light follows SkyX sun color gradient | Vehicle and terrain brightness; avoid washed-out white |
| SkyX sunrise/sunset | Direct light smoothly fades with sun elevation | Harsh direct lighting at/after sunset, ambient remaining visible |
| Map with custom terrain shader | May not receive new PSSM shadows | Vehicles still cast shadows; no crashes or shader errors |
| Cabin/driver camera then outside camera | Shadows restored when optimization OFF | Wheels, beams, vehicle body |
| Multiple vehicles on one map | No shadow toggling crash | Vehicles lacking optional wheel/cab/prop meshes |
| Direct3D9 with 2010 DirectX app-local DLLs | Startup succeeds without modifying plugins.cfg | Check RoR.log on any missing plugin or GPU errors |

For each run record: exact preview tag, GPU, renderer (D3D9/D3D11/OpenGL),
screen resolution, selected preset, map and vehicle names, FPS before/after,
and a screenshot from the same camera location. If the renderer fails,
attach the corresponding `RoR.log` and the relevant OGRE log error.

**Limitations:** CI can verify C++ compilation, unit checks, file presence,
and a published Windows ZIP; it cannot establish that the shaders visibly
render correctly on your GPU. Those observations require an actual Windows
graphics session.
