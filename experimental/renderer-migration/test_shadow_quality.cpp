/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../../source/main/gfx/ShadowQualitySettings.h"
#include <iostream>
#include <stdexcept>

using namespace RoR::ShadowQualitySettings;

static void Require(bool value, const char* message)
{
    if (!value) throw std::runtime_error(message);
}

int main()
{
    Require(ClampDistance(-30) == 150, "negative shadow distance clamp");
    Require(ClampDistance(0) == 150, "zero shadow distance clamp");
    Require(ClampDistance(150) == 150, "minimum shadow distance");
    Require(ClampDistance(350) == 350, "preserve 350-unit legacy default");
    Require(ClampDistance(900) == 900, "extended shadow distance");
    Require(ClampDistance(1500) == 1500, "maximum shadow distance");
    Require(ClampDistance(30000) == 1500, "oversized shadow distance clamp");
    Require(DirectionalExtrusion(350) == 299.0f, "legacy directional extrusion distance");
    Require(DirectionalExtrusion(900) == 849.0f, "extended directional extrusion distance");

    Require(TerrainPcfWidth(0) == 2, "low quality uses four taps");
    Require(TerrainPcfWidth(1) == 2, "medium quality uses four taps");
    Require(TerrainPcfWidth(2) == 3, "high quality uses nine taps");
    Require(TerrainPcfWidth(3) == 3, "ultra quality uses nine taps");
    std::cout << "PASS: shadow range and terrain PCF quality policy\n";
}
