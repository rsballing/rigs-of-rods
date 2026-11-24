/*
 * Rigs of Rods experimental SkyX lighting math
 * SPDX-License-Identifier: GPL-3.0-or-later
 */
#pragma once

#include <cmath>

namespace RoR {
namespace SkyLightingMath {

struct RGB { float r, g, b; };

inline float Clamp01(float v)
{
    if (!std::isfinite(v) || v <= 0.f) return 0.f;
    if (v >= 1.f) return 1.f;
    return v;
}

// SkyX uses a 0..1 mapping of sun elevation, with the horizon at 0.5.
// Fade the direct light smoothly across twilight instead of leaving a
// full-strength directional sun shining after it goes below the horizon.
inline float SunVisibility(float sky_point)
{
    const float t = Clamp01((sky_point - 0.43f) / (0.67f - 0.43f));
    return t * t * (3.f - 2.f * t);
}

// Combines the SkyX sunlight gradient with the day/night visibility.
// Clamps for the OGRE 1.x fixed-function material path. This is NOT PBR
// and does not change terrain lightmaps or the map's ambient light.
inline RGB DirectionalSunlight(float sky_point, RGB skyx_gradient)
{
    const float visibility = SunVisibility(sky_point);
    return {Clamp01(skyx_gradient.r * visibility),
            Clamp01(skyx_gradient.g * visibility),
            Clamp01(skyx_gradient.b * visibility)};
}

} // namespace SkyLightingMath
} // namespace RoR
