# AIDIN Gripper — ROS2 Driver / ROS2 드라이버

```
 █████╗ ██╗██████╗ ██╗███╗   ██╗     ██████╗ ██████╗ ██╗██████╗ ██████╗ ███████╗██████╗
██╔══██╗██║██╔══██╗██║████╗  ██║    ██╔════╝ ██╔══██╗██║██╔══██╗██╔══██╗██╔════╝██╔══██╗
███████║██║██║  ██║██║██╔██╗ ██║    ██║  ███╗██████╔╝██║██████╔╝██████╔╝█████╗  ██████╔╝
██╔══██║██║██║  ██║██║██║╚██╗██║    ██║   ██║██╔══██╗██║██╔═══╝ ██╔═══╝ ██╔══╝  ██╔══██╗
██║  ██║██║██████╔╝██║██║ ╚████║    ╚██████╔╝██║  ██║██║██║     ██║     ███████╗██║  ██║
╚═╝  ╚═╝╚═╝╚═════╝ ╚═╝╚═╝  ╚═══╝     ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝     ╚═╝     ╚══════╝╚═╝  ╚═╝
            BLDC-driven gripper · DH-Robotics RTU · STM32G431CB @ 160 MHz
```

[![ROS2](https://img.shields.io/badge/ROS2-26.04%20LTS%20%2F%20Jazzy%20%2F%20Humble-22314E)](https://docs.ros.org/)
[![Ubuntu 26.04](https://img.shields.io/badge/Ubuntu-26.04-E95420)](https://releases.ubuntu.com/)
[![Build: colcon](https://img.shields.io/badge/build-colcon-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()

## Overview / 개요

This workspace exposes the **AIDIN BLDC gripper** firmware (DH-Robotics
Modbus RTU compatible) on ROS2. The driver wraps our standalone
[`aidin::Gripper` C++ SDK](../cpp/) — which implements Modbus RTU framing
in-tree (**no external Modbus library**) — and publishes live state at
50 Hz while accepting commands over standard ROS2 services.

본 워크스페이스는 **AIDIN BLDC 그리퍼 펌웨어** (DH-Robotics 호환 Modbus RTU)
를 ROS2 환경에서 제어할 수 있도록 한 드라이버입니다. C++ SDK
[`aidin::Gripper`](../cpp/) 위에 토픽·서비스 인터페이스를 입혔으며, SDK 는
Modbus RTU 프레이밍을 자체 구현해 **외부 라이브러리 의존성이 없습니다**.
레지스터 계약의 정본은 펌웨어 저장소(`aidin-bldc-firmware`)의
`docs/protocol/protocol.md` (작성 기준 v1.10.3) 입니다.

---

## Firmware Stack

```
┌─────────────────────────────────────────────────────────┐
│  Your ROS2 graph                                         │
│  ┌─────────────────────────┐                             │
│  │  aidin_gripper_driver   │ ── /aidin_gripper_driver/state         (50 Hz)
│  │  rclcpp node            │ ── /aidin_gripper_driver/activate      (Trigger)
│  │                         │ ── /aidin_gripper_driver/home · /stop  (Trigger)
│  │                         │ ── /aidin_gripper_driver/fault_clear   (Trigger)
│  │                         │ ── /aidin_gripper_driver/move_to       (MoveTo)
│  │                         │ ── /aidin_gripper_driver/emergency_release
│  └────────┬────────────────┘ ── /aidin_gripper_driver/dev_cmd  (opt-out)
│           │                                              │
│           │  aidin::Gripper  (C++17 SDK,                 │
│           │   self-contained Modbus RTU framing)         │
└───────────┼──────────────────────────────────────────────┘
            │  Modbus RTU  115200 8N1  (RS485)
            ▼
┌─────────────────────────────────────────────────────────┐
│  AIDIN BLDC firmware  (STM32G431CB / Cortex-M4 @160MHz) │
│   · FreeModbus slave   · DH-Robotics register map        │
│   · ST MCSDK FOC       · TIM7 control loop               │
└─────────────────────────────────────────────────────────┘
```

---

## Compatible Operating Systems

- **Ubuntu 26.04** — ROS2 2026 LTS (primary target)
- Ubuntu 24.04 (Noble) — ROS2 Jazzy
- Ubuntu 22.04 (Jammy) — ROS2 Humble (legacy)

---

## Dependencies

| Component | Version | Source |
|---|---|---|
| ROS2         | desktop / base | `apt install ros-<distro>-desktop` |
| CMake        | ≥ 3.16 | `apt install cmake` |
| Build essentials | gcc-11+ | `apt install build-essential` |

If ROS2 was installed correctly, every required package is already
present. The C++ SDK implements Modbus RTU framing in-tree
([`cpp/src/modbus_rtu.cpp`](../cpp/src/modbus_rtu.cpp)) — **no
external Modbus library, no network access at build time**.

---

## Warning

- The AIDIN BLDC gripper applies real torque to mechanical fingers. Keep
  hands clear during `home()`, and use `emergency_release` to free a
  stuck object before re-enabling the motor.
- Homing pushes the fingers against a hard stop — make sure nothing is
  in the workspace before launching with `auto_home:=true`.
- Visit **<http://aidin-robotics.example>** for the hardware manual.

---

## Build & Run

```bash
# 1. Clone this repo (this gives you cpp/ + ros2/ + urdf/ side by side)
git clone <this-repo> aidin-2f-gripper-sdk
cd aidin-2f-gripper-sdk

# 2. Symlink the ROS2 packages into your workspace
mkdir -p ~/ros2_ws/src
ln -s $(pwd)/ros2/aidin_gripper_msgs        ~/ros2_ws/src/
ln -s $(pwd)/ros2/aidin_gripper_driver      ~/ros2_ws/src/
ln -s $(pwd)/ros2/aidin_gripper_examples    ~/ros2_ws/src/
ln -s $(pwd)/urdf                           ~/ros2_ws/src/

# 3. Build
cd ~/ros2_ws
colcon build --symlink-install
#   개발자 명령 서비스(~/dev_cmd) 제거 빌드:
#   colcon build --symlink-install --cmake-args -DAIDIN_ENABLE_DEV_CMD=OFF
source install/setup.bash

# 4. Run
ros2 launch aidin_gripper_driver aidin_gripper.launch.py port:=/dev/ttyUSB0
```

In another terminal:
```bash
# Watch state changes
ros2 run aidin_gripper_examples state_listener

# Repeat open-close 5 times
ros2 run aidin_gripper_examples open_close_loop 5

# Interactive REPL
ros2 run aidin_gripper_examples interactive_cli
```

---

## ROS2 Topic

| Topic                                  | Type                                       | Frequency |
|----------------------------------------|--------------------------------------------|-----------|
| `/aidin_gripper_driver/state`          | `aidin_gripper_msgs/msg/GripperState`      | 50 Hz (configurable) |

### `GripperState` fields

| Field               | Type     | Notes |
|---------------------|----------|-------|
| `header`            | `std_msgs/Header` | stamp + `frame_id="aidin_gripper"` |
| `activated`         | bool     | gACT — motor enabled |
| `homed`             | bool     | gHOM |
| `go_to_active`      | bool     | gGTO |
| `stage`             | uint8    | `STAGE_RESET=0`, `STAGE_ACTIVATING=1`, `STAGE_ACTIVE=3` |
| `object_state`      | uint8    | `OBJECT_MOVING=0`, `OPEN_CONTACT=1`, `CLOSED_CONTACT=2`, `AT_TARGET=3` |
| `fault`             | uint8    | gFLT (0 = OK) |
| `latched_fault`     | uint8    | gFLTO (sticky) |
| `position_echo`     | uint8    | gPR (echo of last `rPR`) |
| `position`          | uint8    | gPO — **0 = fully open, 255 = fully closed** |
| `current`           | uint8    | gCU (0..255 raw) |
| `speed`             | uint8    | gSP (0..255 raw) |
| `voltage`           | float32  | gV × 0.1 [V] |

---

## ROS2 Services

| Service                                          | Type                                         | Purpose |
|--------------------------------------------------|----------------------------------------------|---------|
| `/aidin_gripper_driver/activate`                 | `std_srvs/srv/Trigger`                       | Set `rACT=1`, wait until `gSTA=Active` |
| `/aidin_gripper_driver/deactivate`               | `std_srvs/srv/Trigger`                       | Set `rACT=0` |
| `/aidin_gripper_driver/home`                     | `std_srvs/srv/Trigger`                       | Rising-edge `rHOM`, block until `gHOM=1` |
| `/aidin_gripper_driver/stop`                     | `std_srvs/srv/Trigger`                       | Stop an in-flight motion (`rGTO=0`), keep holding |
| `/aidin_gripper_driver/fault_clear`              | `std_srvs/srv/Trigger`                       | Clear the latched fault `gFLTO` (DEV_CMD 0x07) |
| `/aidin_gripper_driver/move_to`                  | `aidin_gripper_msgs/srv/MoveTo`              | Position / speed / force command. Same-position re-issue pulses `rGTO` (protocol v1.9.1) |
| `/aidin_gripper_driver/emergency_release`        | `aidin_gripper_msgs/srv/EmergencyRelease`    | rATR pulse release (open or close direction) |
| `/aidin_gripper_driver/dev_cmd`                  | `aidin_gripper_msgs/srv/DevCmd`              | Developer command passthrough (firmware repo `protocol.md` §3). **Compile out with `-DAIDIN_ENABLE_DEV_CMD=OFF`** |

### Service request structure

| Service              | Request                                                                | Value range |
|----------------------|------------------------------------------------------------------------|-------------|
| `activate`           | _(empty)_                                                              | — |
| `deactivate`         | _(empty)_                                                              | — |
| `home`               | _(empty)_                                                              | — |
| `stop`               | _(empty)_                                                              | — |
| `fault_clear`        | _(empty)_                                                              | — |
| `move_to`            | `position` (uint8), `speed` (uint8), `force` (uint8), `blocking` (bool), `timeout_sec` (float32) | position 0..255 (0=open, 255=close); speed 0..255; force 0..255 |
| `emergency_release`  | `close_direction` (bool)                                               | false = open, true = close |
| `dev_cmd`            | `cmd` (uint8), `timeout_sec` (float32)                                 | cmd = protocol.md §3 코드 (예: 0x0A STROKE_CAL — timeout_sec 25 권장) |

### Examples from the command line

```bash
ros2 service call /aidin_gripper_driver/activate std_srvs/srv/Trigger
ros2 service call /aidin_gripper_driver/home     std_srvs/srv/Trigger

ros2 service call /aidin_gripper_driver/move_to aidin_gripper_msgs/srv/MoveTo \
    "{position: 200, speed: 180, force: 128, blocking: true, timeout_sec: 5.0}"

ros2 service call /aidin_gripper_driver/emergency_release \
    aidin_gripper_msgs/srv/EmergencyRelease "{close_direction: false}"
```

---

## Parameters

Set via `config/default.yaml` or on the command line.

| Parameter            | Type    | Default          | Description |
|----------------------|---------|------------------|-------------|
| `port`               | string  | `/dev/ttyUSB0`   | Serial port (`COM3` on Windows) |
| `baudrate`           | int     | `115200`         | Modbus RTU baud |
| `parity`             | string  | `N`              | `N` / `E` / `O` |
| `slave_id`           | int     | `1`              | 1..247 |
| `publish_rate_hz`    | double  | `50.0`           | `/state` publish rate |
| `auto_activate`      | bool    | `true`           | Call `activate()` at startup |
| `auto_home`          | bool    | `false`          | Call `home()` at startup (be careful — moves the fingers) |

---

## Workspace Layout

```
aidin-2f-gripper-sdk/
├── cpp/                           # aidin::Gripper C++17 SDK (self-contained Modbus RTU)
├── python/                        # pure-Python SDK (pyserial)
├── ros2/
│   ├── aidin_gripper_msgs/        # msg + srv definitions
│   │   ├── msg/GripperState.msg
│   │   └── srv/{MoveTo,EmergencyRelease,DevCmd}.srv
│   ├── aidin_gripper_driver/      # rclcpp node, launch, config
│   │   ├── src/gripper_node.cpp
│   │   ├── launch/aidin_gripper.launch.py
│   │   └── config/default.yaml
│   └── aidin_gripper_examples/    # rclpy CLI clients
│       └── aidin_gripper_examples/{state_listener,open_close_loop,interactive_cli}.py
└── urdf/                          # `aidin_gripper_description` ROS2 package — URDF + meshes
    ├── urdf/aidin_2f_gripper.urdf     # SolidWorks-exported 2-finger prismatic model
    ├── urdf/aidin_2f_gripper.csv      # SW2URDF link/joint export record (reference only)
    ├── meshes/{gripper_base,gripper_joint_1,gripper_joint_2}.STL
    ├── config/joint_names_aidin_2f_gripper.yaml
    └── launch/{display,gazebo}.launch.py
```

---

## Troubleshooting

| Symptom                                       | Likely cause                                          | Fix |
|-----------------------------------------------|-------------------------------------------------------|-----|
| `connect failed: ... Permission denied`       | User not in `dialout`                                 | `sudo usermod -a -G dialout $USER` then re-login |
| `/dev/ttyUSB0` disappears right after plug-in | Ubuntu `brltty` grabbing the USB-serial adapter       | `sudo apt remove brltty` |
| Driver starts but `/state` never publishes    | Wrong baud / parity / slave ID, or RS485 A↔B swapped  | Try `parity:=E`, swap RS485 lines |
| State rate stutters below `publish_rate_hz`   | FTDI latency_timer at its 16 ms default               | `echo 1 \| sudo tee /sys/bus/usb-serial/devices/ttyUSB0/latency_timer` (udev 규칙으로 영속화 권장) |
| `auto_activate failed`                        | Power supply too low, or latched fault                | Read `latched_fault` field in `/state`, then call `fault_clear` |
| `move_to` reports `success=false`             | Mechanical jam, or `rATR` still latched               | Call `activate` to clear the latch |
| `colcon build` cannot find SDK                | Workspace layout differs                              | Pass `--cmake-args -DAIDIN_SDK_DIR=/abs/path/to/aidin-2f-gripper-sdk/cpp` |

포트 이름 고정 + latency 자동 설정 udev 규칙 예 (`/etc/udev/rules.d/99-aidin-gripper.rules`,
idVendor/idProduct 는 `lsusb` 로 확인):
```
SUBSYSTEM=="tty", ATTRS{idVendor}=="0403", ATTRS{idProduct}=="6001", \
  SYMLINK+="aidin_gripper", ATTR{device/latency_timer}="1"
```

---

## Related Documentation

- [SDK quick-start (`cpp/README.md`)](../cpp/README.md)
- [SDK developer manual (`cpp/MANUAL.md`)](../cpp/MANUAL.md)
- Register map mirror: [`cpp/include/aidin/registers.hpp`](../cpp/include/aidin/registers.hpp)
  (정본은 펌웨어 저장소 `aidin-bldc-firmware` 의 `docs/protocol/protocol.md`)

---

## Contact

E-mail: firmware@aidin.example  
Homepage: <http://aidin-robotics.example>

---

*AIDIN Robotics — BLDC 모터 기반 그리퍼/액추에이터 솔루션*
