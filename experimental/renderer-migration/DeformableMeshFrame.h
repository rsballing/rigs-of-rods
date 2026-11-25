/*
 * Rigs of Rods renderer migration experiment
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 * Renderer-independent deformable geometry, not yet integrated into RoR.
 */
#pragma once

#include <cmath>
#include <cstddef>
#include <cstdint>
#include <stdexcept>
#include <vector>

namespace RoR {
namespace RendererMigration {

struct Vec2 { float x, y; };
struct Vec3 { float x, y, z; };

inline Vec3 operator-(const Vec3& a, const Vec3& b)
{
    return {a.x - b.x, a.y - b.y, a.z - b.z};
}

inline Vec3 operator+(const Vec3& a, const Vec3& b)
{
    return {a.x + b.x, a.y + b.y, a.z + b.z};
}

inline Vec3 operator/(const Vec3& a, float divisor)
{
    return {a.x / divisor, a.y / divisor, a.z / divisor};
}

inline Vec3 Cross(const Vec3& a, const Vec3& b)
{
    return {a.y * b.z - a.z * b.y,
            a.z * b.x - a.x * b.z,
            a.x * b.y - a.y * b.x};
}

inline float LengthSquared(const Vec3& v)
{
    return v.x * v.x + v.y * v.y + v.z * v.z;
}

inline bool IsFinite(const Vec3& v)
{
    return std::isfinite(v.x) && std::isfinite(v.y) && std::isfinite(v.z);
}

struct VertexBinding
{
    std::size_t node_index;
    Vec2 uv;
};

struct Triangle
{
    std::uint32_t a, b, c; // Indices into the vertex bindings
};

struct Vertex
{
    Vec3 position; // Relative to origin
    Vec3 normal;
    Vec2 uv;
};

struct MeshFrame
{
    Vec3 origin;
    std::vector<Vertex> vertices;
    std::vector<std::uint32_t> triangle_indices;
};

// Converts simulated node locations to vertex data without depending on OGRE.
// Intended for testing a future shared mesh builder used by both OGRE 1.x
// and a new renderer. This does not reproduce FlexObj's triangle-collapse
// heuristic or manage materials/submeshes yet.
inline MeshFrame BuildMeshFrame(const std::vector<Vec3>& nodes,
                               const std::vector<VertexBinding>& bindings,
                               const std::vector<Triangle>& triangles)
{
    if (bindings.size() < 2)
        throw std::invalid_argument("At least two vertex bindings required");

    for (const VertexBinding& binding : bindings)
    {
        if (binding.node_index >= nodes.size())
            throw std::out_of_range("Vertex binding references missing node");
        if (!IsFinite(nodes[binding.node_index]) ||
            !std::isfinite(binding.uv.x) || !std::isfinite(binding.uv.y))
            throw std::invalid_argument("Non-finite vertex data");
    }

    const Vec3& a = nodes[bindings[0].node_index];
    const Vec3& b = nodes[bindings[1].node_index];

    MeshFrame frame;
    frame.origin = {(a.x + b.x) * 0.5f,
                    (a.y + b.y) * 0.5f,
                    (a.z + b.z) * 0.5f};
    frame.vertices.reserve(bindings.size());
    frame.triangle_indices.reserve(triangles.size() * 3);

    for (const VertexBinding& binding : bindings)
        frame.vertices.push_back({nodes[binding.node_index] - frame.origin,
                                  {0.0f, 0.0f, 0.0f}, binding.uv});

    for (const Triangle& triangle : triangles)
    {
        if (triangle.a >= bindings.size() ||
            triangle.b >= bindings.size() ||
            triangle.c >= bindings.size())
            throw std::out_of_range("Triangle references missing vertex");

        frame.triangle_indices.push_back(triangle.a);
        frame.triangle_indices.push_back(triangle.b);
        frame.triangle_indices.push_back(triangle.c);

        const Vec3& p0 = frame.vertices[triangle.a].position;
        const Vec3& p1 = frame.vertices[triangle.b].position;
        const Vec3& p2 = frame.vertices[triangle.c].position;
        const Vec3 n = Cross(p1 - p0, p2 - p0);
        const float magnitude_sq = LengthSquared(n);
        if (magnitude_sq <= 1e-20f)
            continue; // No NaNs from degenerate triangles

        // Accumulate area-weighted face normals. Equal weighting makes
        // a tiny triangle pull the normal as strongly as a large face,
        // which creates conspicuous lighting artifacts on deformable cabs.
        // The final pass normalizes each accumulated vertex normal.
        frame.vertices[triangle.a].normal = frame.vertices[triangle.a].normal + n;
        frame.vertices[triangle.b].normal = frame.vertices[triangle.b].normal + n;
        frame.vertices[triangle.c].normal = frame.vertices[triangle.c].normal + n;
    }

    for (Vertex& vertex : frame.vertices)
    {
        const float magnitude_sq = LengthSquared(vertex.normal);
        if (magnitude_sq > 1e-20f)
            vertex.normal = vertex.normal / std::sqrt(magnitude_sq);
    }
    return frame;
}

} // namespace RendererMigration
} // namespace RoR
