import time
import streamlit as st

st.set_page_config(page_title="6DOF — Zero/Home + Sliders", layout="centered")

JOINTS = ["J1", "J2", "J3", "J4", "J5", "J6"]
LIMITS_DEG = {j: (-180, 180) for j in JOINTS}
ZERO_POSE = [0] * 6
HOME_POSE = [0, -90, 90, 0, 90, 0]  # <- change to your real home

# --- Initialize state & widget keys BEFORE creating sliders -------------------
def ensure_state():
    if "pose_deg" not in st.session_state:
        st.session_state.pose_deg = ZERO_POSE.copy()
    # Make sure slider keys exist with initial values
    for j, v in zip(JOINTS, st.session_state.pose_deg):
        st.session_state.setdefault(f"angle_{j}", int(v))

ensure_state()

st.title("🦾 6DOF — Zero, Home & Sliders")

# Buttons: update widget keys, then rerun so sliders render with new values
c1, c2 = st.columns(2)
with c1:
    if st.button("Set ZERO pose", use_container_width=True):
        for j, v in zip(JOINTS, ZERO_POSE):
            st.session_state[f"angle_{j}"] = v
        st.session_state.pose_deg = ZERO_POSE.copy()
        st.rerun()
with c2:
    if st.button("Set HOME pose", use_container_width=True):
        for j, v in zip(JOINTS, HOME_POSE):
            st.session_state[f"angle_{j}"] = v
        st.session_state.pose_deg = HOME_POSE.copy()
        st.rerun()

st.divider()

# Sliders (use only keys; no 'value' argument)
st.subheader("Adjust Joints (deg)")
cols = st.columns(3)
for i, j in enumerate(JOINTS):
    with cols[i % 3]:
        st.slider(
            j,
            min_value=LIMITS_DEG[j][0],
            max_value=LIMITS_DEG[j][1],
            key=f"angle_{j}",
            step=1,
        )

# Read slider values and store as current pose (safe: doesn't touch widget keys)
pose = [int(st.session_state[f"angle_{j}"]) for j in JOINTS]
if pose != st.session_state.pose_deg:
    st.session_state.pose_deg = pose

# Readout
st.subheader("Current Pose (deg)")
mcols = st.columns(len(JOINTS))
for i, (j, v) in enumerate(zip(JOINTS, st.session_state.pose_deg)):
    with mcols[i]:
        st.metric(j, f"{v}°")

# Command you can send to your backend
cmd = {
    "type": "set_joints",
    "units": "deg",
    "values": st.session_state.pose_deg,
    "sent_at": int(time.time()),
}
st.subheader("Command JSON")
st.json(cmd)

if st.button("🚀 Send pose (stub)"):
    st.success("Pose sent (stub). Replace with your backend call.")
