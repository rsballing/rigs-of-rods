# Renderer modernization plan — preserve deformable RoR vehicles

Status: experimental development on `graphics-overhaul`. This plan is **not**
an announcement of a working new engine or a validated Windows build.

## Decision

**Improve the existing OGRE renderer before attempting a renderer replacement.**
The project currently pins `ogre3d/1.11.6.1@anotherfoxguy/stable` in
`conanfile.py`, with tightly coupled Ogre-based dependencies for MyGUI,
Caelum, terrain, shadows and other resources. Upstream OGRE 1.x has advanced
to the 14.6 series, but simply editing the dependency version is not a
working upgrade. All dependent modules and renderer plugins must be built
against a compatible OGRE ABI/API.

OGRE-Next is a separate API and needs a rendering integration/scene pipeline;
it cannot safely be used as a drop-in replacement for the current `RoR.exe`.
A homemade renderer would also need to recreate texture/material systems,
terrain, water, sky, UI overlays, clipping, shadows and GPU buffer lifetime.

## Phase 1 — current OGRE improvements (active)

- Retain the current OGRE version and the working physics simulation.
- Improve PSSM shadow setup and shader correctness, with quality/range controls.
- Keep custom terrain materials intact; stock PSSM receives shadows separately
  from map-specific shaders. Avoid forcing an incompatible shadow shader.
- Keep gameplay controls and settings accessible at different UI scales.
- Use `CabMeshSafety.h` to prevent a stretched old-style cab triangle from
  moving physics nodes that are shared by other triangles, including duplicates
  across UV seams. The test-only mesh frame remains renderer-neutral.
- Verify no NaN/Inf normals are uploaded on collapsed or degenerate faces.
- Preserve original vertex bindings, UV coordinates, submesh/material ordering,
  and the simulation's node positions.

### Current tested scope

The standalone cab-mesh safety helper compiles in C++11 Release mode and
passes a test covering shared nodes, duplicated UV seam vertices, area limits,
and malformed indices. This test is **not** an end-to-end RoR build or GPU test.
The Windows game and graphic effects must still be compiled and tested.

## Phase 2 — renderer-neutral vehicle geometry

- Extract position/normal/UV and triangle construction into a shared mesh-frame
  generator with explicit per-submesh material ranges.
- Compare the frame builder against current `FlexObj` and `FlexBody` on
  unchanged vehicles and recorded deformation frames.
- Add a switchable OGRE 1.x GPU-upload adapter using identical render data.
- Test position stability when vehicles travel far from the world origin.
- Do not revise the node-beam solver, collision model, or rig-file format.

## Phase 3 — upgrade OGRE 1.x in an isolated build

- Create a **separate upgrade branch** only after obtaining a compatible
  Ogre 14.x recipe/binaries and rebuilding all OGRE-dependent packages.
- Address compile/API changes one subsystem at a time: renderer plugins,
  material/shader system, terrain, batching, sky/water and MyGUI.
- Produce a second Windows preview, never overwrite the baseline binary.
- Compare each terrain/vehicle under identical camera, lighting and settings.

## Phase 4 — consider OGRE-Next or another renderer

Only after Phase 2 proves a renderer-neutral deformable-mesh pipeline:
build a prototype drawing one deformable vehicle with the replacement backend.
Migrate terrain, material shaders, skies, water, UI and scripting incrementally.
Do not remove current OGRE or migrate the whole game in one step.

## Required acceptance tests

| Area | Minimum acceptance condition |
| --- | --- |
| Existing content | Existing vehicles, maps, and mod ZIPs still load |
| Visual deformation | Cab/flexbody follows same node motion; no cross-panel pulls |
| UV seams | No gaps caused by moving an index that shares a physics node |
| Degenerate geometry | No non-finite vertex positions/normals or driver crashes |
| Material continuity | Cab front/back/transparency and submeshes render correctly |
| Shadows | Vehicle/trees/buildings cast, stock terrain receives when supported |
| Custom terrain | No replacement or corruption of custom materials |
| Performance | Measured FPS and frametimes on the same map/GPU/configuration |
| Windows distribution | Full ZIP, required DLLs/resources, UI buttons visible |
| Backward compatibility | Stock game remains separately installable |

For shadow checks, distinguish *caster* problems (a tree or building does not
enter a shadow map) from *receiver* problems (custom ground shader ignores PSSM).
Test Direct3D9, Direct3D11, and OpenGL only where available. Use `RoR.log`,
matched screenshots and `GRAPHICS_BUILD_INFO.txt` to identify builds.

### Build instructions for standalone regression tests

```sh
cmake -S experimental/renderer-migration -B build/renderer-migration -DCMAKE_BUILD_TYPE=Release
cmake --build build/renderer-migration --config Release
ctest --test-dir build/renderer-migration -C Release --output-on-failure
```

A passing standalone suite does not prove the full game compiled or that
shadows are visually correct. Publish a new `RoR.exe` only after the full
Windows build and live graphics acceptance tests.
