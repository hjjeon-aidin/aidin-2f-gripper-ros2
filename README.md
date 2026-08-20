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

## Reference for AI agents / AI 참고 자료

This section is a single, self-contained technical reference for an AI
assistant integrating this gripper into a *different* codebase (a new
language, a different framework) that doesn't want to explore this whole
repo. It restates the protocol precisely enough to write a correct client
from scratch, then points at the three reference implementations that
already exist here.

### What this device is

- AIDIN 2-finger BLDC gripper, DH-Robotics-compatible **Modbus RTU** slave.
- Transport: RS485 over a USB adapter. Default link: **115200 baud, 8 data
  bits, no parity, 1 stop bit (8N1)**, slave address **1** (changeable,
  1..247).
- Function codes the SDKs in this repo actually use: **0x03** (Read Holding
  Registers) and **0x06** (Write Single Register). Every register below is
  a 16-bit holding register at its protocol-level (PDU) address.
- The full authoritative protocol spec (fault code table, CAN-side sensor
  commands, etc.) lives in a separate firmware repo (`aidin-bldc-firmware`,
  `docs/protocol/protocol.md`) that is **not** included here — only what's
  mirrored below and in
  [`cpp/include/aidin/registers.hpp`](cpp/include/aidin/registers.hpp) /
  [`python/aidin_gripper/registers.py`](python/aidin_gripper/registers.py)
  is guaranteed accurate for this repo's version.

### Register map (everything the SDKs in this repo touch)

