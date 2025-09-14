# Robot Arm Control Frontend
# --- ensure repository root is importable ---
from pathlib import Path
import sys
REPO_ROOT = Path(__file__).resolve().parents[1]  # /Users/expertty_/exspace/robot-arm
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
# -------------------------------------------

import time
import streamlit as st
from dataclasses import dataclass
import requests
from backend.app.joint_interpolator import JointInterpolator, Result
from visualization import plot_trajectory

st.set_page_config(page_title="Robot Arm Control", layout="centered")
st.title("Robot Arm Control Interface")

# Configuration
JOINTS = ["Joint 1", "Joint 2", "Joint 3", "Joint 4", "Joint 5", "Joint 6"]
HOME_POSE = [0, -90, 90, 0, 90, 0]
LIMITS = {joint: (-180, 180) for joint in JOINTS}
ZERO_POSE = [0, 0, 0, 0, 0, 0]

# Backend server URL
st.sidebar.header("Backend Server")
default_url = "http://127.0.0.1:8000"
backend_url = st.sidebar.text_input("Backend URL", value=default_url)
st.sidebar.caption("Endpoints: \n - GET /arm \n - POST /set_joints")

def assert_pose_in_limits(pose):
    for j, v in zip(JOINTS, pose):
        jmin, jmax = LIMITS[j]
        if not (jmin <= v <= jmax):
            raise ValueError(f"{j}={v} out of limits [{jmin}, {jmax}]")

def ensure_state():
    if "pose_deg" not in st.session_state:
        st.session_state.pose_deg = HOME_POSE.copy()
    for j,v in zip(JOINTS, st.session_state.pose_deg):
        st.session_state.setdefault(f"slider_{j}", int(v))

def set_pose_on_ui(pose_deg: list[float]) -> None:
    st.session_state.pose_deg = pose_deg.copy()
    for j, v in zip(JOINTS, pose_deg):
        st.session_state[f"slider_{j}"] = int(v)

def get_current_robot_pose_from_backend(base_url: str) -> list[float] | None:
    try:
        r = requests.get(f"{base_url}/arm", timeout=3.0)
        r.raise_for_status()
        joints = r.json().get("joints", [])
        return [float(j["angle_deg"]) for j in joints] if joints else None
    except requests.RequestException:
        return None

if "current_pose_deg" not in st.session_state:
    # Try to bootstrap from backend; if unavailable, fall back to HOME
    live = get_current_robot_pose_from_backend(backend_url)
    st.session_state.current_pose_deg = live if live else HOME_POSE.copy()
    # Optionally sync sliders to the real robot on first load:
    set_pose_on_ui(st.session_state.current_pose_deg)


def build_cmd():
    cmd = {
        "type": "set_joints",
        "units": "deg",
        "values": st.session_state.pose_deg,
        "timestamp": int(time.time())
    }
    return cmd

def post_command(url:str, cmd:dict, timeout:float=3.0) -> tuple[bool, dict]:
    """Send command to backend server and return (ok, response_json)."""
    try:
        response = requests.post(f"{url}/set_joints", json=cmd, timeout=timeout)
        response.raise_for_status()
        if response.ok:
            return True, response.json()
        else:
            return False, {"error": f"Status code {response.status_code}"}
    except requests.RequestException as e:
        return False, {"error": str(e)}


assert_pose_in_limits(HOME_POSE)
ensure_state()

c1, c2 = st.columns(2)
with c1:
    if st.button("Go to Home Pose"):
        st.session_state.pose_deg = HOME_POSE.copy()
        for j,v in zip(JOINTS, st.session_state.pose_deg):
            st.session_state[f"slider_{j}"] = v

with c2:
    if st.button("Go to Zero Pose"):
        st.session_state.pose_deg = ZERO_POSE.copy()
        for j,v in zip(JOINTS, st.session_state.pose_deg):
            st.session_state[f"slider_{j}"] = v

st.divider()

st.subheader("Set Joint Angles")
columns = st.columns(3)

for i, joint in enumerate(JOINTS):
    with columns[i % 3]:
        st.slider(
            label = joint,
            min_value= LIMITS[joint][0],
            max_value= LIMITS[joint][1],
            step=1,
            key = f"slider_{joint}",
        )

# Update pose from sliders
st.session_state.pose_deg = [st.session_state[f"slider_{j}"] for j in JOINTS]

cmd = build_cmd()
st.subheader("Generated JSON Command")
st.json(cmd, expanded=False)


# Send command to backend
send_col, refresh_col = st.columns(2)

with send_col:
    if st.button("Send Command to Robot", use_container_width=True):
        assert_pose_in_limits(st.session_state.pose_deg)
        # Target Sliders
        target_pos_deg = st.session_state.pose_deg.copy()
        print(f"Target position on slider is: {target_pos_deg}")

        # Current position
        current_pos_deg = st.session_state.get("current_pose_deg", HOME_POSE).copy()
        print(f"Current position in state is: {current_pos_deg}")
        ok, payload = post_command(backend_url, cmd)
        if ok:
            st.success("Command sent successfully!")
            st.json(payload, expanded=False)


            ji = JointInterpolator(step_size=0.01, dof=6,
                                   max_acceleration=50,
                                   max_velocity=10,
                                   max_jerk=500.0) # Units: deg, deg/s, deg/s^2, deg/s^3)
            traj = ji.run_interpolation(target_pos_deg, current_pos_deg=current_pos_deg)
            plot_trajectory(traj, step_size=ji.step_size, dof=ji.dof, save_path="traj.png")
            st.session_state.current_pose_deg = target_pos_deg.copy()
            
        else:
            st.error(f"Failed to send command - {payload.get('error', 'Unknown error')} ")

with refresh_col:
    if st.button("Refresh Current State (GET /arm)", use_container_width=True):
        try:
            response = requests.get(f"{backend_url}/arm", timeout=3.0)
            response.raise_for_status()
            if response.ok:
                arm_state = response.json()
                st.success("Fetched current arm state successfully!")
                st.json(arm_state, expanded=False)
                # st.session_state.pose_deg = [joint["angle_deg"] for joint in arm_state.get("joints", [])]
                # for j,v in zip(JOINTS, st.session_state.pose_deg):
                #     st.session_state[f"slider_{j}"] = int(v)
            else:
                st.error(f"Failed to fetch state - Status code {response.status_code}")
        except requests.RequestException as e:
            st.error(f"Failed to fetch state - {str(e)}")
    