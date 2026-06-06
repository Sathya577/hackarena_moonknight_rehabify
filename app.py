from flask import Flask, render_template, Response

import cv2
import mediapipe as mp
import numpy as np
import random
import math
import json
import time

app = Flask(__name__)

# -----------------------------
# MediaPipe Setup
# -----------------------------
mp_pose = mp.solutions.pose
pose = mp_pose.Pose()

# -----------------------------
# Webcam
# -----------------------------
cap = cv2.VideoCapture(0)

# -----------------------------
# Load Balloon PNG
# -----------------------------
balloon_img = cv2.imread(
    "static/balloon.png",
    cv2.IMREAD_UNCHANGED
)

if balloon_img is None:
    print("ERROR: balloon image not found")
    exit()

balloon_size = 100

balloon_img = cv2.resize(
    balloon_img,
    (balloon_size, balloon_size)
)

# -----------------------------
# Game Variables
# -----------------------------
score = 0
max_angle = 0

rep_count = 0

correct_frames = 0
total_frames = 0

stage = "down"

session_start = time.time()

balloon_x = 500
balloon_y = random.randint(120, 400)

balloon_radius = 50

balloon_direction = 1

MIN_ANGLE = 40
MAX_ANGLE = 110

popped = False

# -----------------------------
# Angle Calculation
# -----------------------------
def calculate_angle(a, b, c):

    a = np.array(a)
    b = np.array(b)
    c = np.array(c)

    radians = np.arctan2(
        c[1] - b[1],
        c[0] - b[0]
    ) - np.arctan2(
        a[1] - b[1],
        a[0] - b[0]
    )

    angle = np.abs(radians * 180.0 / np.pi)

    if angle > 180:
        angle = 360 - angle

    return angle

# -----------------------------
# Distance Formula
# -----------------------------
def distance(x1, y1, x2, y2):

    return math.sqrt(
        (x2 - x1) ** 2 +
        (y2 - y1) ** 2
    )

# -----------------------------
# PNG Overlay Function
# -----------------------------
def overlay_png(background, overlay, x, y):

    h, w = overlay.shape[:2]

    if x < 0 or y < 0:
        return background

    if x + w > background.shape[1]:
        return background

    if y + h > background.shape[0]:
        return background

    overlay_rgb = overlay[:, :, :3]

    mask = overlay[:, :, 3] / 255.0

    bg_region = background[y:y+h, x:x+w]

    for c in range(3):

        bg_region[:, :, c] = (
            (1 - mask) * bg_region[:, :, c]
            + mask * overlay_rgb[:, :, c]
        )

    background[y:y+h, x:x+w] = bg_region

    return background

