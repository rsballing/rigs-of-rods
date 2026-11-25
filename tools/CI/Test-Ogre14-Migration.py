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
