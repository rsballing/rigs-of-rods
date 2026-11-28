/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../../source/main/gfx/SkyLightingMath.h"
#include <cmath>
#include <iostream>
#include <limits>
#include <stdexcept>

using RoR::SkyLightingMath::RGB;
using RoR::SkyLightingMath::SunVisibility;
using RoR::SkyLightingMath::DirectionalSunlight;

static void Require(bool pass, const char* message)
{
    if (!pass) throw std::runtime_error(message);
}
static bool Near(float a, float b, float tolerance=0.0001f)
{
    return std::fabs(a-b) <= tolerance;
}
int main()
{
    const RGB white{1.f, 1.f, 1.f};
    const auto night = DirectionalSunlight(0.2f, white);
    Require(Near(night.r, 0.f) && Near(night.g, 0.f) && Near(night.b, 0.f), "night must be dark");
    const auto midday = DirectionalSunlight(1.f, white);
    Require(Near(midday.r, 1.f) && Near(midday.g, 1.f), "midday must show full gradient");
    const auto dawn = DirectionalSunlight(0.5f, RGB{1.f, 0.65f, 0.35f});
    Require(dawn.r > dawn.g && dawn.g > dawn.b, "sunrise should retain warm hue");
    Require(dawn.r > 0.f && dawn.r < 1.f, "twilight should smoothly fade");
    Require(Near(SunVisibility(0.43f), 0.f), "fade should start at zero");
    Require(Near(SunVisibility(0.67f), 1.f), "fade should finish at one");
    for (int i=0; i<=1000; ++i)
    {
        float sky_point = i / 1000.f;
        RGB s = DirectionalSunlight(sky_point, RGB{5.f, 0.8f, 0.7f});
        Require(s.r>=0.f && s.r<=1.f && s.g>=0.f && s.g<=1.f && s.b>=0.f && s.b<=1.f, "channels out of range");
        if(i>0) Require(SunVisibility(sky_point)+0.00001f >= SunVisibility((i-1)/1000.f), "non-monotonic visibility");
    }
    const float nan = std::numeric_limits<float>::quiet_NaN();
    const auto invalid = DirectionalSunlight(nan, RGB{nan, 1.f, -1.f});
    Require(Near(invalid.r, 0.f) && Near(invalid.g, 0.f) && Near(invalid.b, 0.f), "invalid input must not poison lighting");
    const auto high = DirectionalSunlight(2.f, RGB{3.f, -2.f, 0.4f});
    Require(Near(high.r, 1.f) && Near(high.g, 0.f) && Near(high.b, 0.4f), "channels must clamp");
    std::cout << "PASS: SkyX sunlight test cases and 1001-sample range sweep\n";
}