# -----------------------------
# Video Stream Generator
# -----------------------------
def generate_frames():

    global balloon_x
    global balloon_y
    global score
    global popped
    global balloon_direction
    global max_angle
    global rep_count
    global correct_frames
    global total_frames
    global stage

    while True:

        success, frame = cap.read()

        if not success:
            break

        # Mirror webcam
        frame = cv2.flip(frame, 1)

        h, w, _ = frame.shape

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        results = pose.process(rgb)

        angle = 0

        wrist_x = 0
        wrist_y = 0

        correct_form = False

        # -----------------------------
        # Pose Detection
        # -----------------------------
        if results.pose_landmarks:

            landmarks = results.pose_landmarks.landmark

            shoulder = [
                landmarks[
                    mp_pose.PoseLandmark.LEFT_SHOULDER
                ].x,

                landmarks[
                    mp_pose.PoseLandmark.LEFT_SHOULDER
                ].y
            ]

            elbow = [
                landmarks[
                    mp_pose.PoseLandmark.LEFT_ELBOW
                ].x,

                landmarks[
                    mp_pose.PoseLandmark.LEFT_ELBOW
                ].y
            ]

            hip = [
                landmarks[
                    mp_pose.PoseLandmark.LEFT_HIP
                ].x,

                landmarks[
                    mp_pose.PoseLandmark.LEFT_HIP
                ].y
            ]

            wrist = landmarks[
                mp_pose.PoseLandmark.LEFT_WRIST
            ]

            # Convert to screen coordinates
            shoulder_x = int(shoulder[0] * w)
            shoulder_y = int(shoulder[1] * h)

            elbow_x = int(elbow[0] * w)
            elbow_y = int(elbow[1] * h)

            wrist_x = int(wrist.x * w)
            wrist_y = int(wrist.y * h)

            # Calculate angle
            angle = calculate_angle(
                hip,
                shoulder,
                elbow
            )
            max_angle = max(
               max_angle,
               angle
            )
            if angle > 100:
              stage = "up"

            if angle < 40 and stage == "up":

                rep_count += 1
                stage = "down"
            # Rehab validation
            if MIN_ANGLE <= angle <= MAX_ANGLE:
                correct_form = True
            total_frames += 1

            if correct_form:
                correct_frames += 1    

            # -----------------------------
            # Neon Arm Tracking
            # -----------------------------
            neon_color = (255, 255, 0)

            for thickness in [20, 14, 8]:

                glow_color = (
                    neon_color[0] // (thickness // 4),
                    neon_color[1] // (thickness // 4),
                    neon_color[2] // (thickness // 4)
                )

                cv2.line(
                    frame,
                    (shoulder_x, shoulder_y),
                    (elbow_x, elbow_y),
                    glow_color,
                    thickness
                )

                cv2.line(
                    frame,
                    (elbow_x, elbow_y),
                    (wrist_x, wrist_y),
                    glow_color,
                    thickness
                )

            cv2.line(
                frame,
                (shoulder_x, shoulder_y),
                (elbow_x, elbow_y),
                neon_color,
                4
            )

            cv2.line(
                frame,
                (elbow_x, elbow_y),
                (wrist_x, wrist_y),
                neon_color,
                4
            )

            # -----------------------------
            # Floating Balloon Animation
            # -----------------------------
            balloon_y += balloon_direction

            if balloon_y > 320:
                balloon_direction = -1

            if balloon_y < 180:
                balloon_direction = 1

            # -----------------------------
            # Draw Balloon PNG
            # -----------------------------
            frame = overlay_png(
                frame,
                balloon_img,
                balloon_x - balloon_size // 2,
                balloon_y - balloon_size // 2
            )

            # -----------------------------
            # Collision Detection
            # -----------------------------
            dist = distance(
                wrist_x,
                wrist_y,
                balloon_x,
                balloon_y
            )

            # -----------------------------
            # Wrist Color Feedback
            # -----------------------------
            wrist_color = (255, 0, 0)

            if dist < 50 and correct_form:
                wrist_color = (0, 255, 0)

            # Neon joints
            for point in [
                (shoulder_x, shoulder_y),
                (elbow_x, elbow_y)
            ]:

                cv2.circle(
                    frame,
                    point,
                    14,
                    (255, 255, 255),
                    -1
                )

                cv2.circle(
                    frame,
                    point,
                    8,
                    neon_color,
                    -1
                )

            # Wrist tracker
            cv2.circle(
                frame,
                (wrist_x, wrist_y),
                16,
                (255, 255, 255),
                -1
            )

            cv2.circle(
                frame,
                (wrist_x, wrist_y),
                10,
                wrist_color,
                -1
            )

            # -----------------------------
            # Balloon Pop Logic
            # -----------------------------
            if dist < balloon_radius and correct_form and not popped:

                score += 1

                popped = True

                balloon_x = random.randint(
                    250,
                    w - 150
                )

                balloon_y = random.randint(
                    120,
                    h - 150
                )

            # Reset pop after lowering arm
            if angle < 20:
                popped = False
            posture_score = 0

            if total_frames > 0:

               posture_score = (
               correct_frames
              /
              total_frames
             ) * 100

            report = {
              "max_angle":
               round(max_angle),

               "reps":
                rep_count,

               "posture_score":
                  round(posture_score),

                "score":
                   score,

                "duration":
                 round(
                time.time()
                 -
                session_start
              )
            }    
            
            with open(
                "session_report.json",
                   "w"
            ) as f:

               json.dump(
                 report,
                 f
               ) 
            
            

        # -----------------------------
        # UI TEXT
        # -----------------------------
        cv2.putText(
            frame,
            f"Score: {score}",
            (30, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (0, 255, 255),
            3
        )

        cv2.putText(
            frame,
            f"Angle: {int(angle)}",
            (30, 100),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (255, 255, 255),
            2
        )

        if correct_form:
            form_text = "GOOD FORM"
            form_color = (0, 255, 0)
        else:
            form_text = "ALIGN SHOULDER"
            form_color = (0, 0, 255)

        cv2.putText(
            frame,
            form_text,
            (30, 150),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            form_color,
            2
        )

        cv2.putText(
            frame,
            "Touch balloon with LEFT hand",
            (30, 200),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 0),
            2
        )

        # Encode frame
        ret, buffer = cv2.imencode('.jpg', frame)

        frame = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            frame +
            b'\r\n'
        )

# -----------------------------
# Routes
# -----------------------------
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():

    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )

# -----------------------------
# Run Flask
# -----------------------------
if __name__ == "__main__":

    app.run(
        debug=True
    )