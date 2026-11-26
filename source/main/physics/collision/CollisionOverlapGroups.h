/*
    Rigs of Rods collision scheduling helper.
    The groups partition all actor bounding boxes into connected overlap
    components. Collision tasks in one component must not run concurrently:
    each task can apply forces to nodes owned by another member.
    This header intentionally has no Ogre dependencies, allowing unit tests.
*/
#pragma once

#include <cstddef>
#include <numeric>
#include <vector>

namespace RoR {

class CollisionOverlapGroups
{
public:
    // Returns true if at least one actor pair overlaps.
    // Include all actors, even those with no collision job: an actor without
    // its own job can still receive forces from multiple other actors.
    template <typename Overlaps>
    bool Rebuild(std::size_t actor_count, Overlaps overlaps)
    {
        m_parent.resize(actor_count);
        std::iota(m_parent.begin(), m_parent.end(), std::size_t(0));

        bool any_overlap = false;
        for (std::size_t i = 0; i < actor_count; ++i)
        {
            for (std::size_t j = i + 1; j < actor_count; ++j)
            {
                if (!overlaps(i, j))
                    continue;

                any_overlap = true;
                const std::size_t a = Root(i);
                const std::size_t b = Root(j);
                if (a != b)
                    m_parent[b] = a;
            }
        }
        return any_overlap;
    }

    // Read-only after Rebuild(), including when called by parallel tasks.
    std::size_t Root(std::size_t actor_index) const
    {
        while (actor_index != m_parent[actor_index])
            actor_index = m_parent[actor_index];
        return actor_index;
    }

private:
    std::vector<std::size_t> m_parent;
};

} // namespace RoR
