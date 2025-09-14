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
