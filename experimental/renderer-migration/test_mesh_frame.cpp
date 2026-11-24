/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "DeformableMeshFrame.h"
#include <cassert>
#include <cmath>
#include <iostream>
#include <stdexcept>

using namespace RoR::RendererMigration;

static bool Near(float a, float b) { return std::fabs(a - b) < 1e-5f; }

int main()
{
    const std::vector<Vec3> nodes = {{0, 0, 0}, {1, 0, 0}, {1, 0, 1}, {0, 0, 1}};
    const std::vector<VertexBinding> bindings = {
        {0, {0, 0}}, {1, {1, 0}}, {2, {1, 1}}, {3, {0, 1}}};
    const std::vector<Triangle> triangles = {{0, 2, 1}, {0, 3, 2}};

    const MeshFrame initial = BuildMeshFrame(nodes, bindings, triangles);
    assert(initial.vertices.size() == 4);
    assert(initial.triangle_indices.size() == 6);
    assert(Near(initial.origin.x, 0.5f));
    assert(Near(initial.vertices[0].position.x, -0.5f));
    assert(Near(initial.vertices[2].uv.x, 1.0f));
    for (const Vertex& vertex : initial.vertices)
    {
        assert(Near(vertex.normal.x, 0.0f));
        assert(Near(vertex.normal.y, 1.0f));
        assert(Near(vertex.normal.z, 0.0f));
    }

    std::vector<Vec3> dented = nodes;
    dented[2].y = -0.4f;
    const MeshFrame damaged = BuildMeshFrame(dented, bindings, triangles);
    assert(Near(damaged.vertices[2].position.y, -0.4f));
    assert(damaged.triangle_indices == initial.triangle_indices);

    const MeshFrame degenerate = BuildMeshFrame(nodes, bindings, {{0, 0, 0}});
    assert(std::isfinite(degenerate.vertices[0].normal.y));
    assert(Near(degenerate.vertices[0].normal.y, 0.0f));

    bool bad_triangle_rejected = false;
    try { BuildMeshFrame(nodes, bindings, {{0, 1, 99}}); }
    catch (const std::out_of_range&) { bad_triangle_rejected = true; }
    assert(bad_triangle_rejected);

    bool bad_node_rejected = false;
    std::vector<VertexBinding> invalid = bindings;
    invalid[0].node_index = 99;
    try { BuildMeshFrame(nodes, invalid, triangles); }
    catch (const std::out_of_range&) { bad_node_rejected = true; }
    assert(bad_node_rejected);

    std::cout << "PASS: renderer-independent deformable mesh frame tests\n";
    return 0;
}
