# OGRE 14 migration — experimental branch

**Branch:** `ogre14-migration` (forked from `graphics-overhaul`)

**Status:** Dependency selection and initial source compatibility work only.
**No successful complete Windows executable or GPU validation is claimed.**

## Scope

This branch tests OGRE **14.5.2** without overwriting the existing
`graphics-overhaul` build. The baseline branch remains on OGRE 1.11.6.1,
where users report good directional sun shadows.

The original physics engine and its node-beam simulation are unchanged.
The deformation fixes in `FlexObj` / `CabMeshSafety.h` are inherited from
`graphics-overhaul` and must continue passing their tests.

## Dependencies

The RoR-specific Conan repository provides a package recipe for OGRE 14.5.2.
The earlier upstream `RigsOfRods/rigs-of-rods` `ogre-14` branch used a
different, older 14.x package and corresponding MyGUI/Caelum integrations.
This branch selects:

| Package | Baseline | Experimental |
| --- | --- | --- |
| OGRE | 1.11.6.1 | **14.5.2** |
| MyGUI | 3.4.0 | 3.4.3 |
| Caelum | 0.6.3.1 | 2022.08 |

The versions are **candidates, not verified as ABI-compatible binaries**.
Conan must resolve and build the full dependency graph using the selected
compiler/architecture. The project CMake requirement is OGRE 14, so it
cannot accidentally configure against legacy OGRE 1.11.

## Known compatibility work

The upstream `ogre-14` branch changed hundreds of files and removed or
replaced legacy terrain/shadow infrastructure. We cannot migrate by replacing
`OgreMain.dll` or only changing the Conan pin.

Important integration areas:

1. **UI:** adapt custom ImGui overlay and MyGUI GPU resources; the legacy
   `RenderOperation::useGlobalInstancingVertexBufferIsAvailable` member was
   removed in the upstream OGRE14 migration and is omitted here.
2. **Shadows:** keep the existing good directional sun shadow behavior as
   an explicit acceptance test, not an assumption. Legacy
   `ShadowManager.cpp`, PSSM shaders and custom terrain receivers may
   require a new RTShaderSystem-compatible implementation.
3. **Terrain/materials:** preserve custom `.terrn2` materials, texture
   blending and correct shadow reception. A shadow-casting object without
   a receiving material will still appear shadowless.
4. **Deformable meshes:** retain each physics-node position and stable
   UV/submesh bindings; test both `FlexObj` cabs and `FlexBody` deforming
   assets on real mods.
5. **Plugin packaging:** confirm the actual OGRE14 renderer plugins,
   shader compilers and runtime dependencies in a full Windows archive.
   Do not move DLLs from an OGRE1.11 distribution into OGRE14.

## Build and regression checks

The existing `.github/workflows/build-game.yml` workflow attempts a Windows
build on pushes, but a *passed* full Windows build and packaged `.exe` have
not been observed yet. The separate standalone geometry test suite is
independent of OGRE and must continue passing.

To attempt a local game build with the project's Conan provider:

```powershell
conan remote add rigs-of-rods-deps https://nexus.anotherfoxguy.com/repository/rigs-of-rods/ -f
cmake . -GNinja -DCMAKE_BUILD_TYPE=Release -Bbuild -DCMAKE_PROJECT_TOP_LEVEL_INCLUDES=cmake/conan_provider.cmake -DCMAKE_INSTALL_PREFIX=redist -DCREATE_CONTENT_FOLDER=ON
cmake --build build --target install
```

On GitHub, view the `Build game` workflow for `ogre14-migration`. If the
build fails, examine the *first* compiler/Conan error. Do not claim the
renderer is working because only the dependency version number changed.

## Release criteria

Do **not** distribute the OGRE14 branch as the ordinary RoR graphics preview
until all the following are verified:

- Game starts on Windows 11 with correct plugins and font/UI resources.
- Custom graphics preset buttons remain visible and usable.
- The directional sun shadows users already like are visually preserved.
- Trees and buildings cast onto stock terrain; custom shader limitations
  are reported clearly.
- Vehicles do not glitch on collision, deformation, UV seams or far travel.
- Existing maps and vehicle ZIPs load with the same or better fidelity.
- Frame-time and VRAM comparisons on the same GPU and content are recorded.
- The original `graphics-overhaul` installation remains unaffected.

**Fallback:** `graphics-overhaul` (OGRE 1.11.6.1) until the above pass.

## Implementation checkpoint — November 25, 2026

A draft pull request is available at
https://github.com/rsballing/rigs-of-rods/pull/2 (base: `graphics-overhaul`).
It is **not** ready to merge.

Beyond the initial dependency pin, the migration now contains source ports for:

- OGRE14 `TerrainMaterialGeneratorA` and the map-specific custom terrain
  material generator, with the legacy OGRE1.11 terrain generator excluded
  from compilation on this branch.
- Matching `ShadowManager` terrain-receiver type while retaining the
  previous PSSM cascade setup for later visual verification.
- Scene-node transforms for the primary terrain directional sun, SkyX and
  Caelum sun directions, vegetation/map spot and point lights, vehicle
  flares and animated beacons.
- Scene-node-backed vehicle video cameras, mirrors, cubemap reflections,
  and water reflection/refraction cameras.
- Modern FlexBody vertex reorganization API and preserved UV-seam-safe cab
  vertex mapping and normal checks.
- MyGUI dashboard string conversion compatibility and a Direct3D11
  warning-texture startup workaround based on the upstream OGRE14
  experimental discussion.
- Static preflight contract checks for these APIs on Windows/Linux.

The upstream experimental minimal OGRE14 port
(https://github.com/RigsOfRods/rigs-of-rods/pull/3418) was **closed without
merge** and documented Direct3D11 and PSSM problems. Its patches are useful
references, but do not establish that this fork compiles or runs.

**Outstanding blocking verification:** no complete dependency-resolution,
Windows C++ compilation, packaged `RoR.exe`, actual GPU shadow screenshot,
or deformable-mesh crash test has been verified for the new branch. The
connector currently exposes no completed workflow-run result for the draft
PR commit. Preserve the fallback and do not distribute this branch as a
finished graphics upgrade.

Next compiler-driven work: resolve build errors one at a time; confirm the
new Caelum/MyGUI/OGRE dependency graph; test Cg shader and PSSM runtime
behavior; compare directional sun shadows against the 1.11 baseline; then
run the crash/UV seam and mod compatibility matrix. Only after those
checks should improved lighting be introduced on top of the renderer.
