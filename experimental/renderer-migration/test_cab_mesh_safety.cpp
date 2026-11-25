/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../../source/main/physics/flex/CabMeshSafety.h"
#include <iostream>
#include <limits>
#include <stdexcept>

using namespace RoR::CabMeshSafety;

static void Require(bool condition, const char* message)
{
    if (!condition) throw std::runtime_error(message);
}

int main()
{
    Require(CanCollapseFace(5.f, 4.f, 1u, 1u), "isolated stretched face must collapse");
    Require(!CanCollapseFace(5.f, 4.f, 2u, 1u), "second node is shared");
    Require(!CanCollapseFace(5.f, 4.f, 1u, 2u), "third node is shared");
    Require(!CanCollapseFace(5.f, 4.f, 2u, 2u), "both nodes are shared");
    Require(!CanCollapseFace(4.f, 4.f, 1u, 1u), "equal areas must not collapse");
    Require(!CanCollapseFace(3.f, 4.f, 1u, 1u), "unstretched face must not collapse");
    Require(!CanCollapseFace(5.f, 0.f, 1u, 1u), "zero reference area invalid");
    Require(!CanCollapseFace(5.f, 1e-12f, 1u, 1u), "near-zero reference area invalid");
    Require(!CanCollapseFace(0.f, 4.f, 1u, 1u), "zero face area invalid");
    Require(!CanCollapseFace(std::numeric_limits<float>::infinity(), 4.f, 1u, 1u), "infinite current area invalid");
    Require(!CanCollapseFace(5.f, std::numeric_limits<float>::quiet_NaN(), 1u, 1u), "NaN reference area invalid");

    // Vertex 2 and vertex 3 have different UVs, but the SAME physics node 6.
    // A GPU-vertex-only reference count would incorrectly allow a collapse.
    const int node_ids[] = {4, 5, 6, 6, 7, 8};
    const unsigned short triangles[] = {0, 1, 2, 3, 4, 5};
    const std::vector<unsigned int> counts = CountTriangleReferencesByNode(
        node_ids, 6u, triangles, 6u);
    Require(counts.size() == 6u, "reference count size");
    Require(counts[2] == 2u && counts[3] == 2u, "UV seams must share face count");
    Require(counts[1] == 1u && counts[4] == 1u, "independent nodes remain unique");
    Require(!CanCollapseFace(5.f, 4.f, counts[1], counts[2]),
        "collapsing a UV seam node would tear a neighbouring panel");
    Require(CanCollapseFace(5.f, 4.f, counts[4], counts[5]),
        "independent face may still use original collapse rule");

    bool bad_index_rejected = false;
    const unsigned short invalid_triangles[] = {0, 1, 99};
    try { CountTriangleReferencesByNode(node_ids, 6u, invalid_triangles, 3u); }
    catch (const std::out_of_range&) { bad_index_rejected = true; }
    Require(bad_index_rejected, "out-of-range vertex index must be rejected");

    std::cout << "PASS: shared cab vertex and UV-seam safety policy\n";
    return 0;
}
