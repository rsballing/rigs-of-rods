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
3. In Settings > Graphics, select PSSM, set shadow quality to 2 or 3, and disable `Shadow optimizations`. Reload terrain when changing the PSSM distance or quality.
4. On a SkyX-enabled terrain, try **Experimental natural sunlight (SkyX)** ON versus OFF. Default is OFF.
5. Compare the same terrain, vehicle, time of day, and camera settings with the official version. Several custom terrain materials do not implement PSSM shadow reception.
6. Report rendering glitches, missing shadows, shader compiler errors, and FPS differences with screenshots and `RoR.log`.

The preview was compiled by GitHub Actions; source-level unit tests are not a substitute for an in-game smoke test.
