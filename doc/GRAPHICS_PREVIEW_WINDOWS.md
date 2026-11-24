# Windows graphics-preview build: installation and contents

The `graphics-overhaul` branch is **experimental**. It builds against the original OGRE renderer; it is **not** an OGRE-Next port, an HDR/PBR lighting overhaul, or a verified improvement across every map.

## Windows dependencies

Windows GitHub Actions builds now use `tools/windows/Add-LegacyDirectX.ps1` **after** installing the game but **before** packaging the portable release. That script downloads the official `Microsoft.DXSDK.D3DX` **9.29.952.8** NuGet package and copies these unmodified, Microsoft-signed 64-bit release libraries directly beside `RoR.exe`:

- `D3DX9_43.dll`
- `D3DCompiler_43.dll`

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
