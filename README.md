# robot-arm
Programming the control of a stationary 6-axis robot arm


# Commands to run the application:
streamlit run app.py
python -m uvicorn backend.app.server:app --reload --port 8000

curl http://127.0.0.1:8000/arm