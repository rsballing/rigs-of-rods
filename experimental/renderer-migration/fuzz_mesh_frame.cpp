/* SPDX-License-Identifier: GPL-3.0-or-later */
// Deterministic property testing for the renderer-neutral deformable mesh.
// This exercises the same large/small/degenerate face math used on cabs.
#include "DeformableMeshFrame.h"
#include <cmath>
#include <iostream>
#include <random>
#include <stdexcept>
#include <vector>

using namespace RoR::RendererMigration;

int main()
{
    std::mt19937 rng(20261124u); // Reproducible across test runs
    std::uniform_real_distribution<float> coordinate(-1000.f, 1000.f);
    std::uniform_int_distribution<int> vertexIndex(0, 15);

    const int frameCount = 25000;
    const int trianglesPerFrame = 26;
    for (int frameIndex = 0; frameIndex < frameCount; ++frameIndex)
    {
        std::vector<Vec3> nodes;
        std::vector<VertexBinding> bindings;
        for (int v = 0; v < 16; ++v)
        {
            Vec3 p = {coordinate(rng), coordinate(rng), coordinate(rng)};
            if (v > 0 && (v % 5) == 0)
                p = nodes[0]; // Intentionally collapsed vertices
            nodes.push_back(p);
            bindings.push_back({static_cast<std::size_t>(v), {0, 0}});
        }

        std::vector<Triangle> faces;
        for (int t = 0; t < trianglesPerFrame; ++t)
        {
            faces.push_back({static_cast<unsigned>(vertexIndex(rng)),
                             static_cast<unsigned>(vertexIndex(rng)),
                             static_cast<unsigned>(vertexIndex(rng))});
        }
        const MeshFrame generated = BuildMeshFrame(nodes, bindings, faces);
        for (const Vertex& v : generated.vertices)
        {
            if (!std::isfinite(v.position.x) || !std::isfinite(v.position.y) ||
                !std::isfinite(v.position.z) || !std::isfinite(v.normal.x) ||
                !std::isfinite(v.normal.y) || !std::isfinite(v.normal.z))
                throw std::runtime_error("Non-finite deformable mesh position or normal");
            const float lengthSq = v.normal.x * v.normal.x +
                                   v.normal.y * v.normal.y +
                                   v.normal.z * v.normal.z;
            if (lengthSq > 1.00001f)
                throw std::runtime_error("Deformable vertex normal exceeds unit length");
        }
    }
    std::cout << "PASS: " << frameCount << " deformable frames and "
              << frameCount * trianglesPerFrame
              << " faces tested with deterministic random deformations\n";
}
