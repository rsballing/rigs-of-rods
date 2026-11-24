# Renderer migration: phase 1 — deformable vehicle geometry

**Experimental.** The code in this directory is standalone, not connected to RoR's main build. It does **not** replace OGRE or improve the game's graphics yet.

## Why this is needed

RoR uses OGRE directly in `source/main/AppContext.cpp` for startup and in `source/main/gfx/GfxScene.cpp` for scene management. `source/main/physics/flex/FlexObj.cpp` calculates vehicle mesh positions and normals from the simulation's nodes, then uploads them to `Ogre::HardwareVertexBuffer`.

A renderer migration needs to preserve this deformation without tying the calculation to one graphics library.

`DeformableMeshFrame.h` is a C++11 prototype of a renderer-neutral mesh snapshot with:
- Positions relative to a moving origin
- Vertex normals and UV coordinates
- Indexed triangles
- Validation of node and triangle indices
- Zero-safe normals for degenerate triangles

A future OGRE/OGRE-Next adapter can transform and upload this data to its own GPU buffers.

## Standalone tests

With CMake:

```sh
cmake -S experimental/renderer-migration -B build/renderer-migration
cmake --build build/renderer-migration
ctest --test-dir build/renderer-migration --output-on-failure
```

Or from this directory:

```sh
g++ -std=c++11 -Wall -Wextra -Werror -pedantic test_mesh_frame.cpp -o test_mesh_frame
./test_mesh_frame
```

## Not yet implemented

- Connecting the prototype to `FlexObj`, `FlexBody`, or `GfxActor`
- Multiple materials / cab submesh ranges
- RoR's existing overstretched-triangle collapse rule
- GPU resource ownership and upload interface
- OGRE-Next rendering, PBR materials, or upgraded lighting
- Dynamic vehicle skin detachment and fracture
- End-to-end RoR build and runtime tests

## Suggested migration sequence

1. Add a read-only RoR node-data adapter, keeping OGRE as the active renderer.
2. Compare old and new vertex generation (including normals, deformation and submeshes) on real vehicles.
3. Add a switchable mesh upload interface with an OGRE 1.x backend.
4. Prototype an OGRE-Next backend for one deforming vehicle while preserving the original physics.
5. Migrate scene, materials, terrain, sky, water, UI, and scripting only after the prototype is validated.

All changes should remain on the `graphics-overhaul` branch until tested. This folder is isolated so it cannot break a normal RoR build.

License: GPL-3.0-or-later, compatible with the upstream RoR project.



## 2026-11-24 experimental lighting pass

A separate, opt-in SkyX sun-lighting experiment now exists in the main RoR source:

- `source/main/gfx/SkyLightingMath.h`: testable 0..1 channel clamping and smooth twilight fade.
- `source/main/gfx/SkyXManager.cpp`: uses the pre-existing SkyX `mSunGradient` for the directional light when enabled; the legacy diffuse color remains the default.
- `source/main/system/CVar.cpp` and `Application.{h,cpp}`: archived Boolean CVar `gfx_natural_sunlight`, default `false`.
- `source/main/gui/panels/GUI_GameSettings.cpp`: Graphics tab checkbox visible when SkyX is selected.
- `test_sky_lighting.cpp`: checks nighttime, daytime, twilight hue, monotonicity, non-finite inputs, and channel bounds.
- `.github/workflows/renderer-migration-tests.yml`: standalone CMake tests on Linux and Windows when GitHub Actions is enabled.

### How to try the lighting experiment

Build RoR from the `graphics-overhaul` branch using its **normal** build instructions and dependencies (the full game is not built by the standalone CMake target). Open Graphics settings, select SkyX, then enable **Experimental natural sunlight (SkyX)**.

The setting is OFF by default. Turning it off restores the legacy SkyX directional diffuse colors; the experiment does not modify the physics engine or existing map files. Visual results will vary across terrain materials and render backends.

### What has been tested

The standalone CMake suite was built and passed locally with GCC in Release mode. The two test executables cover deformable mesh frame calculations and sunlight interpolation. This validates the numerical helpers, **not** an entire RoR build, runtime integration, lighting appearance, driver compatibility, or an OGRE-Next migration.

### Limitations and next checks

- No physically-based shading, HDR, global illumination, or new render engine yet.
- The sunset color is clamped to the range expected by the legacy renderer and is **not** physically calibrated.
- RoR's built-in SkyX gradients, lightmaps, and mod-specific materials may behave differently.
- Existing ambient lighting remains terrain-defined, so nighttime may retain ambient illumination.
- Validate a full game build on Windows; visually compare the option on multiple terrains, vehicles, and DirectX/OpenGL renderers before deciding whether to enable it by default.
- GitHub Actions may need to be enabled manually on a newly forked repository.

