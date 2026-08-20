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

## Gripper operating procedure / 그리퍼 실행 절차

`cpp/`, `python/`, `ros2/` all drive the same firmware state machine in the
same order, regardless of which interface you pick.

세 인터페이스(`cpp/`, `python/`, `ros2/`) 모두 동일한 순서로 동일한 펌웨어
상태 머신을 구동합니다. 사용하는 인터페이스와 무관하게 아래 순서를
따르세요.

| # | Step / 단계 | Python | ROS2 | Protocol |
|---|---|---|---|---|
| 1 | Wire & power / 배선·전원 | USB↔RS485 adapter → gripper UART1, 115200 8N1 | 동일 | — |
| 2 | Connect / 연결 | `g.connect("/dev/ttyUSB0")` | `port:=` launch arg | opens the serial link |
| 3 | Activate / 활성화 | `g.activate()` | `ros2 service call .../activate std_srvs/srv/Trigger` | `rACT=1`, wait `gSTA=Active` |
| 4 | Home / 호밍 | `g.home()` | `.../home` service (or `auto_home:=true`) | `rHOM` rising edge, wait `gHOM=1` — **keep hands clear, fingers seek a hard stop / 손을 가까이 두지 마세요** |
| 5 | Move (open/close) / 이동 | `g.move_to(pos, speed, force, blocking=True)` | `.../move_to` (`MoveTo` service) | `rPR`/`rSP`/`rFR` + `rGTO` |
| 6 | Monitor status / 상태 모니터링 | `g.read_state()` | subscribe `/aidin_gripper_driver/state` | `gSTA`/`gOBJ`/`gPO`/`gFLT` |
| — | Recover from a fault/jam / 고장·끼임 복구 | `g.emergency_release(...)` then `g.activate()` again | `.../emergency_release` then `.../activate` | see each README's Troubleshooting table |

Minimal Python run-through (full script with progress logging:
[`python/examples/06_full_quickstart_demo.py`](python/examples/06_full_quickstart_demo.py)):

```python
from aidin_gripper import Gripper

with Gripper() as g:
    g.connect("/dev/ttyUSB0")     # 1-2. wire + connect
    g.activate()                  # 3. activate
    g.home()                      # 4. home (hands clear!)
    g.move_to(255, speed=200, force=128, blocking=True)   # 5. close
    g.move_to(0,   speed=200, force=128, blocking=True)   # 5. open
    print(g.read_state())         # 6. status
```

Full per-SDK instructions: [python/README.md](python/README.md) ·
[cpp/README.md](cpp/README.md) · [ros2/README.md](ros2/README.md).

## Quick start (Python)

```bash
git clone <this-repo> aidin-2f-gripper-ros2
cd aidin-2f-gripper-ros2/python

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -e .

cd examples
python 06_full_quickstart_demo.py /dev/ttyUSB0   # Windows: COM3
```

More examples (activate/home, single open+close, cyclic loop, status,
fault + emergency release): [python/README.md](python/README.md#run-the-examples).

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
