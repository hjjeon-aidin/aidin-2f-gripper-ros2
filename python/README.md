# AIDIN Gripper — Python SDK

Pure-Python SDK for the AIDIN BLDC gripper (DH-Robotics Modbus RTU). Runs
on Ubuntu and Windows with **one `pip install` step**. API surface is
deliberately kept close to the [C++ SDK](../cpp/) so the two are easy to
switch between.

```python
from aidin_gripper import Gripper

with Gripper() as g:
    g.connect("/dev/ttyUSB0")                      # Windows: "COM3"
    g.activate()
    g.home()
    g.move_to(255, speed=200, force=128, blocking=True)   # close
    g.move_to(0,   speed=200, force=128, blocking=True)   # open
    print(g.read_state())
```

## Requirements

| | Minimum |
|---|---|
| Python | 3.8+ |
| pymodbus | 3.0+ |
| pyserial | 3.5+ |
| Hardware | USB ↔ RS485 adapter (FTDI / CH340 / CP210x) |

Default link: **115200 baud, 8N1, slave ID 1**.

## Install

### Ubuntu / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .          # from the python/ directory
```

If you can't access `/dev/ttyUSB0`:
```bash
sudo usermod -a -G dialout $USER     # then log out / log back in
```

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

USB-RS485 adapters need their vendor driver (FTDI / CH340 / CP210x).

### Just want the dependencies?

```bash
pip install "pymodbus>=3.0,<4.0" pyserial
```

## Run the examples

| File | Demonstrates |
|---|---|
| `examples/01_activate_and_home.py` | Minimal startup sequence: activate + home |
| `examples/02_open_and_close.py` | One close + one open move (assumes already activated/homed) |
| `examples/03_open_close_loop.py` | Repeated open/close cycles with blocking moves and SIGINT (CTRL+C) handling |
| `examples/04_get_status.py` | Read status once, or `--watch` to poll @ 100 ms and print on change |
| `examples/05_fault_and_emergency_release.py` | Inspect `fault`/`latched_fault`, call `emergency_release()`, recover with `activate()` |
| `examples/06_full_quickstart_demo.py` | End-to-end: connect → activate → home → close → open → status |

```bash
cd examples
python 01_activate_and_home.py           /dev/ttyUSB0
python 02_open_and_close.py              /dev/ttyUSB0
python 03_open_close_loop.py             /dev/ttyUSB0 5
python 04_get_status.py                  /dev/ttyUSB0 --watch
python 05_fault_and_emergency_release.py /dev/ttyUSB0 open
python 06_full_quickstart_demo.py        /dev/ttyUSB0
```

Windows: pass `COM3` (or your actual port) instead.

## API at a glance

| Method | Purpose |
|---|---|
| `connect(port, baudrate=115200, parity='N', slave_id=1)` | Open serial link |
| `disconnect()`                                            | Close link |
| `activate(timeout_s=3.0)`                                 | rACT=1, wait for ACTIVE |
| `deactivate()`                                            | rACT=0 |
| `home(timeout_s=15.0)`                                    | Rising-edge homing, wait for gHOM=1 |
| `move_to(position, speed=128, force=128, blocking=False, timeout_s=5.0)` | Position 0=open … 255=close |
| `emergency_release(close_direction=False)`                | Latched release |
| `read_state() -> GripperState`                            | Full status snapshot |
| `is_at_target()` / `has_fault()`                          | Convenience predicates |
| `read_register(pdu_addr)` / `write_register(pdu_addr, value)` | Raw Modbus access |

`Gripper` is a context manager — `with Gripper() as g:` auto-closes the port.

All failures raise `aidin_gripper.GripperError` (a `RuntimeError` subclass).

## `GripperState` dataclass

```python
@dataclass
class GripperState:
    activated:     bool
    homed:         bool
    go_to_active:  bool
    stage:         GripperStage   # RESET / ACTIVATING / ACTIVE
    object_state:  ObjectState    # MOVING / OPEN_CONTACT / CLOSED_CONTACT / AT_TARGET
    fault:         int            # 0 = OK
    position_echo: int            # gPR
    position:      int            # gPO (0..255)
    current:       int            # gCU (0..255)
    speed:         int            # gSP (0..255)
    voltage:       float          # V
    latched_fault: int            # gFLTO
```

## C++ vs Python API mapping

| C++                             | Python                          |
|---------------------------------|---------------------------------|
| `g.connect("/dev/ttyUSB0")`     | `g.connect("/dev/ttyUSB0")`     |
| `g.activate()`                  | `g.activate()`                  |
| `g.home()`                      | `g.home()`                      |
| `g.moveTo(255, 200, 128, true)` | `g.move_to(255, 200, 128, blocking=True)` |
| `g.readState()`                 | `g.read_state()`                |
| `g.isAtTarget()`                | `g.is_at_target()`              |
| `aidin::reg::ACTION`            | `aidin_gripper.registers.ACTION` |
| `try { ... } catch (GripperError& e)` | `try: ... except GripperError as e:` |

The same register map, same default arguments, same blocking semantics.

## Register map

See [`aidin_gripper/registers.py`](aidin_gripper/registers.py). Mirrors the
firmware-side definitions in `aidin_modbus.h`. Full protocol details:
[`../cpp/MANUAL.md`](../cpp/MANUAL.md).

## Troubleshooting

| Symptom | Likely cause |
|---|---|
| `Cannot open serial port '/dev/ttyUSB0'`         | Wrong port or adapter not connected |
| `Cannot open serial port` (Linux, Permission)    | User not in `dialout` group |
| `read_holding_registers failed: ... timeout`     | Wrong baud / parity / slave ID; or RS485 A↔B swapped |
| `activate timeout`                               | Power supply low, or latched fault — read `state.latched_fault` |
| Gripper ignores `move_to` after one move         | `rATR` still latched after `emergency_release` — call `activate()` again |

## License

MIT. `pymodbus` is BSD-3-Clause.
