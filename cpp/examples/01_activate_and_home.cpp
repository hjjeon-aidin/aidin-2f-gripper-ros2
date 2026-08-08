// Example 1: Activate and home the Aidin gripper.
//
// Usage:
//   ./01_activate_and_home /dev/ttyUSB0      (Linux)
//   01_activate_and_home.exe COM3            (Windows)
#include "aidin/gripper.hpp"

#include <iostream>

int main(int argc, char** argv) {
    const std::string port = (argc > 1) ? argv[1]
#if defined(_WIN32)
                                        : "COM3";
#else
                                        : "/dev/ttyUSB0";
#endif

    try {
        aidin::Gripper g;
        std::cout << "Connecting to " << port << " ...\n";
        g.connect(port);                       // 115200 8N1, slave ID 1

        std::cout << "Activating ...\n";
        g.activate();
        std::cout << "  -> state: " << g.readState() << "\n";

        std::cout << "Homing (this may take a few seconds) ...\n";
        g.home();
        std::cout << "  -> state: " << g.readState() << "\n";

        std::cout << "Done.\n";
    } catch (const std::exception& e) {
        std::cerr << "ERROR: " << e.what() << "\n";
        return 1;
    }
    return 0;
}
