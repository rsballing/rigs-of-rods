cmake_minimum_required(VERSION 3.16)
project(RoRPhysicsHotpathTests LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

add_executable(ror_threadpool_test TestThreadPool.cpp)
target_include_directories(ror_threadpool_test PRIVATE
    "${CMAKE_CURRENT_SOURCE_DIR}/include"
    "${CMAKE_CURRENT_SOURCE_DIR}/../../../source/main/threadpool"
)
find_package(Threads REQUIRED)
target_link_libraries(ror_threadpool_test PRIVATE Threads::Threads)

enable_testing()
add_test(NAME ror_threadpool_physics_hotpath COMMAND ror_threadpool_test)
