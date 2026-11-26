#!/usr/bin/env python3
"""Static contract tests for OGRE 14 migration scaffolding.

These checks do NOT compile RoR or validate visuals. The full game build,
shadow compatibility and deforming GPU-buffer behavior require separate tests.
"""
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[2]


def source(path):
    return (ROOT / path).read_text(encoding="utf-8")


class Ogre14MigrationContract(unittest.TestCase):
    def test_modern_dependency_graph_selected(self):
        deps = source("conanfile.py")
        cmake = source("cmake/DependenciesConfig.cmake")
        for ref in (
            "ogre3d/14.5.2@anotherfoxguy/stable",
            "mygui/3.4.3@anotherfoxguy/stable",
            "ogre3d-caelum/2022.08@anotherfoxguy/stable",
        ):
            self.assertIn(ref, deps)
        self.assertNotIn("ogre3d/1.11.6.1@", deps)
        self.assertIn("find_package(OGRE 14 REQUIRED", cmake)

    def test_existing_soft_body_glitch_protection_kept(self):
        cab = source("source/main/physics/flex/FlexObj.cpp")
        safety = source("source/main/physics/flex/CabMeshSafety.h")
        flexbody = source("source/main/physics/flex/FlexBody.cpp")
        self.assertIn("CountTriangleReferencesByNode(", cab)
        self.assertIn("CabMeshSafety::CanCollapseFace(", cab)
        self.assertIn("node_face_counts[vertex_node_ids[triangle_indices[i]]]", safety)
        self.assertIn("reorganiseBuffers(optimalVD)", flexbody)
        self.assertIn("reorganiseBuffers(optimalVD->clone())", flexbody)

    def test_camera_and_gui_api_changes(self):
        envcpp = source("source/main/gfx/EnvironmentMap.cpp")
        envh = source("source/main/gfx/EnvironmentMap.h")
        scene = source("source/main/gfx/GfxScene.cpp")
        imgui = source("source/main/gui/imgui/OgreImGuiOverlay.cpp")
        self.assertIn("void RoR::GfxEnvmap::CreateSceneNodes()", envcpp)
        self.assertIn("m_cameras_snode[i]->setPosition(center)", envcpp)
        self.assertIn("m_cameras_snode[NUM_FACES]", envh)
        self.assertIn("GetEnvMap().CreateSceneNodes()", scene)
        self.assertNotIn("useGlobalInstancingVertexBufferIsAvailable =", imgui)

    def test_ogre14_terrain_generator_and_shadow_pipeline(self):
        terrain = source("source/main/terrain/TerrainGeometryManager.cpp")
        shadow_api = source("source/main/gfx/ShadowManager.h")
        shadow_impl = source("source/main/gfx/ShadowManager.cpp")
        game_cmake = source("source/main/CMakeLists.txt")
        self.assertIn("new Ogre::TerrainMaterialGeneratorA()", terrain)
        self.assertIn("class Terrn2CustomMaterial : public Ogre::TerrainMaterialGenerator", terrain)
        self.assertIn("Ogre::MaterialPtr generate(const Ogre::Terrain* terrain) override", terrain)
        self.assertIn("Ogre::TerrainMaterialGeneratorA::SM2Profile*", shadow_api)
        self.assertIn("Ogre::TerrainMaterialGeneratorA::SM2Profile*", shadow_impl)
        self.assertNotIn("terrain/OgreTerrainPSSMMaterialGenerator.{h,cpp}", game_cmake)
        self.assertIn("setShadowTextureCountPerLightType", shadow_impl)

    def test_ogre14_vehicle_camera_and_sun_node_transforms(self):
        spawner = source("source/main/physics/ActorSpawner.cpp")
        gfx = source("source/main/gfx/GfxActor.cpp")
        terrain = source("source/main/terrain/Terrain.cpp")
        sky = source("source/main/gfx/SkyXManager.cpp")
        caelum = source("source/main/gfx/SkyManager.cpp")
        self.assertIn("vcam_node->attachObject(vcam.vcam_ogre_camera)", spawner)
        self.assertIn("mirror_camera_node->attachObject(vcam.vcam_ogre_camera)", spawner)
        self.assertIn("vidcam.vcam_ogre_camera->getParentSceneNode()->setPosition(", gfx)
        self.assertIn("lightbar_light_node->attachObject(prop.pp_beacon_light[k])", spawner)
        self.assertIn("main_light_node->attachObject(m_main_light)", terrain)
        self.assertIn("sunlight_node->attachObject(mLight1)", sky)
        self.assertIn("getMainLight()->getParentSceneNode()->setDirection", caelum)

    def test_ogre14_scene_lights_and_reflections(self):
        objects = source("source/main/terrain/TerrainObjectManager.cpp")
        water = source("source/main/gfx/GfxWater.cpp")
        spawner = source("source/main/physics/ActorSpawner.cpp")
        self.assertIn("spot_node->attachObject(spotLight);", objects)
        self.assertIn("point_node->attachObject(pointlight);", objects)
        self.assertIn("spot_node->setDirection(spotl.dir);", objects)
        self.assertIn("refract_camera_node->attachObject(m_refract_cam);", water)
        self.assertIn("reflect_camera_node->attachObject(m_reflect_cam);", water)
        self.assertIn("m_reflect_cam->getParentSceneNode()->setPosition(", water)
        self.assertIn("m_refract_cam->getParentSceneNode()->setOrientation(", water)
        self.assertIn("flare_light_node->attachObject(flare.light);", spawner)

    def test_ogre14_caelum_initialisation_and_d3d11_safety(self):
        main = source("source/main/main.cpp")
        plugins = source("source/main/plugins.cfg.in")
        warning = source("source/main/system/CVar.cpp")
        self.assertIn("new Caelum::CaelumPlugin()", main)
        self.assertIn("#include <Caelum.h>", main)
        self.assertNotIn("@CFG_OGRE_PLUGIN_CAELUM@", plugins)
        self.assertIn('"Warning texture",', warning)
        self.assertIn('CVAR_ARCHIVE | CVAR_TYPE_BOOL,    "true"); // OGRE14 DX11', warning)

    def test_native_ogre14_shadow_shader_pipeline(self):
        main = source("source/main/main.cpp")
        shadow = source("source/main/gfx/ShadowManager.cpp")
        terrain = source("source/main/terrain/TerrainGeometryManager.cpp")
        caster = source("resources/OgreCore/Shadow.material")
        programs = source("resources/OgreCore/ShadowVolumeExtude.program")
        pssm_shader = source("resources/rtshader/SGXLib_IntegratedPSSM.glsl")

        self.assertIn("ShaderGenerator::initialize()", main)
        self.assertIn("ShaderGenerator::getSingletonPtr()", main)
        self.assertIn("ContentManager::ResourcePack::RTSHADER", main)
        self.assertLess(
            main.index("ContentManager::ResourcePack::RTSHADER"),
            main.index("ShaderGenerator::initialize()"),
        )
        self.assertIn("SHADOWTYPE_TEXTURE_MODULATIVE_INTEGRATED", shadow)
        self.assertIn('getByName("Ogre/TextureShadowCaster")', shadow)
        self.assertIn("PF_X8B8G8R8", shadow)
        self.assertNotIn("PF_FLOAT32_R", shadow)
        self.assertNotIn("matProfile->setReceiveDynamicShadowsDepth(", shadow)
        self.assertNotIn("matProfile->setReceiveDynamicShadowsDepth(", terrain)
        self.assertNotIn("matProfile->setGlobalColourMapEnabled(", terrain)
        self.assertIn("page_terrain->setGlobalColourMapEnabled(true)", terrain)
        self.assertIn("material Ogre/TextureShadowCaster", caster)
        self.assertIn("Ogre/ShadowBlendVP", programs)
        self.assertIn("SGX_ComputeShadowFactor_PSSM3", pssm_shader)

        for resource in (
            "resources/OgreCore/TerrainSurface.glsl",
            "resources/OgreCore/TerrainTransforms.glsl",
            "resources/OgreCore/OgreUnifiedShader.h",
            "resources/OgreCore/GLSL_GL3Support.glsl",
            "resources/OgreCore/HLSL_SM4Support.hlsl",
            "resources/OgreCore/ShadowBlend.vert",
            "resources/OgreCore/ShadowBlend.frag",
            "resources/OgreCore/ShadowExtrudeDirLight.vert",
            "resources/OgreCore/ShadowExtrudeDirLightFinite.vert",
            "resources/OgreCore/ShadowExtrudePointLight.vert",
            "resources/OgreCore/ShadowExtrudePointLightFinite.vert",
            "resources/rtshader/SGXLib_NormalMap.glsl",
            "resources/rtshader/FFPLib_AlphaTest.glsl",
        ):
            self.assertTrue((ROOT / resource).is_file(), resource)

    def test_remaining_ogre14_ui_and_particle_api_ports(self):
        gui = source("source/main/gui/RTTLayer.cpp")
        imgui = source("source/main/gui/imgui/OgreImGuiOverlay.cpp")
        imgui_header = source("source/main/gui/imgui/OgreImGuiOverlay.h")
        input_source = source("source/main/utils/InputEngine.cpp")
        spawner = source("source/main/physics/ActorSpawner.cpp")
        self.assertIn('std::string(propert->findAttribute("key"))', gui)
        self.assertIn('std::string(propert->findAttribute("value"))', gui)
        self.assertNotIn("mConvertToBGR", imgui)
        self.assertNotIn("mConvertToBGR", imgui_header)
        self.assertIn("rw->getMetrics(width, height, left, top);", input_source)
        self.assertNotIn("rw->getMetrics(width, height, depth, left, top)", input_source)
        self.assertIn("Ogre::MOT_PARTICLE_SYSTEM", spawner)

    def test_minimap_scene_node_and_legacy_resource_group_compatibility(self):
        survey = source("source/main/gfx/SurveyMapTextureCreator.cpp")
        resources = source("source/main/resources/ContentManager.cpp")
        menus = source("source/main/gui/GUIManager.cpp")
        icons = source("source/main/gui/GUIUtils.cpp")
        self.assertIn("camera_node->attachObject(mCamera)", survey)
        self.assertIn("mCamera->getParentSceneNode()->setPosition", survey)
        self.assertNotIn("mCamera->setFixedYawAxis(", survey)
        self.assertIn('DECLARE_RESOURCE_PACK( WALLPAPERS,', resources)
        self.assertIn('"Wallpapers"', menus)
        self.assertIn('"FlagsRG"', icons)
        self.assertNotIn("RGN_WALLPAPERS", menus)
        self.assertNotIn("RGN_UI_ICONS", icons)

    def test_windows_game_build_is_gated(self):
        build = source(".github/workflows/ogre14-windows-compile.yml")
        self.assertIn("cmake --build build --target install", build)
        self.assertIn("Test-RoRWindowsPackage.ps1", build)
        self.assertIn("Test-RendererPlugins.ps1", build)
        self.assertIn("Test-CgShaders.py", build)
        self.assertIn("--ci-load-check", build)
        self.assertIn("if: always()", build)
        self.assertIn("https://conan.cloudsmith.io/rigs-of-rods/deps/", build)

    def test_ogre14_skyx_hydrax_and_camera_projection(self):
        sky = source("source/main/gfx/skyx/VClouds/VClouds.cpp")
        hydrax_rtt = source("source/main/gfx/hydrax/RttManager.cpp")
        hydrax_mat = source("source/main/gfx/hydrax/MaterialManager.cpp")
        camera = source("source/main/gfx/camera/CameraManager.cpp")
        self.assertIn("Ogre::RENDER_QUEUE_8", sky)
        self.assertNotIn("Ogre::RENDER_QUEUE_9", sky)
        self.assertNotIn("getProjectionMatrixRS()", hydrax_rtt)
        self.assertIn("getCamera()->getParentSceneNode()->getPosition()", hydrax_mat)
        self.assertIn("setFarClipDistance(100000.0f)", camera)

    def test_missing_optional_cg_shadow_parameters_are_safe(self):
        shadows = source("source/main/gfx/ShadowManager.cpp")
        self.assertIn("getAvailableSharedParameters()", shadows)
        self.assertIn('shared_sets.find("pssm_params")', shadows)
        self.assertIn("if (legacy_params == shared_sets.end())", shadows)
        self.assertIn("legacy_params->second->setNamedConstant", shadows)

    def test_preserve_existing_graphics_controls_and_shadow_code(self):
        ui = source("source/main/gui/panels/GUI_GameSettings.cpp")
        menu = source("source/main/gui/panels/GUI_GameMainMenu.cpp")
        shadows = source("source/main/gfx/ShadowManager.cpp")
        self.assertIn("Apply experimental graphics preset", ui)
        self.assertIn("Apply preview preset", menu)
        self.assertIn("processPSSM()", shadows)
        self.assertIn("setShadowFarDistance", shadows)


if __name__ == "__main__":
    unittest.main(verbosity=2)