| Addr | R/W | Field | Meaning |
|---|---|---|---|
| `0x0100` | W | `ACTION` | bitfield — see below |
| `0x0101` | W | `SPEED` (`rSP`) | 0..255 |
| `0x0102` | W | `FORCE` (`rFR`) | 0..255 (current/force limit) |
| `0x0103` | W | `POSITION` (`rPR`) | 0..255 — **0 = fully open, 255 = fully closed** |
| `0x0200` | R | `STATUS` | bitfield — see below |
| `0x0201` | R | `FAULT` (`gFLT`) | 0 = OK, nonzero = active fault code |
| `0x0202` | R | `POS_ECHO` (`gPR`) | echo of the last `rPR` written |
| `0x0203` | R | `POS_ACTUAL` (`gPO`) | actual position 0..255 |
| `0x0204` | R | `CUR_ACTUAL` (`gCU`) | actual current 0..255 (raw) |
| `0x0205` | R | `SPD_ACTUAL` (`gSP`) | actual speed 0..255 (raw) |
| `0x0206` | R | `VOLTAGE` (`gV`) | supply voltage — register × 0.1 = volts |
| `0x0207` | R | `FAULT_LATCH` (`gFLTO`) | sticky fault code (persists after `gFLT` clears) |
| `0x0182` | R/W | `CFG_MB_ADDR` | Modbus slave address, 1..247 (factory config — see "Multiple grippers on one bus" in [python/README.md](python/README.md#multiple-grippers-on-one-bus-rs485-multi-drop)) |
| `0x0180` / `0x0181` | R/W | `DEV_CMD` / `DEV_STATUS` | factory/developer command channel — **not** for normal operation; consult firmware docs before using |

`STATUS`..`FAULT_LATCH` (`0x0200`..`0x0207`, 8 registers) are meant to be
read **in one block transaction**, not one register at a time — that's
what every SDK's `read_state()` / `readState()` does.

### `ACTION` bits (write, `0x0100`)

| Bit | Name | Type | Meaning |
|---|---|---|---|
| 0 | `rACT` | level | 1 = request activation. The firmware ignores nearly every other command while this is 0. |
| 1 | `rHOM` | **rising edge** | trigger homing. Must go 0→1; holding it at 1 does nothing again. |
| 3 | `rGTO` | level, edge-sensitive re-trigger | 1 = go to `rPR`. Re-commanding the *same* position while `rGTO` is already 1 is ignored — pulse it 0→1 to force re-execution (firmware ≥ v1.9.1). |
| 4 | `rATR` | **rising edge** | emergency auto-release. Only processed while `rACT=1`. |
| 5 | `rADR` | level | auto-release direction: 0 = open, 1 = close. Set before/with the `rATR` pulse. |

Because `ACTION` is one register, every write replaces *all* of these bits
at once — there is no way to set one bit without knowing (or explicitly
re-asserting) the others. This is also why `emergency_release()` writing
`rATR` (without `rACT`) leaves the device with `rACT=0`: the *next*
`activate()` call is what clears the release latch and restores normal
`move_to()`/`moveTo()` behavior.

### `STATUS` bits (read, `0x0200`)

| Bits | Name | Meaning |
|---|---|---|
| 0 | `gACT` | activated |
| 1 | `gHOM` | homed |
| 3 | `gGTO` | echo of `rGTO` |
| 4-5 | `gSTA` | `00`=Reset, `01`=Activating, `11`=Active |
| 6-7 | `gOBJ` | `00`=Moving, `01`=stopped on object while opening, `10`=stopped on object while closing, `11`=at target |

### Protocol invariants an integration needs to get right

- **Position is inverted from what you might guess**: `0` = open, `255` = closed.
- `rHOM`/`rATR` are edge-triggered, not level-triggered — write them low,
  then high (every SDK here waits ~20 ms between the two writes), or the
  firmware never sees a transition.
- Re-issuing a move to the *same* position while already moving there
  needs an `rGTO` 0→1 pulse, not just rewriting `rGTO=1`.
- `emergency_release()`/`emergencyRelease()` drops `rACT` — call
  `activate()` again afterward, or every subsequent command is ignored.
- Treat a full status read (8 registers, `0x0200`-`0x0207`) as one
  transaction; don't split it into 8 separate reads, both for latency and
  because the fields are meant to be read as one consistent snapshot.
- **RS485 multi-drop**: several grippers can share one physical bus if
  each has a distinct `CFG_MB_ADDR`, but only one Modbus transaction may
  be in flight on the wire at a time. All three SDKs in this repo share
  one underlying serial connection per port path and serialize
  transactions with a lock/mutex whenever more than one logical device
  object targets the same port — don't open the port twice from
  independent client objects, and don't fire transactions from multiple
  threads without equivalent serialization if you re-implement this
  elsewhere.

### Multi-drop: sharing one connection across slave IDs (the pattern used here)

Naively giving each logical gripper its own client object breaks as soon
as two of them target the same physical port: opening a COM port twice
fails outright on Windows, and on Linux it can silently interleave two
independent handles' bytes on the wire and corrupt every transaction.
This repo solves it the same way in both compiled SDKs — the pattern to
copy if you're writing a fourth client:

- A **process-wide registry keyed by port path** (`{port_path: shared_transport}`)
  holds one already-open transport per physical port.
- `connect(port, ..., slave_id)` looks the port up in the registry. Not
  found → open it, create the shared transport, register it. Found →
  reuse it, but reject the call if `baudrate`/`parity` don't match what's
  already open (those are properties of the wire, not of one device).
- Each logical `Gripper` object keeps only its own `slave_id` plus a
  reference to the shared transport — never its own OS handle.
- The shared transport owns a **mutex/lock held only around a single
  register read or write**, not around a whole `activate()`/`home()`
  call — so gripper A's 15-second homing doesn't block gripper B's status
  polling.
- The transport is closed automatically once every `Gripper` sharing it
  has disconnected (reference counting — Python does it explicitly with
  an int counter; C++ leans on `std::shared_ptr`/`std::weak_ptr` and gets
  this for free).

Reference implementations:
[`python/aidin_gripper/gripper.py`](python/aidin_gripper/gripper.py)
(`_SharedPort` / `_port_registry`) and
[`cpp/src/gripper.cpp`](cpp/src/gripper.cpp) (`SharedBus` /
`portRegistry()`), demonstrated end-to-end in
[`python/examples/07_multi_gripper_two_slaves.py`](python/examples/07_multi_gripper_two_slaves.py).

**Scope limit**: the registry lives in one process's memory, so this only
shares a port across multiple client objects *within the same process*.
Two independent OS processes (e.g. two separately-launched
`aidin_gripper_driver` ROS2 node instances) each still open the port for
themselves and will conflict if pointed at the same physical port — the
ROS2 driver as shipped is one node = one gripper = one port; running two
grippers on one bus under ROS2 currently means giving each its own
port/adapter, not sharing one, unless you extend the driver to own
multiple slave IDs itself.

### Minimal integration algorithm (language-agnostic)

```
open(port, baud=115200, 8N1)

write(ACTION, rACT)                            # request activation
poll read(STATUS) until gSTA == Active          # or timeout -> error

write(ACTION, rACT)                            # ensure rHOM low
sleep(20ms)
write(ACTION, rACT | rHOM)                     # rising edge
sleep(100ms)                                    # let firmware clear gHOM first
poll read(STATUS..FAULT_LATCH) until gHOM==1 or gFLT!=0   # or timeout -> error

write(SPEED, speed); write(FORCE, force); write(POSITION, pos)
write(ACTION, rACT | rGTO)
if blocking:
    poll read(STATUS..FAULT_LATCH) until gOBJ != Moving or gFLT!=0   # or timeout -> error

# status monitoring: read(STATUS..FAULT_LATCH) on whatever cadence you need
# fault/jam recovery: write(ACTION, rATR [| rADR]) briefly, then re-run the activate step
```

### Same algorithm, three ways (already implemented here)

| Step | Python (`python/aidin_gripper`) | C++ (`aidin::Gripper`, `cpp/`) | ROS2 (`aidin_gripper_driver`) |
|---|---|---|---|
| Connect | `g.connect(port, baudrate, parity, slave_id)` | `g.connect(port, baud, parity, slaveId)` | `port`/`baudrate`/`parity`/`slave_id` params |
| Activate | `g.activate()` | `g.activate()` | `/activate` (`Trigger`) |
| Home | `g.home()` | `g.home()` | `/home` (`Trigger`) |
| Move | `g.move_to(pos, speed, force, blocking)` | `g.moveTo(pos, speed, force, blocking)` | `/move_to` (`MoveTo`) |
| Status | `g.read_state()` → `GripperState` | `g.readState()` → `GripperState` | subscribe `/state` (`GripperState` msg, 50 Hz) |
| Emergency release | `g.emergency_release(close_direction)` | `g.emergencyRelease(closeDirection)` | `/emergency_release` (`EmergencyRelease`) |
| Raw register access | `g.read_register()` / `g.write_register()` | `g.readRegister()` / `g.writeRegister()` | `/dev_cmd` (opt-out, factory only) |
| Errors | raises `GripperError` | throws `GripperError` | service `success=false` + `message` |

Full method signatures, defaults, and the `GripperState` field lists:
[python/README.md](python/README.md#api-at-a-glance) ·
[cpp/README.md](cpp/README.md#public-api) ·
[ros2/README.md](ros2/README.md#ros2-services). A reference
implementation of the raw Modbus RTU framing (CRC16, timing, retries) if
you need to write a client in a fourth language:
[`cpp/src/modbus_rtu.cpp`](cpp/src/modbus_rtu.cpp).

## License

MIT — see [LICENSE](LICENSE).

---

*AIDIN Robotics — BLDC 모터 기반 그리퍼/액추에이터 솔루션*
