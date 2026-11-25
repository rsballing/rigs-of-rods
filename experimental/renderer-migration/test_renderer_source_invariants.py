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

    def test_vehicle_shadow_receiver_normalizes_interpolated_normals(self):
        shader = load("resources/managed_materials/shadows/pssm/on/pssm.cg")
        receiver = shader.split("void shadow_receiver_ps(", 1)[1]
        self.assertIn(
            "surfaceNormal = normal * rsqrt(max(dot(normal, normal), 1e-8f));",
            receiver,
        )
        self.assertIn("dot(surfaceNormal, lightVec)", receiver)
        self.assertIn("dot(surfaceNormal, halfAngle)", receiver)
        self.assertNotIn("lit(dot(normal, lightVec)", receiver)

    def test_manual_pssm_shadow_samplers_use_point_filter_and_white_border(self):
        # Bilinear depth filtering before a manual depth comparison creates
        # false shadows; clamping the shadowmap to its last texel smears
        # dark streaks beyond the cascade projection.
        for filename, expected in (
            ("resources/materials/general.material", 9),
            ("resources/materials/grass.material", 3),
        ):
            text = load(filename)
            import re
            units = re.findall(
                r"texture_unit shadow_tex[012]\s*\{(.*?)\}",
                text,
                flags=re.DOTALL,
            )
            self.assertEqual(expected, len(units), filename)
            for unit in units:
                self.assertIn("content_type shadow", unit)
                self.assertIn("tex_address_mode border", unit)
                self.assertIn("tex_border_colour 1 1 1 1", unit)
                self.assertIn("filtering none", unit)
                self.assertNotIn("tex_address_mode clamp", unit)

    def test_general_and_grass_shaders_share_live_pssm_splits(self):
        general = load("resources/materials/general.program")
        grass = load("resources/materials/grass.material")
        shared = load("resources/managed_materials/shadows/pssm/on/shared/pssm_shared.program")
        manager = load("source/main/gfx/ShadowManager.cpp")
        resources = load("source/main/resources/ContentManager.cpp")
        self.assertEqual(2, general.count("shared_params_ref pssm_params"))
        self.assertEqual(1, grass.count("shared_params_ref pssm_params"))
        self.assertNotIn("param_named pssmSplitPoints float4 1.0 187 774 10000.0", general)
        self.assertNotIn("param_named pssmSplitPoints float4 1.0 187 774 10000.0", grass)
        self.assertIn("shared_param_named pssmSplitPoints float4", shared)
        self.assertIn('getSharedParameters("pssm_params")', manager)
        self.assertIn('setNamedConstant("pssmSplitPoints", splitPoints)', manager)
        # Material scripts parse in non-PSSM mode as well: the shared
        # parameter definition must still be registered before they load.
        shared_registration = resources.index('"shadows/pssm/on/shared"')
        pssm_branch = resources.index("if (App::gfx_shadow_type->getEnum<GfxShadowType>()")
        self.assertLess(shared_registration, pssm_branch)

    def test_managed_shadows_end_at_last_cascade(self):
        cpp = load("source/main/gfx/ShadowManager.cpp")
        self.assertIn("for (int i = 0; i < 4; ++i)", cpp)
        self.assertIn("setManagedMaterialSplitPoints(pssmSetup->getSplitPoints());", cpp)
        shader = load("resources/managed_materials/shadows/pssm/on/pssm.cg")
        self.assertIn("else if (uv.z <= pssmSplitPoints.w)", shader)
        self.assertIn("shadowing = 1.0f;", shader)

    def test_general_and_grass_shadows_stop_at_last_cascade(self):
        general = load("resources/materials/general.cg")
        grass = load("resources/materials/grass.cg")
        # These shaders are used by specialized map materials, not the
        # default managed receiver or terrain PSSM generator.
        self.assertEqual(2, general.count("else if (IN.uv.z <= pssmSplitPoints.w)"))
        self.assertIn("else if (uv.z <= pssmSplitPoints.w)", grass)
        self.assertEqual(2, general.count(
            "diffuseTex.rgb * ambient + (diffC + specC) * shadowing;"))
        self.assertNotIn("0.25f + 0.75f * shadowing", general)

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

    def test_live_deformable_cab_normals_match_area_weighted_mesh_policy(self):
        cpp = load("source/main/physics/flex/FlexObj.cpp")
        section = cpp.split("Vector3 FlexObj::UpdateMesh()", 1)[1].split(
            "Vector3 FlexObj::UpdateFlexObj()", 1
        )[0]
        self.assertIn("const Vector3 face_normal = edge1.crossProduct(edge2);", section)
        self.assertIn("!std::isfinite(doubled_area)", section)
        self.assertIn("doubled_area <= 1e-10f", section)
        collapsed = section.split("if (doubled_area > m_s_ref[i])", 1)[1].split("}", 1)[0]
        self.assertIn("continue;", collapsed)
        self.assertIn("m_vertices[m_indices[i*3]].normal += face_normal;", section)
        self.assertNotIn("v1=v1/s;", section)

    def test_vehicle_shadow_toggle_checks_optional_meshes(self):
        gfx_actor = load("source/main/gfx/GfxActor.cpp")
        self.assertIn("if (m_cab_entity != nullptr)", gfx_actor)
        self.assertIn("i < wheel.wx_scenenode->numAttachedObjects()", gfx_actor)
        self.assertIn("i < rod.rod_scenenode->numAttachedObjects()", gfx_actor)
        self.assertIn("wheel.wx_scenenode->getAttachedObject(i)->setCastShadows(value)", gfx_actor)
        self.assertIn("rod.rod_scenenode->getAttachedObject(i)->setCastShadows(value)", gfx_actor)
        self.assertNotIn("wheel.wx_scenenode->getAttachedObject(0)->setCastShadows(value)", gfx_actor)
        self.assertNotIn("rod.rod_scenenode->getAttachedObject(0)->setCastShadows(value)", gfx_actor)
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
        self.assertIn('"[RoR Graphics Preview] PSSM quality="', cpp)
        self.assertIn('Ogre::LogManager::getSingleton().logMessage(diag.str());', cpp)

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
        validation = load("tools/windows/Test-RoRWindowsPackage.ps1")
        self.assertIn("Validate Windows renderer and shader distribution", workflow)
        self.assertIn("./tools/windows/Test-RoRWindowsPackage.ps1", workflow)
        self.assertIn("'RenderSystem_Direct3D9.dll'", validation)
        self.assertIn("'RenderSystem_Direct3D11.dll'", validation)
        self.assertIn("'RenderSystem_GL.dll'", validation)
        self.assertIn("'resources/managed_materials/shadows/pssm/on/pssm.cg'", validation)
        self.assertLess(
            workflow.index("Validate Windows renderer and shader distribution"),
            workflow.index("      - name: Upload redist folder", workflow.index("  build-msvc:")),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
