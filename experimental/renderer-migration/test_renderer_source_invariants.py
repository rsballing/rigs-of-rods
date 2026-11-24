"""Source-contract checks for OGRE 1.x renderer regression fixes.

These are inexpensive static checks, NOT GPU shader compilation.
They complement the Windows full build and standalone C++ policy tests.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]


def load(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class RendererSourceContracts(unittest.TestCase):
    def test_terrain_shadow_uses_projected_depth(self):
        cpp = load("source/main/terrain/OgreTerrainPSSMMaterialGenerator.cpp")
        self.assertIn("newUV = newUV / newUV.w;", cpp)
        self.assertIn("depth >= newUV.z", cpp)
        self.assertNotIn("depth >= uv.z", cpp)

    def test_terrain_shadows_end_at_last_cascade(self):
        cpp = load("source/main/terrain/OgreTerrainPSSMMaterialGenerator.cpp")
        self.assertIn("Vector4 splitPoints(0, 0, 0, 0);", cpp)
        self.assertIn("i <= numTextures && i <= 4", cpp)
        self.assertIn("camDepth > pssmSplitPoints.", cpp)
        self.assertIn("ShaderHelper::getChannel(numTextures - 1)", cpp)

    def test_managed_shadows_end_at_last_cascade(self):
        cpp = load("source/main/gfx/ShadowManager.cpp")
        self.assertIn("for (int i = 0; i < 4; ++i)", cpp)
        self.assertIn("setManagedMaterialSplitPoints(pssmSetup->getSplitPoints());", cpp)
        shader = load("resources/managed_materials/shadows/pssm/on/pssm.cg")
        self.assertIn("else if (uv.z <= pssmSplitPoints.w)", shader)
        self.assertIn("shadowing = 1.0f;", shader)

    def test_managed_material_shadows_suppress_only_direct_lighting(self):
        shader = load("resources/managed_materials/shadows/pssm/on/pssm.cg")
        self.assertIn("shininess * 52) * shadowing;", shader)
        self.assertNotIn("0.3f + 0.7f * shadowing", shader.split("float4 lighting = ")[1])
        self.assertIn("ambient + lightDiffuse * lighting.y", shader)
        self.assertIn("lightSpecular * specularColour * lighting.z", shader)

    def test_default_shadow_caster_is_opaque(self):
        material = load("resources/managed_materials/shadows/pssm/on/shadows_depth.material")
        self.assertIn("fragment_program_ref PSSM/shadow_caster_ps", material)
        self.assertNotIn("fragment_program_ref PSSM/shadow_caster_alpha_ps", material)
        # The dedicated alpha caster remains available for materials that
        # explicitly bind an opacity mask; it is not safe as a global default.
        program = load("resources/managed_materials/shadows/pssm/on/depthshadows.program")
        self.assertIn("fragment_program PSSM/shadow_caster_alpha_ps cg", program)

    def test_depth_samplers_use_point_filtering_for_manual_pcf(self):
        generator = load("source/main/terrain/OgreTerrainPSSMMaterialGenerator.cpp")
        self.assertIn("tu->setTextureFiltering(TFO_NONE);", generator)
        material = load("resources/managed_materials/shadows/pssm/on/shadows.material")
        self.assertEqual(3, material.count("filtering point point none"))
        self.assertNotIn("filtering anisotropic anisotropic none", material)

    def test_quality_matches_shader_kernel_policy(self):
        header = load("source/main/gfx/ShadowQualitySettings.h")
        self.assertIn("if (quality >= 3) return 5;", header)
        self.assertIn("return quality >= 2 ? 3 : 2;", header)
        generator = load("source/main/terrain/OgreTerrainPSSMMaterialGenerator.cpp")
        self.assertIn("ShadowQualitySettings::TerrainPcfWidth(", generator)
        self.assertIn("SHADOW_SAMPLES NUM_SHADOW_SAMPLES_1D*NUM_SHADOW_SAMPLES_1D", generator)

    def test_vehicle_shadow_toggle_checks_optional_meshes(self):
        gfx_actor = load("source/main/gfx/GfxActor.cpp")
        self.assertIn("if (m_cab_entity != nullptr)", gfx_actor)
        self.assertIn("wheel.wx_scenenode->numAttachedObjects() > 0", gfx_actor)
        self.assertIn("rod.rod_scenenode->numAttachedObjects() > 0", gfx_actor)
        self.assertIn("if (fb != nullptr)", gfx_actor)

    def test_vehicle_shadows_restore_when_optimization_disabled(self):
        actor = load("source/main/physics/Actor.cpp")
        ui = load("source/main/gui/panels/GUI_GameSettings.cpp")
        self.assertIn("ShadowQualitySettings::ShouldCastVehicleShadows(", actor)
        self.assertIn("&& !App::gfx_reduce_shadows->getBool()", ui)
        self.assertIn("actor->GetGfxActor()->SetCastShadows(true);", ui)

    def test_runtime_reconfiguration_updates_splits(self):
        cpp = load("source/main/gfx/ShadowManager.cpp")
        self.assertIn("PSSM_Shadows.Quality = App::gfx_shadow_quality->getInt();", cpp)
        self.assertIn("pssmSetup->calculateSplitPoints(3, near_clip,", cpp)

    def test_renderer_startup_diagnoses_missing_plugin_dependencies(self):
        app = load("source/main/AppContext.cpp")
        self.assertIn("renderer_plugin_errors += fmt::format", app)
        self.assertIn('plugin_filename.find("RenderSystem_")', app)
        self.assertIn("if (!renderer_plugin_errors.empty())", app)
        self.assertIn("No render system plugin available", app)

    def test_windows_package_adds_legal_directx_dlls(self):
        workflow = load(".github/workflows/build-game.yml")
        script = load("tools/windows/Add-LegacyDirectX.ps1")
        self.assertIn("Get-AuthenticodeSignature", script)
        for dll in ("D3DX9_43.dll", "D3DCompiler_43.dll", "d3dx10_43.dll", "d3dx11_43.dll"):
            self.assertIn(dll, script)
        for step in (
            "Bundle signed Microsoft DirectX 9 runtime DLLs",
            "Upload redist folder",
            "Package and prerelease Windows graphics preview",
        ):
            self.assertIn(step, workflow)
        self.assertLess(
            workflow.index("Bundle signed Microsoft DirectX 9 runtime DLLs"),
            workflow.index("      - name: Upload build to itch.io", workflow.index("  build-msvc:")),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
