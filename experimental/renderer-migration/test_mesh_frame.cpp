/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "DeformableMeshFrame.h"
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>

using namespace RoR::RendererMigration;

static bool Near(float a, float b) { return std::fabs(a - b) < 1e-5f; }

static void Require(bool condition, const char* message)
{
    if (!condition) throw std::runtime_error(message);
}

int main()
{
    const std::vector<Vec3> nodes = {{0, 0, 0}, {1, 0, 0}, {1, 0, 1}, {0, 0, 1}};
    const std::vector<VertexBinding> bindings = {
        {0, {0, 0}}, {1, {1, 0}}, {2, {1, 1}}, {3, {0, 1}}};
    const std::vector<Triangle> triangles = {{0, 2, 1}, {0, 3, 2}};

    const MeshFrame initial = BuildMeshFrame(nodes, bindings, triangles);
    Require(initial.vertices.size() == 4, "mesh validation failed");
    Require(initial.triangle_indices.size() == 6, "mesh validation failed");
    Require(Near(initial.origin.x, 0.5f), "mesh validation failed");
    Require(Near(initial.vertices[0].position.x, -0.5f), "mesh validation failed");
    Require(Near(initial.vertices[2].uv.x, 1.0f), "mesh validation failed");
    for (const Vertex& vertex : initial.vertices)
    {
        Require(Near(vertex.normal.x, 0.0f), "mesh validation failed");
        Require(Near(vertex.normal.y, 1.0f), "mesh validation failed");
        Require(Near(vertex.normal.z, 0.0f), "mesh validation failed");
    }

    std::vector<Vec3> dented = nodes;
    dented[2].y = -0.4f;
    const MeshFrame damaged = BuildMeshFrame(dented, bindings, triangles);
    Require(Near(damaged.vertices[2].position.y, -0.4f), "mesh validation failed");
    Require(damaged.triangle_indices == initial.triangle_indices, "mesh validation failed");

    const MeshFrame degenerate = BuildMeshFrame(nodes, bindings, {{0, 0, 0}});
    Require(std::isfinite(degenerate.vertices[0].normal.y), "mesh validation failed");
    Require(Near(degenerate.vertices[0].normal.y, 0.0f), "mesh validation failed");

    // A very small adjacent face should not dominate the smooth vertex
    // normal of a large surface. This is important for bent and torn cabs.
    const std::vector<Vec3> unequal_nodes = {
        {0.f, 0.f, 0.f}, {4.f, 0.f, 0.f}, {0.f, 0.f, 4.f},
        {0.f, 0.1f, 0.f}, {0.f, 0.f, 0.1f}};
    const std::vector<VertexBinding> unequal_bindings = {
        {0,{0,0}}, {1,{0,0}}, {2,{0,0}},
        {3,{0,0}}, {4,{0,0}}};
    const MeshFrame unequal = BuildMeshFrame(
        unequal_nodes, unequal_bindings, {{0, 2, 1}, {0, 3, 4}});
    Require(unequal.vertices[0].normal.y > 0.99f,
        "small face incorrectly outweighs broad surface normal");
    Require(unequal.vertices[0].normal.x > 0.f &&
            unequal.vertices[0].normal.x < 0.01f,
        "area-weighted smooth normal should retain the tiny face influence");

    // A tiny side triangle must not rotate a large cab panel's normal by
    // ~45 degrees: accumulated face normals must be area-weighted.
    const std::vector<Vec3> mixed_nodes = {
        {0, 0, 0}, {4, 0, 0}, {0, 0, 4}, {0, 0.1f, 0}, {0.1f, 0, 0}};
    const std::vector<VertexBinding> mixed_bindings = {
        {0, {0, 0}}, {1, {1, 0}}, {2, {0, 1}},
        {3, {0, 0}}, {4, {0, 0}}};
    const MeshFrame mixed = BuildMeshFrame(
        mixed_nodes, mixed_bindings, {{0, 1, 2}, {0, 3, 4}});
    Require(std::fabs(mixed.vertices[0].normal.y) > 0.99f,
        "tiny triangle must not dominate cab normal");
    Require(std::fabs(mixed.vertices[0].normal.z) < 0.01f,
        "triangle normal must be weighted by doubled area");
    Require(std::isfinite(mixed.vertices[0].normal.x),
        "area-weighted vertex normal must remain finite");

    bool bad_triangle_rejected = false;
    try { BuildMeshFrame(nodes, bindings, {{0, 1, 99}}); }
    catch (const std::out_of_range&) { bad_triangle_rejected = true; }
    Require(bad_triangle_rejected, "mesh validation failed");

    bool bad_node_rejected = false;
    std::vector<VertexBinding> invalid = bindings;
    invalid[0].node_index = 99;
    try { BuildMeshFrame(nodes, invalid, triangles); }
    catch (const std::out_of_range&) { bad_node_rejected = true; }
    Require(bad_node_rejected, "mesh validation failed");

    // Two finite, same-sign positions can overflow during midpoint
    // calculation unless each summand is scaled before addition.
    const float large = std::numeric_limits<float>::max() * 0.75f;
    const std::vector<Vec3> large_nodes = {
        {large, large, large}, {large, large, large}
    };
    const std::vector<VertexBinding> large_bindings = {
        {0, {0, 0}}, {1, {1, 0}}
    };
    const MeshFrame large_frame = BuildMeshFrame(
        large_nodes, large_bindings, {});
    Require(std::isfinite(large_frame.origin.x), "large mesh origin overflowed");
    Require(std::isfinite(large_frame.origin.y), "large mesh origin overflowed");
    Require(std::isfinite(large_frame.origin.z), "large mesh origin overflowed");
    Require(large_frame.origin.x == large, "large mesh origin inaccurate");
    Require(large_frame.vertices[0].position.x == 0.f,
        "large mesh relative position inaccurate");

    std::cout << "PASS: renderer-independent deformable mesh frame tests\\n";
    return 0;
}
