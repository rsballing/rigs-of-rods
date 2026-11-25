/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../../source/main/physics/flex/CabMeshSafety.h"
#include <cassert>
#include <iostream>
#include <limits>

using RoR::CabMeshSafety::CanCollapseFace;

int main()
{
    assert(CanCollapseFace(5.f, 4.f, 1u, 1u));
    assert(!CanCollapseFace(5.f, 4.f, 2u, 1u));
    assert(!CanCollapseFace(5.f, 4.f, 1u, 2u));
    assert(!CanCollapseFace(5.f, 4.f, 2u, 2u));
    assert(!CanCollapseFace(4.f, 4.f, 1u, 1u));
    assert(!CanCollapseFace(3.f, 4.f, 1u, 1u));
    assert(!CanCollapseFace(5.f, 0.f, 1u, 1u));
    assert(!CanCollapseFace(5.f, 1e-12f, 1u, 1u));
    assert(!CanCollapseFace(0.f, 4.f, 1u, 1u));
    assert(!CanCollapseFace(std::numeric_limits<float>::infinity(), 4.f, 1u, 1u));
    assert(!CanCollapseFace(5.f, std::numeric_limits<float>::quiet_NaN(), 1u, 1u));
    std::cout << "PASS: safe cab triangle collapse policy\n";
}
