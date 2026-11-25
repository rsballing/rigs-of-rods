/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <cmath>
#include <cstddef>
#include <stdexcept>
#include <unordered_map>
#include <vector>

namespace RoR {
namespace CabMeshSafety {

// Count by physics node rather than GPU vertex index: a material/UV seam
// can generate two GPU vertices attached to the same simulation node.
inline std::vector<unsigned int> CountTriangleReferencesByNode(
    const int* vertex_node_ids, std::size_t vertex_count,
    const unsigned short* triangle_indices, std::size_t index_count)
{
    if (index_count % 3u != 0u)
        throw std::invalid_argument("Cab triangle indices must be divisible by three");
    std::unordered_map<int, unsigned int> node_face_counts;
    for (std::size_t i = 0; i < index_count; ++i)
    {
        if (triangle_indices[i] >= vertex_count)
            throw std::out_of_range("Cab triangle references missing vertex");
        ++node_face_counts[vertex_node_ids[triangle_indices[i]]];
    }
    std::vector<unsigned int> counts(vertex_count);
    for (std::size_t i = 0; i < vertex_count; ++i)
        counts[i] = node_face_counts[vertex_node_ids[i]];
    return counts;
}

// A stretched face can only collapse when its two displaced physics nodes
// do not also belong to another face. This leaves neighbouring panels intact.
inline bool CanCollapseFace(float doubled_area, float reference_area,
                            unsigned int second_vertex_face_count,
                            unsigned int third_vertex_face_count)
{
    return std::isfinite(doubled_area) && std::isfinite(reference_area) &&
           doubled_area > 1e-10f && reference_area > 1e-10f &&
           doubled_area > reference_area &&
           second_vertex_face_count == 1u && third_vertex_face_count == 1u;
}

} // namespace CabMeshSafety
} // namespace RoR
