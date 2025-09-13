from dataclasses import dataclass
from enum import Enum
from typing import List, Optional
from ruckig import InputParameter, OutputParameter, Ruckig, Result, ControlInterface, Synchronization

@dataclass
class JointSample:
    position: List[float]
    velocity: List[float] 
    acceleration: List[float]
    done: bool

class TargetState(Enum):
    SAME = 0
    CHANGED = 1
    STOP = 2 

class JointInterpolator:
    def __init__(self, step_size: float, dof: int, max_acceleration: float, max_velocity: float, max_jerk: float):
        self.step_size = step_size
        self.dof = dof

        self.input_param = InputParameter(self.dof)
        self.output_param = OutputParameter(self.dof)

        self.ruckig = Ruckig(self.dof, self.step_size)

        self.max_acceleration = [max_acceleration] * dof
        self.max_velocity = [max_velocity] * dof
        self.max_jerk = [max_jerk] * dof
        

        self.is_trajectory_active = False
        self.target_state = TargetState.STOP 

        # Current state
        self.current_position = [0.0] * dof
        self.current_velocity = [0.0] * dof
        self.current_acceleration = [0.0] * dof


    ## Helper methods
    def __apply_limits(self):
        self.input_param.max_acceleration = self.max_acceleration
        self.input_param.max_velocity = self.max_velocity
        self.input_param.max_jerk = self.max_jerk

    def is_finished(self) -> bool:
        return not self.is_trajectory_active and self.target_state == TargetState.STOP

    def assert_length(self, lst: List[float], name: str):
        if len(lst) != self.dof:
            raise ValueError(f"{name} length {len(lst)} does not match DOF {self.dof}")
        
    ## Public methods
    def set_target_configuration(self, target_position: List[float], current_position: Optional[List[float]] = None):
        self.assert_length(target_position, "target_position")
        if current_position is not None:
            self.assert_length(current_position, "current_position")

        ip = self.input_param
        ip.control_interface = ControlInterface.POSITION
        ip.synchronization = Synchronization.Time

        ip.current_position = current_position or self.current_position
        ip.current_velocity = self.current_velocity
        ip.current_acceleration = self.current_acceleration

        ip.target_position = target_position
        ip.target_velocity = [0.0] * self.dof
        ip.target_acceleration = [0.0] * self.dof

        self.__apply_limits()
        self.is_trajectory_active = True
        self.target_state = TargetState.SAME

    def change_target_configuration(self, new_target_position: List[float]):
        self.assert_length(new_target_position, "new_target_position")
        if not self.is_trajectory_active:
            raise RuntimeError("No active trajectory to change target")
            return

          # Retarget from current dynamic state
        ip = self.input_param
        ip.control_interface = ControlInterface.POSITION
        ip.synchronization = Synchronization.Time

        ip.current_position = self.current_position
        ip.current_velocity = self.current_velocity
        ip.current_acceleration = self.current_acceleration

        ip.target_position = new_target_position
        ip.target_velocity = [0.0] * self.dof
        ip.target_acceleration = [0.0] * self.dof

        self.__apply_limits()
        self.is_trajectory_active = True
        self.target_state = TargetState.CHANGED

    def stop_trajectory(self):
        if not self.is_trajectory_active:
            return

        ip = self.input_param
        ip.control_interface = ControlInterface.POSITION
        ip.synchronization = Synchronization.Time

        ip.current_position = self.current_position
        ip.current_velocity = self.current_velocity
        ip.current_acceleration = self.current_acceleration

        ip.target_velocity = [0.0] * self.dof # Stop in place

        self.__apply_limits()
        self.is_trajectory_active = True
        self.target_state = TargetState.STOP

    def get_joint_commands(self) -> JointSample:
        "Advance the trajectory by one step and return the new joint commands"

        if not self.is_trajectory_active:
            return JointSample(
                position=self.current_position.copy(),
                velocity=self.current_velocity.copy(),
                acceleration=self.current_acceleration.copy(),
                done=True
            )
        
        result = self.ruckig.update(self.input_param, self.output_param)

        if result == Result.Error:
            self.is_trajectory_active = False
            return JointSample(position=self.current_position.copy(),
                velocity=self.current_velocity.copy(),
                acceleration=self.current_acceleration.copy(),
                done=True
            )
        
        # Update internal state
        self.current_position = list(self.output_param.new_position)
        self.current_velocity = list(self.output_param.new_velocity)
        self.current_acceleration = list(self.output_param.new_acceleration)

        done = result == Result.Finished
        if done:
            self.is_trajectory_active = False
        else:
            self.output_param.pass_to_input(self.input_param)
            
        return JointSample(
            position=self.current_position.copy(),
            velocity=self.current_velocity.copy(),
            acceleration=self.current_acceleration.copy(),
            done=False
        )