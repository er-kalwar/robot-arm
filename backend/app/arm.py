from dataclasses import dataclass, field 
from typing import  Any , Dict , List, Optional, Tuple, Iterable
import math
import json

# -- Helper functions for arm kinematics --
def deg2rad(deg: float) -> float:
    return(deg*math.pi / 180.0)

def rad2deg(rad: float) ->float:
    return(rad*180 /math.pi)

class JointLimitError(ValueError):
    pass

# -- Individual core data types --
@dataclass
class Joint:
    """
    Represents a single joint in the robotic arm. 
    Angle can be set and retrieved in degrees.
    Feed angle in min and max degrees to enforce limits.
    """
    name: str
    min_deg: float
    max_deg: float
    _angle_rad: float = field(default=0.0, repr=True)

    def __post_init__(self):
        if self.min_deg > self.max_deg:
            raise ValueError(f"{self.name}: min_deg {self.min_deg} is greater than the max degree: {self.max_deg}")
        self.angle_deg = self.angle_deg   

    @property
    def angle_deg(self) -> float:       
        return rad2deg(self._angle_rad)
    
    @angle_deg.setter
    def angle_deg(self, value_deg: float):
        clamped = max(self.min_deg, min(self.max_deg, value_deg))
        self._angle_rad = deg2rad(clamped)

    def validate_angle(self, value_deg: float):
        """Raise if value is reached out of limits"""
        if not (self.min_deg <= value_deg <= self.max_deg):
            raise JointLimitError(
                f"{self.name}: {value_deg} is out of limits [{self.min_deg}, {self.max_deg}]"
            )
        
    def set_angle_deg_safe(self, value_deg: float, *, mode: str = "clamp"):
        """Set angle with different modes:
        - clamp: clamps the value to the nearest limit if out of bounds
        - raise: raises JointLimitError if out of bounds
        """
        if mode == "clamp":
            self.angle_deg = value_deg
        elif mode == "raise":
            self.validate_angle(value_deg)
            self.angle_deg = value_deg
        else:
            raise ValueError(f"Unknown mode: {mode}")
        
    def to_dict(self) -> Dict[str, Any]:
        return{
            "name": self.name ,
            "min_deg": self.min_deg,
            "max_deg": self.max_deg,
            "angle_deg": self.angle_deg
        }
    
# -- Robotic Arm -- 
@dataclass
class RobotArm:
    """Collection of joints representing a robotic arm.
    Provide safe bulk updates, serialization, and queries."""
    joints: List[Joint]

    # -- Queries --
    @property
    def names(self) -> List[str]:
        return [joint.name for joint in self.joints]

    @property
    def get_angles_deg(self) -> List[float]:
        return [joint.angle_deg for joint in self.joints]
    
    @property
    def get_limits_deg(self) -> List[Tuple[float, float]]:
        return [(joint.min_deg, joint.max_deg) for joint in self.joints]

    def describe(self) -> List[Dict[str, Any]]:
        return [joint.to_dict() for joint in self.joints]

    # -- Commands --
    def _index_of(self, name: str) -> int:
        for i, joint in enumerate(self.joints):
            if joint.name == name:
                return i
        raise KeyError(f"Joint with name {name} not found")

    def set_angle_deg(self, joint_name: str, value_deg: float, *, mode: str = "clamp"):
        idx = self._index_of(joint_name)
        self.joints[idx].set_angle_deg_safe(value_deg, mode=mode)

    def set_angles_deg(self, values_deg: Iterable[float], *, mode: str = "clamp"):
        values = list(values_deg)
        if len(values) != len(self.joints):
            raise ValueError(f"Expected {len(self.joints)} angles, got {len(values)}")
        for joint, value in zip(self.joints, values):
            joint.set_angle_deg_safe(value, mode=mode)

    def ensure_within_limits(self):
        for joint in self.joints:
            joint.validate_angle(joint.angle_deg)


    # -- Serialization --
    def to_dict(self) -> Dict[str, Any]:
        return {
            "joints": [joint.to_dict() for joint in self.joints]
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "RobotArm":
        joints = [Joint(**joint_data) for joint_data in data["joints"]]
        return cls(joints=joints)

    def to_json(self, *, indent: Optional[int] = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent)
    
    @classmethod
    def from_json(cls, json_str: str) -> "RobotArm":
        data = json.loads(json_str)
        return cls.from_dict(data)