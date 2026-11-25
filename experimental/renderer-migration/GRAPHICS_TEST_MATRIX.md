# Windows graphics-preview regression and visual A/B test matrix

This is a **release acceptance protocol**, not a claim that the preview has passed these tests.
Rigs of Rods uses OGRE 1.x; GitHub Actions compilation cannot judge GPU output, perceived quality or map compatibility.

## Reproducible control conditions

- Install official RoR and the preview in **separate extracted directories**. Keep the same content library in `Documents\My Games\Rigs of Rods\mods`.
- Do not compare the limited starter-only content build against a larger 3 GB/full content pack as if it were a renderer regression.
- Use one GPU driver and display resolution; use the **same rendering API** (start with Direct3D9 if the machine needs `D3DX9_43.dll`).
- Set the **same map, vehicle, spawn, camera, direction, lighting/time-of-day, quality, and screenshot resolution** in both builds.
- Capture three screenshots after terrain load: stationary vehicle at 5 m, roadside tree shadows at 40 m, distant terrain at 200-500 m. Preserve `RoR.log`.
- Measure FPS only after a warm-up pass; use five 60-second repeats with identical camera movement. Compare median frame time, not the best single FPS.

## Test cases and pass criteria

| ID | Test | Criteria |
|---|---|---|
| WIN-01 | Fresh extraction and first launch with no handwritten changes to `plugins.cfg` | Game reaches main menu without plugin error |
| WIN-02 | Direct3D9 with application-local `D3DX9_43.dll` and `D3DCompiler_43.dll` | Both runtime DLLs loaded or available, no missing-module startup |
| WIN-03 | Direct3D11 renderer selection (if supported by the GPU) | Launches with no missing `d3dx11_43.dll` / shader compiler error |
| WIN-04 | OpenGL renderer selection | Launches; reports correct active renderer, no plugin loading failures |
| PSSM-01 | High quality (2), distance 350, optimizations OFF | Cab, tires, props, terrain receive/cast shadows where supported |
| PSSM-02 | Same camera; change range 350 → 700 → 1500 with terrain reload | Cascade boundaries move, no missing adjacent bands or full-screen black shadow |
| PSSM-03 | Shadow quality 0,1,2,3 with terrain reload | 2×2,2×2,3×3,5×5 policy and no shader compile errors; expect higher cost at 3 |
| PSSM-04 | Stand at shadow-map cascade transition | No pronounced seams, edge smearing, or visibly darker strip |
| PSSM-05 | Camera inside/outside vehicle; toggle shadow optimizations | Expected shadows return when optimizations are disabled |
| MAP-01 | Stock terrain, sunny midday | Terrain lit; no black surfaces, no missing mesh geometry |
| MAP-02 | Custom `.terrn2` and custom materials | No shader parse errors or lighting breakage; log whether custom material supports PSSM |
| MAP-03 | Trees, grass and partially transparent vegetation | No prominent edge artifacts or missing trunks; alpha geometry correct |
| SKY-01 | Experimental natural sunlight OFF vs ON at dawn/noon/dusk on SkyX terrain | Daylight gradient changes without sudden sun or ambient jumps |
| MAP-04 | Existing full mods library | Vehicle and terrain selections match user's installed content; no assets modified |
| PERF-01 | Shadow quality 2, range 350 | Record median frame time and GPU; investigate repeated >20% slowdown against same settings |
| PERF-02 | Quality 3, range 1500 | Record GPU VRAM pressure, stalls and frame time; no device-loss crash |

## What CI proves and what it does not

- **Standalone C++ CTest**: deformable mesh bounds/degenerate triangle policy and sky/PCF settings math.
- **Python source-contract checks**: expected shader/sampler wiring and regression guards. These are static checks, not rendering.
- **NVIDIA Cg compiler entrypoint checks**: validates the checked shader functions in listed profiles, but does not cover all dynamically generated terrain permutations or real GPU drivers.
- **Windows full build and package checks**: prove the executable compiled and expected files are in the archive, *not* that the program launches on a particular GPU.
- **Real gameplay**: required to accept any claim of improved visual quality or reliable performance.

## Bug-report template

Record the **build tag and commit**, Windows version, GPU name/driver, Direct3D9/11/OpenGL, map name, vehicle, screenshot(s), shadow type/quality/range, shadow optimizations state, SkyX experiment state, and reproducing steps. Include the relevant `RoR.log` segment and whether the same failure occurs in official RoR. If possible include a paired screenshot of the same scene.

Use `tools/windows/RoR-Graphics-Diagnostics.ps1` from a preview that includes it to collect local plugin/DLL checks. The script reports configuration and optionally writes a text report; it cannot judge rendering quality.
