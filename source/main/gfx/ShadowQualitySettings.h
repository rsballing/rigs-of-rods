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

// Render the stock 2x2 PCF at low/medium; high/ultra use a 3x3
// filter for smoother terrain-shadow transitions.
inline int TerrainPcfWidth(int quality)
{
    return quality >= 2 ? 3 : 2;
}

} // namespace ShadowQualitySettings
} // namespace RoR
