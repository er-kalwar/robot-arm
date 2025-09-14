# Robot Arm Control Frontend
# --- ensure repository root is importable ---
from pathlib import Path
import sys
REPO_ROOT = Path(__file__).resolve().parents[1]  # /Users/expertty_/exspace/robot-arm
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
# -------------------------------------------

import time
from typing import List, Tuple, Dict, Optional
import requests
import streamlit as st

from backend.app.joint_interpolator import JointInterpolator
from visualization import plot_trajectory

# --- Page setup ---
st.set_page_config(page_title="Robot Arm Control", layout="centered")
st.title("Robot Arm Control Interface")

# --- Configuration ---
JOINTS: List[str] = ["Joint 1", "Joint 2", "Joint 3", "Joint 4", "Joint 5", "Joint 6"]
HOME_POSE: List[float] = [0, -90, 90, 0, 90, 0]
ZERO_POSE: List[float] = [0, 0, 0, 0, 0, 0]
LIMITS: Dict[str, Tuple[float, float]] = {j: (-180, 180) for j in JOINTS}

# --- Sidebar / Backend URL ---
st.sidebar.header("Backend Server")
default_url = "http://127.0.0.1:8000"
backend_url = st.sidebar.text_input("Backend URL", value=default_url)
st.sidebar.caption("Endpoints:\n- GET /arm\n- POST /set_joints")

def assert_pose_in_limits(pose: List[float]) -> None:
    for j, v in zip(JOINTS, pose):
        jmin, jmax = LIMITS[j]
        if not (jmin <= v <= jmax):
            raise ValueError(f"{j}={v} out of limits [{jmin}, {jmax}]")

def ensure_state() -> None:
    """Initialize session state once."""
    if "pose_deg" not in st.session_state:
        st.session_state.pose_deg = HOME_POSE.copy()
    if "current_pose_deg" not in st.session_state:
        # Try to bootstrap from backend; if unavailable, fall back to HOME
        live = get_current_robot_pose_from_backend(backend_url)
        st.session_state.current_pose_deg = live if live else HOME_POSE.copy()
        set_pose_on_ui(st.session_state.current_pose_deg)

    for j, v in zip(JOINTS, st.session_state.pose_deg):
        st.session_state.setdefault(f"slider_{j}", int(v))

def set_pose_on_ui(pose_deg: List[float]) -> None:
    """Push a pose into sliders and session pose."""
    st.session_state.pose_deg = pose_deg.copy()
    for j, v in zip(JOINTS, pose_deg):
        st.session_state[f"slider_{j}"] = int(v)

def get_current_robot_pose_from_backend(base_url: str) -> Optional[List[float]]:
    try:
        r = requests.get(f"{base_url}/arm", timeout=3.0)
        r.raise_for_status()
        joints = r.json().get("joints", [])
        return [float(j["angle_deg"]) for j in joints] if joints else None
    except requests.RequestException:
        return None

def build_cmd() -> Dict:
    return {
        "type": "set_joints",
        "units": "deg",
        "values": st.session_state.pose_deg,
        "timestamp": int(time.time()),
    }

def post_command(url: str, cmd: Dict, timeout: float = 3.0) -> Tuple[bool, Dict]:
    """Send command to backend server and return (ok, response_json)."""
    try:
        response = requests.post(f"{url}/set_joints", json=cmd, timeout=timeout)
        response.raise_for_status()
        return True, response.json()
    except requests.RequestException as e:
        return False, {"error": str(e)}

def sidebar_backend_status() -> None:
    live = get_current_robot_pose_from_backend(backend_url)
    if live is None:
        st.sidebar.error("Backend: unreachable")
    else:
        st.sidebar.success("Backend: OK")

def main() -> None:
    # --- Init ---
    ensure_state()
    sidebar_backend_status()

    # --- Pose shortcuts ---
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Home Pose"):
            set_pose_on_ui(HOME_POSE)
    with c2:
        if st.button("Zero Pose"):
            set_pose_on_ui(ZERO_POSE)
    with c3:
        preset = st.selectbox("Presets", ["—", "Home", "Zero"], index=0)
        if preset == "Home":
            set_pose_on_ui(HOME_POSE)
        elif preset == "Zero":
            set_pose_on_ui(ZERO_POSE)

    st.divider()

    # --- Sliders ---
    st.subheader("Set Joint Angles")
    columns = st.columns(3)
    for i, joint in enumerate(JOINTS):
        with columns[i % 3]:
            st.slider(
                label=joint,
                min_value=LIMITS[joint][0],
                max_value=LIMITS[joint][1],
                step=1,
                key=f"slider_{joint}",
            )

    # Update pose from sliders
    st.session_state.pose_deg = [st.session_state[f"slider_{j}"] for j in JOINTS]

    # --- Command preview ---
    cmd = build_cmd()
    st.subheader("Generated JSON Command")
    st.json(cmd, expanded=False)

    # --- Actions ---
    send_col, refresh_col = st.columns(2)

    with send_col:
        if st.button("Send Command to Robot", use_container_width=True):
            try:
                assert_pose_in_limits(st.session_state.pose_deg)

                target_pos_deg = st.session_state.pose_deg.copy()
                current_pos_deg = st.session_state.get("current_pose_deg", HOME_POSE).copy()

                ok, payload = post_command(backend_url, cmd)
                if ok:
                    st.success("Command sent successfully!")
                    st.json(payload, expanded=False)

                    # Trajectory (local visualization only)
                    try:
                        ji = JointInterpolator(
                            step_size=0.01, dof=6,
                            max_acceleration=50,  # deg/s^2
                            max_velocity=10,      # deg/s
                            max_jerk=500.0,       # deg/s^3
                        )
                        traj = ji.run_interpolation(target_pos_deg, current_pos_deg=current_pos_deg)

                        # plot_trajectory should return a figure; fall back to image if it saves instead
                        fig = plot_trajectory(traj, step_size=ji.step_size, dof=ji.dof,save_path="traj.png")
                        if fig is not None:
                            st.plotly_chart(fig, use_container_width=True)
                        st.session_state.current_pose_deg = target_pos_deg.copy()
                    except Exception as e:
                        st.warning(f"Interpolation/plot failed: {e}")

                else:
                    st.error(f"Failed to send command — {payload.get('error', 'Unknown error')}")
            except Exception as e:
                st.error(str(e))

    with refresh_col:
        if st.button("Refresh Current State (GET /arm)", use_container_width=True):
            live = get_current_robot_pose_from_backend(backend_url)
            if live is None:
                st.error("Failed to fetch state (backend unreachable)")
            else:
                st.success("Fetched current arm state successfully!")
                # Sync sliders + state to live pose
                set_pose_on_ui(live)
                st.session_state.current_pose_deg = live.copy()
                st.json({"joints_deg": live}, expanded=False)

if __name__ == "__main__":
    main()