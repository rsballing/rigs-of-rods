// Minimal compile-time stand-in for RoR's application configuration.
// Used ONLY by the standalone thread-pool unit test, not the game.
#pragma once

#include <algorithm>
#include <cassert>

namespace Ogre {
struct Math {
    static int Clamp(int value, int lower, int upper)
    {
        return std::max(lower, std::min(value, upper));
    }
};
}

namespace RoR {
struct TestWorkerSetting {
    int getInt() const { return 4; }
    void setVal(int) {}
};

struct App {
    static TestWorkerSetting* app_num_workers;
};

inline TestWorkerSetting test_worker_setting;
inline TestWorkerSetting* App::app_num_workers = &test_worker_setting;

inline void LogFormat(const char*, ...) {}
}

#define ROR_ASSERT(expression) assert(expression)
