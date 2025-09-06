from dataclasses import dataclass, field 
from typing import  Any , Dict
import math


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
    


# Example test of Joint class
if __name__ == "__main__":
    j1 = Joint(name="joint_2", min_deg=-180, max_deg=180)
    j1.angle_deg = 90
    j1.set_angle_deg_safe(200, mode="clamp")
    print(j1.to_dict()) 