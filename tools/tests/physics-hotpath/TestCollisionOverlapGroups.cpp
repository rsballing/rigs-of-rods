#include <CollisionOverlapGroups.h>

#include <cstddef>
#include <iostream>
#include <utility>
#include <vector>

static bool Expect(bool condition, const char* description)
{
    if (!condition)
        std::cerr << "FAIL: " << description << "\n";
    return condition;
}

int main()
{
    RoR::CollisionOverlapGroups groups;

    // Connected overlapping cars must be assigned to one serial phase.
    const std::vector<std::pair<std::size_t, std::size_t>> chain = {
        {0, 1}, {1, 2}};
    const bool any_chain = groups.Rebuild(4, [&](std::size_t a, std::size_t b)
    {
        for (auto edge : chain)
            if (edge.first == a && edge.second == b) return true;
        return false;
    });
    if (!Expect(any_chain, "chain overlap detected") ||
        !Expect(groups.Root(0) == groups.Root(2), "transitive overlap grouped") ||
        !Expect(groups.Root(0) != groups.Root(3), "unrelated actor not grouped"))
        return 1;

    // Actor 1 can have no collision job of its own and still be a common
    // collision recipient. Jobs for actors 0 and 2 cannot run concurrently.
    if (!Expect(groups.Root(0) == groups.Root(2), "non-job bridge actor"))
        return 1;

    // Rebuild must clear prior connectivity; isolated actors still parallelize.
    const bool isolated = groups.Rebuild(4,
        [](std::size_t, std::size_t) { return false; });
    if (!Expect(!isolated, "isolation recognized") ||
        !Expect(groups.Root(0) != groups.Root(2), "stale groups cleared"))
        return 1;

    const std::vector<std::pair<std::size_t, std::size_t>> pairs = {
        {0, 1}, {2, 3}};
    const bool two_pairs = groups.Rebuild(4, [&](std::size_t a, std::size_t b)
    {
        for (auto edge : pairs)
            if (edge.first == a && edge.second == b) return true;
        return false;
    });
    if (!Expect(two_pairs, "two overlap components detected") ||
        !Expect(groups.Root(0) == groups.Root(1), "first pair") ||
        !Expect(groups.Root(2) == groups.Root(3), "second pair") ||
        !Expect(groups.Root(0) != groups.Root(2), "two pairs can run concurrently"))
        return 1;

    // More than nine vehicles exercises the thread-pool overflow path.
    groups.Rebuild(16, [](std::size_t a, std::size_t b)
    {
        return (a % 2 == 0) && (b == a + 1);
    });
    for (std::size_t i = 0; i < 16; i += 2)
    {
        if (!Expect(groups.Root(i) == groups.Root(i + 1), "large group pair") ||
            (i + 2 < 16 && !Expect(groups.Root(i) != groups.Root(i + 2),
                                  "large groups remain independent")))
            return 1;
    }
    if (!Expect(!groups.Rebuild(0, [](std::size_t, std::size_t) { return true; }),
                "empty actor list"))
        return 1;

    std::cout << "PASS: overlap components isolate independent vehicles, "
                 "serialize collision chains, and rebuild correctly\n";
}
