/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
#include <cmath>

namespace RoR {
namespace CabMeshSafety {

// In FlexObj, a stretched face may be folded to a tiny visual triangle.
// This is safe only when the two vertices being moved are not shared by
// other faces. Otherwise folding one damaged panel deforms its neighbours.
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
