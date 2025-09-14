import time
import streamlit as st
from dataclasses import dataclass
import requests

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
#st.write("Current Pose (degrees):", st.session_state.pose_deg)

cmd = build_cmd()
st.subheader("Generated JSON Command")
st.json(cmd, expanded=False)


# Send command to backend
send_col, refresh_col = st.columns(2)

with send_col:
    if st.button("Send Command to Robot", use_container_width=True):
        assert_pose_in_limits(st.session_state.pose_deg)
        ok, payload = post_command(backend_url, cmd)
        if ok:
            st.success("Command sent successfully!")
            st.json(payload, expanded=False)
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







# # Robot Visualization Placeholder
# # --- 3D Visualization (Plotly) -----------------------------------------------
# import numpy as np
# import plotly.graph_objects as go

# # Link lengths in meters (tweak as you like)
# LINKS = [0.30, 0.30, 0.30, 0.30, 0.30, 0.30]

# # Homogeneous transform helpers
# def Rx(a):
#     c, s = np.cos(a), np.sin(a)
#     return np.array([[1,0,0,0],[0,c,-s,0],[0,s,c,0],[0,0,0,1]], dtype=float)

# def Ry(a):
#     c, s = np.cos(a), np.sin(a)
#     return np.array([[c,0,s,0],[0,1,0,0],[-s,0,c,0],[0,0,0,1]], dtype=float)

# def Rz(a):
#     c, s = np.cos(a), np.sin(a)
#     return np.array([[c,-s,0,0],[s,c,0,0],[0,0,1,0],[0,0,0,1]], dtype=float)

# def Tx(d): return np.array([[1,0,0,d],[0,1,0,0],[0,0,1,0],[0,0,0,1]], dtype=float)
# def Tz(d): return np.array([[1,0,0,0],[0,1,0,0],[0,0,1,d],[0,0,0,1]], dtype=float)

# def fk_points_deg(q_deg, L):
#     """Very simple 6R kinematic chain for visualization (not tied to any real robot).
#        Frame sequence (base at origin):
#        1) Rz(q1), Tz(L1)
#        2) Ry(q2), Tx(L2)
#        3) Ry(q3), Tx(L3)
#        4) Rz(q4), Tx(L4)
#        5) Ry(q5), Tx(L5)
#        6) Rz(q6), Tx(L6)
#        Returns 7 points: base + 6 joints/tool.
#     """
#     q = np.radians(q_deg)
#     T = np.eye(4)
#     pts = [T[:3, 3].copy()]  # base

#     T = T @ Rz(q[0]) @ Tz(L[0]);  pts.append(T[:3,3].copy())
#     T = T @ Ry(q[1]) @ Tx(L[1]);  pts.append(T[:3,3].copy())
#     T = T @ Ry(q[2]) @ Tx(L[2]);  pts.append(T[:3,3].copy())
#     T = T @ Rz(q[3]) @ Tx(L[3]);  pts.append(T[:3,3].copy())
#     T = T @ Ry(q[4]) @ Tx(L[4]);  pts.append(T[:3,3].copy())
#     T = T @ Rz(q[5]) @ Tx(L[5]);  pts.append(T[:3,3].copy())

#     return np.vstack(pts)  # shape (7, 3)

# def plot_arm(points, reach):
#     x, y, z = points[:,0], points[:,1], points[:,2]
#     fig = go.Figure()

#     # stick + joints
#     fig.add_trace(go.Scatter3d(
#         x=x, y=y, z=z, mode="lines+markers",
#         line=dict(width=6), marker=dict(size=4)
#     ))

#     # base frame axes (for orientation)
#     ax_len = min(0.15, reach*0.25)
#     fig.add_trace(go.Scatter3d(x=[0, ax_len], y=[0,0], z=[0,0], mode="lines", name="X"))
#     fig.add_trace(go.Scatter3d(x=[0,0], y=[0, ax_len], z=[0,0], mode="lines", name="Y"))
#     fig.add_trace(go.Scatter3d(x=[0,0], y=[0,0], z=[0, ax_len], mode="lines", name="Z"))

#     fig.update_layout(
#         margin=dict(l=0, r=0, t=30, b=0),
#         scene=dict(
#             xaxis=dict(range=[-reach, reach], zeroline=False, showgrid=True),
#             yaxis=dict(range=[-reach, reach], zeroline=False, showgrid=True),
#             zaxis=dict(range=[-reach, reach], zeroline=False, showgrid=True),
#             aspectmode="cube",
#             camera=dict(eye=dict(x=1.6, y=1.6, z=1.0))
#         ),
#         showlegend=False,
#         title="3D Robot Arm (stick model)"
#     )
#     st.plotly_chart(fig, use_container_width=True, key="arm_plot")

# # Compute and draw
# reach = sum(LINKS) + 0.05
# pts = fk_points_deg(st.session_state.pose_deg, LINKS)
# plot_arm(pts, reach)
