// Example 2: Repeatedly open and close the gripper.
//
// Usage:
//   ./02_open_close_loop /dev/ttyUSB0 [cycles]
//   02_open_close_loop.exe COM3 [cycles]
#include "aidin/gripper.hpp"

#include <atomic>
#include <csignal>
#include <iostream>

namespace {
std::atomic<bool> g_stop{false};
void onSignal(int) { g_stop.store(true); }
}

int main(int argc, char** argv) {
    const std::string port = (argc > 1) ? argv[1]
#if defined(_WIN32)
                                        : "COM3";
#else
                                        : "/dev/ttyUSB0";
#endif
    const int cycles = (argc > 2) ? std::atoi(argv[2]) : 5;

    std::signal(SIGINT, onSignal);

    try {
        aidin::Gripper g;
        g.connect(port);

        if (g.readState().stage != aidin::GripperStage::Active) {
            std::cout << "Activating ...\n";
            g.activate();
        }
        if (!g.readState().homed) {
            std::cout << "Homing ...\n";
            g.home();
        }

        for (int i = 0; i < cycles && !g_stop.load(); ++i) {
            std::cout << "Cycle " << (i + 1) << "/" << cycles << "\n";

            std::cout << "  close ...\n";
            g.moveTo(/*pos=*/255, /*speed=*/200, /*force=*/128, /*blocking=*/true);
            std::cout << "    " << g.readState() << "\n";

            if (g_stop.load()) break;

            std::cout << "  open ...\n";
            g.moveTo(/*pos=*/0, /*speed=*/200, /*force=*/128, /*blocking=*/true);
            std::cout << "    " << g.readState() << "\n";
        }

        std::cout << (g_stop.load() ? "Interrupted.\n" : "Done.\n");
    } catch (const std::exception& e) {
        std::cerr << "ERROR: " << e.what() << "\n";
        return 1;
    }
    return 0;
}
