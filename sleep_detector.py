import base64
import threading
import time
import webbrowser
import cv2
import winsound
import numpy as np
import os
import urllib.request
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

app = Flask(
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static',
)
CORS(app)

status = {
    "running": False,
    "eyes_closed": False,
    "alarm_triggered": False,
    "alarm_status": "Normal",
    "elapsed_time": 0.0,
    "message": "Ready to start detection.",
}

closed_start_time = None
alarm_active = False
eye_history = []
CLOSED_TIME_LIMIT = 2.0
CLOSED_EYES_THRESHOLD = 0.015

# Download model if not exists
model_path = "face_landmarker.task"
if not os.path.exists(model_path):
    print("Downloading FaceLandmarker model...")
    url = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    urllib.request.urlretrieve(url, model_path)
    print("Download complete.")

base_options = python.BaseOptions(model_asset_path=model_path)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    output_face_blendshapes=True,
    output_facial_transformation_matrixes=False,
    num_faces=1
)
detector = vision.FaceLandmarker.create_from_options(options)

def decode_image(image_data):
    if image_data.startswith('data:'):
        image_data = image_data.split(',', 1)[1]
    image_bytes = base64.b64decode(image_data)
    np_arr = np.frombuffer(image_bytes, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
    return frame

def analyze_frame(frame):
    global status, closed_start_time, alarm_active, eye_history

    frame = cv2.flip(frame, 1)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
    
    detection_result = detector.detect(mp_image)
    
    eyes_closed = False
    
    if detection_result.face_landmarks:
        face_landmarks = detection_result.face_landmarks[0]
        # Top and bottom landmarks for eyes
        left_top = face_landmarks[159]
        left_bottom = face_landmarks[145]
        right_top = face_landmarks[386]
        right_bottom = face_landmarks[374]
        
        left_eye_dist = abs(left_top.y - left_bottom.y)
        right_eye_dist = abs(right_top.y - right_bottom.y)
        
        if left_eye_dist < CLOSED_EYES_THRESHOLD and right_eye_dist < CLOSED_EYES_THRESHOLD:
            eyes_closed = True
    else:
        # If no face is detected, treat as eyes not closed to avoid false alarms when looking away slightly
        pass

    # Smooth the detection using a history of the last 7 frames
    eye_history.append(eyes_closed)
    if len(eye_history) > 7:
        eye_history.pop(0)

    # We consider eyes closed only if the majority (e.g. >= 5 out of 7) frames say they are closed
    smoothed_eyes_closed = sum(eye_history) >= 5

    if smoothed_eyes_closed:
        if closed_start_time is None:
            closed_start_time = time.time()
            alarm_active = False
        else:
            elapsed_time = time.time() - closed_start_time
            status["elapsed_time"] = elapsed_time
        status["alarm_status"] = "Ring"
        status["message"] = "you are asleep stay awake"
        if status["elapsed_time"] >= CLOSED_TIME_LIMIT:
            status["alarm_triggered"] = True
            if not alarm_active:
                winsound.Beep(1000, 1000)
                alarm_active = True
    else:
        closed_start_time = None
        alarm_active = False
        status["elapsed_time"] = 0.0
        status["alarm_triggered"] = False
        status["alarm_status"] = "Normal"
        status["message"] = "you are awake"

    status["eyes_closed"] = smoothed_eyes_closed
    return status

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start_detection():
    if status["running"]:
        return jsonify({"success": False, "message": "Detection is already running."})

    status.update({
        "running": True,
        "eyes_closed": False,
        "alarm_triggered": False,
        "alarm_status": "Normal",
        "elapsed_time": 0.0,
        "message": "Backend started. Allow camera access in the browser.",
    })
    return jsonify({"success": True, "message": "Detection backend started."})

@app.route("/stop", methods=["POST"])
def stop_detection():
    if not status["running"]:
        return jsonify({"success": False, "message": "No detection is currently running."})

    status.update({
        "running": False,
        "eyes_closed": False,
        "alarm_triggered": False,
        "alarm_status": "Normal",
        "elapsed_time": 0.0,
        "message": "Detection stopped.",
    })
    return jsonify({"success": True, "message": "Detection stopped."})

@app.route("/status")
def get_status():
    return jsonify(status)

@app.route("/detect", methods=["POST"])
def detect_frame():
    if not status["running"]:
        return jsonify({"success": False, "message": "Start detection first."}), 400

    data = request.get_json(force=True)
    image_data = data.get("image")
    if not image_data:
        return jsonify({"success": False, "message": "No image provided."}), 400

    frame = decode_image(image_data)
    if frame is None:
        return jsonify({"success": False, "message": "Unable to decode image."}), 400

    analyze_frame(frame)
    return jsonify({"success": True, "status": status})

def open_browser():
    webbrowser.open("http://127.0.0.1:5000", new=2)

if __name__ == "__main__":
    threading.Timer(1.0, open_browser).start()
    app.run(host="0.0.0.0", port=5000, debug=False)
