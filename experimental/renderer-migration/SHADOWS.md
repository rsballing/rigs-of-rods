# RoR shadow rendering findings (experimental branch)

## Symptoms and code paths

1. **Some vehicle body panels missing shadows:** RoR toggles entire actor shadow casting through `Actor.cpp` / `GfxActor::SetCastShadows` when `gfx_reduce_shadows` is enabled. Certain props/materials also have independent shadow flags. Try turning off **Shadow optimizations** in Graphics. Transparent meshes and customized materials need separate review.
2. **Sharp-edged shadows:** RoR has 2x2 PCF depth comparisons in several paths: `resources/materials/general.cg`, `resources/materials/grass.cg`, `resources/managed_materials/shadows/pssm/on/pssm.cg`, and `resources/rtshader/SGXLib_IntegratedPSSM.{cg,hlsl,glsl}`. Their sampling radius was 0.3 texture pixels and is changed to 0.75 in this branch to produce a slightly wider filtered transition. This is not physically-based area-light filtering, and quality depends on resolution and light angle. It still uses 4 texture fetches.
3. **Dull PSSM material lighting:** `resources/managed_materials/shadows/pssm/on/pssm.cg` accumulated exactly 4 lit depth comparisons, then divided their sum by 5, limiting the lit shadow factor to 0.8. Corrected to divide by 4. This fixes a specific numerical bug; not a comprehensive lighting or materials overhaul.
4. **Missing terrain shadows:** RoR's stock terrain material generator configures PSSM shadow reception through `ShadowManager::updateTerrainMaterial`. However, `TerrainGeometryManager::configureTerrainDefaults` bypasses this stock material generator when the terrain defines a custom material. Such maps require explicitly shadow-capable terrain shaders/materials. PSSM is also limited to 350 world units in `ShadowManager::processPSSM`, so far terrain should not be expected to have dynamic shadows. A generic map-wide override would risk breaking custom terrain materials.
5. **General flatness:** SkyX's main directional light previously used an ambient gradient as its diffuse color. The branch adds an opt-in natural sunlight experiment, but PBR materials, improved sky/ambient lighting and color grading are not yet complete.

## Changes in this pass

- `pssm.cg`: fix 4-tap shadow denominator from 5 to 4, and widen PCF sampling to 0.75.
- `general.cg`, `grass.cg`: widen PCF radius to 0.75 while preserving 4 samples.
- RTShader `SGXLib_IntegratedPSSM.{cg,hlsl,glsl}`: same radius in all three backends.

## What to test in a full RoR build

1. Use a **PSSM** shadow mode with 2/3 shadow quality and **Shadow optimizations OFF**.
2. Compare stock branch vs `graphics-overhaul` for a bright surface, a vehicle parked on an open plain and a tree/terrain feature near the camera.
3. Test a mod with a **custom** `terrn2` material separately from a stock `otc` terrain. Note whether shadows disappear only on custom-material maps.
4. Compare vehicle cab, flexbody, props and wheels while inside vs outside the vehicle.
5. Compare soft-edge quality and artifacts at 1 m, 25 m, 100 m and beyond 350 m. The current range is only 350 m.
6. Test both shader backends available on your operating system. Watch for shader compile errors, acne, detached shadows, over-blurred shadow borders and performance.
7. Enable experimental natural sunlight only after verifying shadow behavior; compare with option OFF.

**Testing status:** Shader source changes were inspected for matching PCF functions and four texture fetches. No complete RoR game build or runtime screenshot validation has been performed in this pass, so the apparent quality improvement is a hypothesis until tested.

**Next engineering targets:** diagnose missing terrain shadow reception per material, add controlled PSSM range and soft-shadow quality settings, then introduce more robust shadows/material rendering on a modern renderer.
