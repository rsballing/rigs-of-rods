cmake_minimum_required(VERSION 3.16)
project(RoRRendererMigrationPrototype LANGUAGES CXX)

add_executable(test_mesh_frame test_mesh_frame.cpp)
target_compile_features(test_mesh_frame PRIVATE cxx_std_11)

add_executable(test_sky_lighting test_sky_lighting.cpp)
target_compile_features(test_sky_lighting PRIVATE cxx_std_11)

add_executable(test_shadow_quality test_shadow_quality.cpp)
target_compile_features(test_shadow_quality PRIVATE cxx_std_11)

enable_testing()
add_test(NAME deformable_mesh_frame COMMAND test_mesh_frame)
add_test(NAME sky_lighting_math COMMAND test_sky_lighting)
add_test(NAME shadow_quality_policy COMMAND test_shadow_quality)

# Source-contract tests guard against regressions in dynamically generated
# Cg and OGRE plugin packaging code; they do not replace GPU runtime tests.
find_package(Python3 COMPONENTS Interpreter QUIET)
if(Python3_Interpreter_FOUND)
    add_test(
        NAME renderer_source_contracts
        COMMAND ${Python3_EXECUTABLE} ${CMAKE_CURRENT_SOURCE_DIR}/test_renderer_source_invariants.py
    )
endif()
