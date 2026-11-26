#include <ThreadPool.h>

#include <atomic>
#include <cassert>
#include <functional>
#include <iostream>
#include <thread>
#include <vector>

int main()
{
    RoR::ThreadPool pool(4);
    const int batch_sizes[] = {0, 1, 2, 4, 8, 9, 10, 12, 32};

    // Includes 4-player workloads and overflow beyond the eight inline
    // worker handles. No task may run after Parallelize() has returned.
    for (int count : batch_sizes)
    {
        for (int iteration = 0; iteration < 100; ++iteration)
        {
            std::atomic<int> completed{0};
            std::vector<std::function<void()>> tasks;
            tasks.reserve(count);
            for (int i = 0; i < count; ++i)
                tasks.emplace_back([&completed]() { completed.fetch_add(1); });

            pool.Parallelize(tasks);
            if (completed.load() != count)
            {
                std::cerr << "FAILED: " << count << " tasks expected, "
                          << completed.load() << " completed\n";
                return 1;
            }
        }
    }

    // Different callers can use the same pool concurrently without
    // overwriting another caller's local/overflow task handles.
    std::atomic<int> concurrent_completed{0};
    auto caller = [&]() {
        for (int j = 0; j < 100; ++j)
        {
            std::vector<std::function<void()>> tasks;
            for (int i = 0; i < 12; ++i)
                tasks.emplace_back([&]() { concurrent_completed.fetch_add(1); });
            pool.Parallelize(tasks);
        }
    };
    std::thread first(caller), second(caller);
    first.join();
    second.join();
    if (concurrent_completed.load() != 2400)
    {
        std::cerr << "FAILED: concurrent task count = "
                  << concurrent_completed.load() << ", expected 2400\n";
        return 1;
    }

    std::cout << "PASS: 2 kHz task scheduler retains strict barriers, "
                 "four-player and overflow batches, and concurrent callers\n";
}
