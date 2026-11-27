"""MyGUI 3.4.3 build recipe for the experimental OGRE 14 renderer.

The published anotherfoxguy/stable Conan recipe unconditionally patches
CMake/Utils/PrecompiledHeader.cmake, which MyGUI 3.4.3 no longer ships.
Export this recipe into the local Conan cache before configuring RoR. Keep
the name/version/user/channel unchanged so the dependency graph still
resolves mygui/3.4.3@anotherfoxguy/stable without modifying master.

Adapted from the MIT-licensed Conan 2 MyGUI recipe in YDTHobby/trussline.
"""

import os

from conan import ConanFile
from conan.tools.cmake import CMake, CMakeDeps, CMakeToolchain, cmake_layout
from conan.tools.files import collect_libs, get, replace_in_file


class MyGUIConan(ConanFile):
    name = "mygui"
    version = "3.4.3"
    license = "MIT"
    url = "https://github.com/AnotherFoxGuy/conan-MyGUI"
    description = "Fast, flexible and simple game UI."
    settings = "os", "compiler", "build_type", "arch"
    options = {"system_ogre": [True, False]}
    default_options = {"system_ogre": False}

    def layout(self):
        cmake_layout(self)

    def requirements(self):
        if not self.options.system_ogre:
            # OGRE 14, not the incompatible MyGUI+OGRE 1.x binaries.
            self.requires("ogre3d/[>=14 <15]@anotherfoxguy/stable")

    def build_requirements(self):
        # The upstream MyGUI 3.4.x CMake scripts predate CMake 4.
        self.tool_requires("cmake/[>=3.22 <4]")

    def source(self):
        get(self, **self.conan_data["sources"][str(self.version)], strip_root=True)

    def generate(self):
        tc = CMakeToolchain(self)
        for option in (
            "MYGUI_BUILD_DEMOS",
            "MYGUI_BUILD_DOCS",
            "MYGUI_BUILD_TEST_APP",
            "MYGUI_BUILD_PLUGINS",
            "MYGUI_BUILD_TOOLS",
        ):
            tc.variables[option] = "OFF"
        tc.variables["MYGUI_RENDERSYSTEM"] = "3"  # OGRE rendering backend
        tc.generate()
        CMakeDeps(self).generate()

    def _patch_sources(self):
        replace_in_file(
            self,
            os.path.join(self.source_folder, "MyGUIEngine", "CMakeLists.txt"),
            "${FREETYPE_LIBRARIES}",
            "freetype",
        )
        replace_in_file(
            self,
            os.path.join(self.source_folder, "CMake", "Dependencies.cmake"),
            "find_package(OGRE_Old)",
            "find_package(OGRE CONFIG)",
        )
        replace_in_file(
            self,
            os.path.join(
                self.source_folder, "Platforms", "Ogre", "OgrePlatform", "CMakeLists.txt"
            ),
            "${OGRE_LIBRARIES}",
            "OGRE::OGRE",
        )
        pch = os.path.join(
            self.source_folder, "CMake", "Utils", "PrecompiledHeader.cmake"
        )
        # MyGUI 3.4.3 removed this legacy file. It is not a build failure.
        if os.path.isfile(pch):
            replace_in_file(
                self,
                pch,
                "if (MSVC)",
                "target_precompile_headers(${TARGET} PRIVATE ${SRC_FILE})\nif (FALSE)",
            )

    def build(self):
        self._patch_sources()
        cmake = CMake(self)
        cmake.configure()
        cmake.build()

    def package(self):
        CMake(self).install()

    def package_info(self):
        self.cpp_info.set_property("cmake_file_name", "MyGUI")
        self.cpp_info.set_property("cmake_target_name", "MyGUI::MyGUI")
        self.cpp_info.set_property("cmake_module_file_name", "MyGUI")
        self.cpp_info.set_property("cmake_module_target_name", "MyGUI::MyGUI")
        self.cpp_info.includedirs = ["include/MYGUI"]
        self.cpp_info.libdirs = ["lib", f"lib/{self.settings.build_type}"]
        self.cpp_info.libs = collect_libs(self)

    def package_id(self):
        if not self.info.options.system_ogre:
            # Avoid treating binaries linked to OGRE 1.x as OGRE 14-compatible.
            self.info.requires["ogre3d"].full_recipe_mode()
