# Rigs of Rods — physics, collision, tire, graphics and audio quality

Status: experimental source work, **not a validated performance or game release**.
Working branch: `physics-quality-upgrade` (based on `graphics-overhaul`).
The incomplete OGRE 14 work remains isolated on `ogre14-migration`.

## What the original comparison gets wrong

RoR is **not entirely single threaded**. `ActorManager::UpdatePhysicsSimulation`
already calls `ThreadPool::Parallelize` for per-actor force computation and
inter-actor collision jobs; its physics loop uses `PHYSICS_DT = 0.0005f`,
or 2,000 substeps per simulated second. Another thread is used for the
simulation task. The existing general worker pool detects available CPU
threads, subject to a configurable limit.

RoR also has node-and-beam wheels and adjustable pressure beams for
`wheels2`. Its `SoundScriptManager` already supports layered samples,
pitch/gain modulation and spatial audio through the existing audio backend.
These do not prove parity with BeamNG, but rewriting them blindly is not
a sound starting point.

## Changes in this branch

1. **Reuse task vectors** in the 2 kHz force and collision phases. The
   existing task filtering, actor order and full phase synchronization remain.
2. **Inline up to eight worker task handles** in
   `ThreadPool::Parallelize`, avoiding one handle-vector allocation on
   the common 1–9 actor path. The overflow path retains arbitrary actor
   counts, concurrent callers, and the strict completion barrier.
3. **Reuse collision-partner scratch storage** inside each
   `PointColDetector`, swapping the lists on change rather than allocating
   and copying them at every 0.5 ms substep.
4. **Conservatively schedule collision components**: build connected
   components of *all* actors with intersecting bounding boxes. Collision
   jobs within a component execute sequentially to prevent simultaneous
   writes to the same node forces and contact flags. Independent components
   still execute in parallel; scenes without any overlap keep the original
   parallel fast path. This does not solve tunneling, deep interpenetration,
   or network-authoritative crash synchronization.
5. **Standalone unit tests** cover scheduler completion barriers for
   0/1/2/4/8/9/10/12/32 jobs; concurrent callers; and overlap components
   including transitive chains and shared non-job recipients. The tests
   build without OGRE and do not substitute for a full-game test.

## Performance validation (still required)

Measure an actual Windows build **before and after** the changes, using the
same hardware, map, camera, vehicles and graphics settings:

| Scenario | Measure | Must verify |
| --- | --- | --- |
| One vehicle idling/driving | wall time per 2 kHz step, FPS | no regression vs. baseline |
| Four separated vehicles | CPU utilization/physics time | independent actors scale across cores |
| Four vehicles colliding | wall time, node stability, damage | no NaNs, hangs, or shared-force races |
| Eight/twelve vehicle stress | timestep overrun %, FPS | overflow path works |
| High-speed head-on/side impact | penetration, deformation, replays | identify clipping and sticking |
| Low/high tire pressure | contact, slip, sidewall response | pressure and tires remain functional |
| Vehicle sound at idle/load/damage | sound transitions and channels | no missing sounds or audio glitches |

The 0.5 ms timestep is a **simulation resolution**, not a promise the PC
can compute the simulation in under 0.5 ms of real time.

## Next engineering workstreams

**Collision physics:** After profiling, fix remaining triangle/point
tunneling and near-zero-velocity sticking; test friction models for
high-speed impacts and make collision-group scheduling finer-grained if
large groups serialize too much. Online multiplayer still needs a
consistent network-authoritative contact model.

**Tires:** Preserve deformable `wheels2` and pressure beams. Build a
measured, surface-dependent traction/contact-patch model using tire
load, slip ratio/angle, temperature if modeled, and pressure. Tune
against repeatable steering/braking tests rather than applying arbitrary
friction multipliers.

**Graphics:** Complete OGRE 14 Windows compilation and validate native
PSSM shadow resources, mod materials, flex meshes, trees and water. Then
add PBR materials, exposure/tonemapping and better postprocessing behind
performance presets.

**Audio:** Retain the sound-script asset pipeline. Add load-dependent
engine layers, tire/surface contact sounds, impact intensity, drivetrain
and suspension audio, and spatial mixing, subject to mod compatibility
and available sound assets.

**Release gate:** successful Windows build, tests, gameplay performance
measurements, visual/audio inspection, and explicit comparison with the
fallback before merging this physics branch into the OGRE 14 branch.
