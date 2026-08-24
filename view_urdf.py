#!/usr/bin/env python
"""AIDIN gripper URDF viewer/animator (MuJoCo backend, no ROS required).

Loads a URDF, resolves package:// mesh URIs to local filesystem paths, and
opens an interactive 3D window. Any non-fixed joint found in the compiled
model is swept open <-> closed automatically so motion is visible without
extra input; joints declared via <mimic> in the URDF (which MuJoCo's URDF
importer does not enforce on its own) are driven in lock-step with their
master joint every frame.

Usage:
    py -m pip install mujoco
    py view_urdf.py urdf/urdf/aidin_2f_gripper.urdf
"""
import argparse
import math
import re
import sys
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path

import mujoco
import mujoco.viewer


def find_package_root(urdf_path: Path):
    """Walk up from the URDF file to the nearest package.xml and return
    (ros_package_name, package_root_dir), or (None, None) if none is found."""
    for d in [urdf_path.parent, *urdf_path.parent.parents]:
        pkg_xml = d / "package.xml"
        if pkg_xml.exists():
            m = re.search(r"<name>\s*([^<\s]+)\s*</name>", pkg_xml.read_text(encoding="utf-8"))
            if m:
                return m.group(1), d
    return None, None


def resolve_package_uris(urdf_path: Path) -> Path:
    """Write a temp copy of the URDF with package:// mesh URIs rewritten to
    absolute filesystem paths, so a plain XML/physics importer (no ROS, no
    $ROS_PACKAGE_PATH) can resolve every <mesh filename=...>."""
    text = urdf_path.read_text(encoding="utf-8")
    pkg_name, pkg_root = find_package_root(urdf_path)
    if pkg_name:
        local = pkg_root.resolve().as_posix()
        text = text.replace(f"package://{pkg_name}/", f"{local}/")

    remaining = re.findall(r'package://[^"\']+', text)
    if remaining:
        print(f"WARNING: unresolved package:// URI(s): {remaining}", file=sys.stderr)

    tmp_path = Path(tempfile.gettempdir()) / (urdf_path.stem + ".resolved.urdf")
    tmp_path.write_text(text, encoding="utf-8")
    return tmp_path


def parse_mimics(urdf_path: Path):
    """Read <mimic joint=".." multiplier=".." offset=".."/> tags directly —
    MuJoCo's URDF importer creates the mimicking joint as an independent DOF
    and silently drops this constraint."""
    root = ET.parse(urdf_path).getroot()
    mimics = {}
    for joint in root.findall("joint"):
        mimic = joint.find("mimic")
        if mimic is not None:
            mimics[joint.get("name")] = (
                mimic.get("joint"),
                float(mimic.get("multiplier", 1.0)),
                float(mimic.get("offset", 0.0)),
            )
    return mimics


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("urdf", type=Path, help="Path to a .urdf file")
    ap.add_argument("--period", type=float, default=3.0,
                     help="Seconds for one open<->close sweep (default: 3.0)")
    args = ap.parse_args()

    urdf_path = args.urdf.resolve()
    if not urdf_path.exists():
        sys.exit(f"URDF not found: {urdf_path}")

    resolved = resolve_package_uris(urdf_path)
    mimics = parse_mimics(urdf_path)

    try:
        model = mujoco.MjModel.from_xml_path(str(resolved))
    except ValueError as e:
        sys.exit(
            "MuJoCo가 이 URDF를 컴파일하지 못했습니다 — BASE_MASS, STROKE_HALF 같은 "
            "CAPS 플레이스홀더가 아직 실수값으로 채워지지 않았을 가능성이 높습니다.\n\n"
            f"원본 오류:\n{e}"
        )

    data = mujoco.MjData(model)
    model.opt.gravity[:] = 0  # shape/kinematics check, not a drop test

    joint_names = [mujoco.mj_id2name(model, mujoco.mjtObj.mjOBJ_JOINT, i)
                   for i in range(model.njnt)]
    print(f"robot: {urdf_path.stem}   bodies={model.nbody - 1}   joints={model.njnt}")
    for n in joint_names:
        tag = f"  [mimic -> {mimics[n][0]}]" if n in mimics else ""
        print(f"  joint: {n}{tag}")

    driven = [n for n in joint_names if n not in mimics]
    if not driven:
        print("움직이는 조인트가 없습니다 (전부 fixed) — 정지된 형상만 확인합니다.")

    with mujoco.viewer.launch_passive(model, data) as viewer:
        t0 = time.time()
        while viewer.is_running():
            t = time.time() - t0
            phase = 0.5 - 0.5 * math.cos(2 * math.pi * t / args.period)
            for n in driven:
                jid = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, n)
                lo, hi = model.jnt_range[jid]
                if lo == hi:
                    continue
                data.qpos[model.jnt_qposadr[jid]] = lo + phase * (hi - lo)
            for mimic_name, (master_name, mult, off) in mimics.items():
                mi = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, mimic_name)
                mj = mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_JOINT, master_name)
                data.qpos[model.jnt_qposadr[mi]] = mult * data.qpos[model.jnt_qposadr[mj]] + off
            mujoco.mj_forward(model, data)
            viewer.sync()
            time.sleep(1 / 60)


if __name__ == "__main__":
    main()
