import time
import streamlit as st
from dataclasses import dataclass

st.set_page_config(page_title="Robot Arm Control", layout="centered")
st.title("Robot Arm Control Interface")

JOINTS = ["Joint 1", "Joint 2", "Joint 3", "Joint 4", "Joint 5", "Joint 6"]
HOME_POSE = [0, -90, 90, 0, 90, 0]
LIMITS = {joint: (-180, 180) for joint in JOINTS}
ZERO_POSE = [0, 0, 0, 0, 0, 0]


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
st.write("Current Pose (degrees):", st.session_state.pose_deg)

# Prepare command to send to backend

def build_cmd():
    cmd = {
        "type": "set_joints",
        "units": "deg",
        "values": st.session_state.pose_deg,
        "timestamp": int(time.time())
    }
    return cmd


# Send command to backend
if st.button("Send Command to Robot"):
    # TODO: Implement actual sending logic (HTTP request)
    cmd = build_cmd()
    st.json(cmd)