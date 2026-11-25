/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../../source/main/physics/flex/CabMeshSafety.h"
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>

using RoR::CabMeshSafety::CanCollapseFace;

static void Require(bool condition, const char* message)
{
    if (!condition) throw std::runtime_error(message);
}

int main()
{
    Require(CanCollapseFace(5.f, 4.f, 1u, 1u), "isolated stretched face must collapse");
    Require(!CanCollapseFace(5.f, 4.f, 2u, 1u), "second vertex is shared");
    Require(!CanCollapseFace(5.f, 4.f, 1u, 2u), "third vertex is shared");
    Require(!CanCollapseFace(5.f, 4.f, 2u, 2u), "both vertices are shared");
    Require(!CanCollapseFace(4.f, 4.f, 1u, 1u), "equal areas must not collapse");
    Require(!CanCollapseFace(3.f, 4.f, 1u, 1u), "unstretched face must not collapse");
    Require(!CanCollapseFace(5.f, 0.f, 1u, 1u), "zero reference area invalid");
    Require(!CanCollapseFace(5.f, 1e-12f, 1u, 1u), "near-zero reference area invalid");
    Require(!CanCollapseFace(0.f, 4.f, 1u, 1u), "zero face area invalid");
    Require(!CanCollapseFace(std::numeric_limits<float>::infinity(), 4.f, 1u, 1u),
        "infinite current area invalid");
    Require(!CanCollapseFace(5.f, std::numeric_limits<float>::quiet_NaN(), 1u, 1u),
        "NaN reference area invalid");

    // This test's premise matches an indexed cab mesh: when the adjacent
    // triangle uses vertex 2, moving it would damage that other panel.
    // The policy refuses the collapse while the original vertex data remain
    // entirely owned by the physics-node mapping.
    const unsigned int shared_ref_count = 2u;
    Require(!CanCollapseFace(5.f, 4.f, shared_ref_count, 1u),
        "shared panel unexpectedly collapsed");

    std::cout << "PASS: safe cab triangle collapse policy\n";
    return 0;
}
