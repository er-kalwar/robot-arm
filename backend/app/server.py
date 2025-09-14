from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Literal, Optional, Tuple
import math
from .arm import Joint, JointLimitError, RobotArm
import logging
from .joint_interpolator import JointInterpolator, Result

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Robotic Arm Control API", version="1.0.0")

arm = RobotArm(joints=[
    Joint(name="Joint 1", min_deg=-180, max_deg=180),
    Joint(name="Joint 2", min_deg=-180, max_deg=180),
    Joint(name="Joint 3", min_deg=-180, max_deg=180),
    Joint(name="Joint 4", min_deg=-180, max_deg=180),
    Joint(name="Joint 5", min_deg=-180, max_deg=180),
    Joint(name="Joint 6", min_deg=-180, max_deg=180),
])

class SetJointsRequest(BaseModel):
    type: Literal["set_joints"]
    units: Literal["deg", "rad"] = "deg"
    values: Tuple[float, float, float, float, float, float]
    timestamp: Optional[int] = None  # Unix timestamp in seconds

@app.get("/arm")
def get_arm():
    return arm.to_dict()

@app.post("/set_joints")
def set_joints(request: SetJointsRequest):
    try:
        vals_deg = request.values if request.units == "deg" else [math.degrees(v) for v in request.values]
        arm.set_angles_deg(vals_deg, mode="clamp")
        logging.info(f"Set joints to {vals_deg} degrees")
        return arm.to_dict()
    except JointLimitError as e:
        logging.error(f"Joint limit error: {e}")
        raise HTTPException(status_code=400, detail=str(e))