cmake_minimum_required(VERSION 3.16)
project(RoRRendererMigrationPrototype LANGUAGES CXX)

add_executable(test_mesh_frame test_mesh_frame.cpp)
target_compile_features(test_mesh_frame PRIVATE cxx_std_11)

add_executable(test_sky_lighting test_sky_lighting.cpp)
target_compile_features(test_sky_lighting PRIVATE cxx_std_11)

enable_testing()
add_test(NAME deformable_mesh_frame COMMAND test_mesh_frame)
add_test(NAME sky_lighting_math COMMAND test_sky_lighting)
