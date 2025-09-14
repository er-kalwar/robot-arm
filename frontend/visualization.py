import os
import numpy as np
import matplotlib.pyplot as plt

def plot_trajectory(traj, step_size: float, dof: int, save_path: str | None = None):
    if not traj:
        print("Trajectory is empty — nothing to plot.")
        return

    # normalize to arrays
    def arr(field):
        if hasattr(traj[0], field):
            return np.array([getattr(s, field) for s in traj], dtype=float)
        return np.array([s[field] for s in traj], dtype=float)

    pos, vel, acc = arr("position"), arr("velocity"), arr("acceleration")
    t = np.arange(len(traj)) * step_size

    fig, axes = plt.subplots(3, 1, figsize=(10, 8), sharex=True)

    for j in range(dof):
        axes[0].plot(t, pos[:, j], label=f"J{j+1}")
    axes[0].set_ylabel("Angle [deg]")
    axes[0].set_title("Joint Positions")
    axes[0].grid(True); axes[0].legend(ncol=min(6, dof), fontsize=8)

    for j in range(dof):
        axes[1].plot(t, vel[:, j])
    axes[1].set_ylabel("Velocity [deg/s]")
    axes[1].set_title("Joint Velocities")
    axes[1].grid(True)

    for j in range(dof):
        axes[2].plot(t, acc[:, j])
    axes[2].set_ylabel("Acceleration [deg/s²]")
    axes[2].set_title("Joint Accelerations")
    axes[2].set_xlabel("Time [s]")
    axes[2].grid(True)

    fig.tight_layout()

    # Prefer Streamlit if available, else save/show
    if "STREAMLIT_SERVER_RUNNING" in os.environ:
        import streamlit as st
        st.pyplot(fig)
        plt.close(fig)
    elif save_path:
        fig.savefig(save_path, dpi=150)
        print(f"Saved plot to: {save_path}")
        plt.close(fig)
    else:
        plt.show()
