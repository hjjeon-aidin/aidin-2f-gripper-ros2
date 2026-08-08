# AIDIN 2F Gripper — Host SDKs & ROS2 Driver

Host-side software for the **AIDIN 2-finger BLDC gripper** (DH-Robotics
compatible Modbus RTU, 115200 8N1, slave ID 1). Everything here talks to the
gripper over a USB↔RS485 adapter — no vendor DLLs, no external Modbus
library, no network access at build time.

AIDIN 2지 BLDC 그리퍼용 호스트 소프트웨어 모음입니다. USB-RS485 어댑터만
있으면 동작하며, 외부 Modbus 라이브러리 의존성이 없습니다.

## What's inside / 구성

| Directory | What it is | Docs |
|---|---|---|
| [`cpp/`](cpp/) | `aidin::Gripper` C++17 SDK — self-contained Modbus RTU framing (termios / Win32). Builds on Ubuntu & Windows with one CMake command | [README](cpp/README.md) · [MANUAL](cpp/MANUAL.md) |
| [`python/`](python/) | Pure-Python SDK (`pyserial`) — same API surface as the C++ SDK | [README](python/README.md) |
| [`ros2/`](ros2/) | ROS2 packages: `aidin_gripper_driver` (rclcpp node), `aidin_gripper_msgs`, `aidin_gripper_examples`. State topic @ 50 Hz + services (`activate`/`home`/`move_to`/`emergency_release`/…) | [README](ros2/README.md) |

## Quick start (ROS2)

```bash
git clone <this-repo> aidin-2f-gripper-ros2
cd aidin-2f-gripper-ros2

mkdir -p ~/ros2_ws/src
ln -s $(pwd)/ros2/aidin_gripper_msgs     ~/ros2_ws/src/
ln -s $(pwd)/ros2/aidin_gripper_driver   ~/ros2_ws/src/
ln -s $(pwd)/ros2/aidin_gripper_examples ~/ros2_ws/src/

cd ~/ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 launch aidin_gripper_driver aidin_gripper.launch.py port:=/dev/ttyUSB0
```

Full instructions (parameters, services, troubleshooting): [ros2/README.md](ros2/README.md)

> The `aidin_gripper_driver` build pulls in [`cpp/`](cpp/) via
> `add_subdirectory` — keep the repo layout intact (or pass
> `-DAIDIN_SDK_DIR=/abs/path/to/cpp`).

## Safety / 주의

The gripper applies real torque to mechanical fingers. Keep hands clear
during homing (fingers seek a hard stop), and clear the workspace before
launching with `auto_home:=true`.

그리퍼는 실제 토크로 핑거를 구동합니다. 호밍 중에는 손을 가까이 두지 말고,
`auto_home:=true` 로 실행하기 전에 작업 공간을 비워 주세요.

## License

MIT — see [LICENSE](LICENSE).

---

*AIDIN Robotics — BLDC 모터 기반 그리퍼/액추에이터 솔루션*
