/*
 * Rigs of Rods shadow quality policy
 * SPDX-License-Identifier: GPL-3.0-or-later
 *
 * Pure helpers for the existing OGRE 1.x PSSM path.
 * No renderer/OGRE dependency, so they can be unit tested.
 */
#pragma once

namespace RoR {
namespace ShadowQualitySettings {

inline int ClampDistance(int distance)
{
    return distance < 150 ? 150 : (distance > 1500 ? 1500 : distance);
}

// Preserve the old value with default settings.
inline float DirectionalExtrusion(int distance)
{
    return static_cast<float>(ClampDistance(distance) - 51);
}

// The quality slider controls terrain PCF samples: 2x2 at low/medium,
// 3x3 at high, and 5x5 at ultra. Ultra is intentionally expensive (25 taps)
// and can be disabled on older graphics cards by lowering shadow quality.
inline int TerrainPcfWidth(int quality)
{
    if (quality >= 3) return 5;
    return quality >= 2 ? 3 : 2;
}

} // namespace ShadowQualitySettings
} // namespace RoR
