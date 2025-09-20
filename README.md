# Robot Arm Control — How to Run

This package contains a prebuilt Docker image and a docker-compose.yml file so you can run the app locally with no setup.

Files provided are:
robot-arm-image.zip → zipped Docker image
docker-compose.yml → defines backend + frontend services


# Steps to run
Unzip the image
unzip robot-arm-image.zip
→ produces robot-arm-image.tar

Load the image into Docker
docker load -i robot-arm-image.tar

Verify:
docker images
You should see robot-arm latest.

Start the application
docker compose up -d
This launches:
Backend (FastAPI) → http://localhost:8000
Frontend (Streamlit) → http://localhost:8501

Open the UI
Visit http://localhost:8501
Move sliders to set joint angles
Click Send Command to Robot → backend responds with JSON + trajectory plot

To Stop the application:
docker compose down

✅ Quick check
Test backend directly:
curl http://localhost:8000/arm

# Summary
The **frontend** is a Streamlit web app that lets you control the 6-DOF robot arm using sliders for each joint. When you adjust the sliders and click **Send Command to Robot**, it sends the joint angles to the backend, gets a trajectory back, and plots the positions, velocities, and accelerations in real time.

Currently, there is no support for 3D Vizualization. 

Currently, the app only shows 2D plots (joint angles, velocities, accelerations). If I had more time, I would add 3D visualization so the robot’s motion can be seen in space.
To do this, I would use a URDF model of the robot and visualizing it in RViz (ROS tool). The Streamlit sliders or trajectory generator would publish joint states, and RViz would animate the robot in real time.