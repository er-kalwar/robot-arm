import time
import streamlit as st
from dataclasses import dataclass

st.set_page_config(page_title="Robot Arm Control", layout="centered")
st.title("Robot Arm Control Interface")

JOINTS = ["Joint 1", "Joint 2", "Joint 3", "Joint 4", "Joint 5", "Joint 6"]
HOME_POSE = [0, -90, 90, 0, 90, 0]
LIMITS = {joint: (-180, 180) for joint in JOINTS}
ZERO_POSE = [0, 0, 0, 0, 0, 0]


