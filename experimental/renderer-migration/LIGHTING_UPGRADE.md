# RoR graphics upgrade: shadow coverage + sky lighting (experimental)

This is an **incremental OGRE 1.x lighting improvement**, not an OGRE-Next port, not ray-traced GI, and not a complete PBR renderer. Changes are on `graphics-overhaul`; `master` is unchanged.

## Implemented in the branch

### Configurable directional shadow distance
- New archived integer CVar `gfx_shadow_distance`, default **350** world units, valid range **150–1500**.
- Graphics page: **PSSM shadow distance (restart terrain)**. The setting is read when PSSM shadows are configured; reload the terrain after changing it.
- The OGRE `SceneManager` PSSM far distance and directional extrusion are derived from the same distance.
- Higher distances increase coverage but distribute three cascades over a larger area, so near/far quality may suffer. Use 500–900 before trying 1500. Beware VRAM/graphics performance.

### Softening the terrain shader at high quality
- OGRE's stock-style terrain PSSM material generator uses 2x2 four-sample PCF on low/medium shadow quality (0–1).
- For high/ultra (2–3), the generated shader now uses a 3x3 nine-sample PCF kernel. This makes near shadow boundaries less blocky at the cost of up to five additional depth fetches per shaded terrain pixel.
- Requires terrain material/shader regeneration; reload the terrain after changing the quality option.
- Other RoR shader paths have a separate 2x2 PCF radius broadened from 0.3 to 0.75 texels in an earlier pass. This is an approximation; it is not contact-hardening sunlight.

### Optional environmental fill light
- When **Experimental natural sunlight (SkyX)** is enabled, the sun uses SkyX's sun gradient and dusk visibility curve; a low-intensity global ambient contribution is derived from SkyX's ambient gradient.
- The original directional diffuse and 0.35 ambient are restored when the setting is toggled off. Defaults remain unchanged (experiment off).
- This is simple sky fill, not ambient occlusion, probe-based irradiance, or bounced global illumination. Sunlight, sky conditions, and custom materials may respond differently.

### Test coverage
- A new standalone header `source/main/gfx/ShadowQualitySettings.h` contains the pure clamp, extrusion, and PCF width policy.
- `experimental/renderer-migration/test_shadow_quality.cpp` checks boundary values, legacy defaults, extended ranges, and quality tiers.
- `experimental/renderer-migration/CMakeLists.txt` registers the new test. Existing GitHub Actions workflow runs standalone tests on Linux and Windows when Actions are enabled.

## Recommended first in-game comparison
1. Build the `graphics-overhaul` branch and use **PSSM**, **Shadow quality 2**, **Shadow optimizations OFF**.
2. Compare distance 350 and 700 on the same map, camera angle, time of day, and vehicle. Reload the terrain after each adjustment.
3. Test sunlight OFF and ON on a SkyX terrain, especially morning and evening.
4. Compare a normal `*.otc` terrain with a custom-material `*.terrn2` terrain. Custom material paths bypass the built-in terrain PSSM generator and may have no dynamic shadow reception unless their own shaders implement it.
5. Check inside and outside vehicles; some actor meshes have shadow casting disabled by optimizations.
6. Compare near vs far shadow detail, terrain shader errors, shadow acne, detached shadows, and frame rate.

## Important limitations

- The full Windows game **has** compiled in GitHub Actions and a Windows preview has been published (for example, #77 at commit `ee57c0cc`). This validates compilation and packaging **for that historical commit only**. More recent graphics commits need their own successful Windows builds.
- The local Linux environment cannot run the Windows graphics application or inspect GPU screenshots. A successful Windows build is **not** a visual-quality, performance, or mod compatibility test.
- Standalone C++ tests and Python source-contract tests run in the renderer-migration CI workflow. The Windows game-build workflow additionally compiles a selection of managed-material, general-material and grass Cg shader entrypoints (provided the required runner dependencies are available). Generated Ogre terrain shader permutations and actual GPU output still require in-game checks.
- For repeatable map/vehicle/camera comparisons and acceptance criteria, see `GRAPHICS_TEST_MATRIX.md`.
- Custom map material support, stable CSM splits across all cameras, complete vehicle casting and terrain receiving, PBR, HDR tone mapping, SSAO, SSR, and true GI are **not finished**.
- A successful lighting overhaul also needs screenshots and frame-time measurements against baseline RoR on representative maps.
