import socket
import math
import csv
import os
from datetime import datetime
from collections import deque

from vpython import box, vector, color, rate, scene, label

# =========================
# CONFIG
# =========================
UDP_PORT = 4210
BUFFER_SIZE = 512
WINDOW_TITLE = "IMU Live 3D + CSV Recorder"

# Recording duration in seconds (set None for manual stop with Ctrl+C)
RECORD_SECONDS = None

# =========================
# USER INPUT
# =========================
activity = input("Enter activity label (e.g., walk_normal, stairs_up, sit_to_stand): ").strip()
if not activity:
    activity = "unlabeled"

subject = input("Enter subject id (e.g., aswin_01): ").strip()
if not subject:
    subject = "subject_unknown"

trial = input("Enter trial number (e.g., 01): ").strip()
if not trial:
    trial = "01"

# Create output folder
out_dir = "recordings"
os.makedirs(out_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_name = f"{activity}_{subject}_trial{trial}_{timestamp}.csv"
csv_path = os.path.join(out_dir, csv_name)

print(f"\nCSV will be saved to: {csv_path}")

# =========================
# UDP SOCKET
# =========================
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", UDP_PORT))
sock.settimeout(1.0)
print(f"Listening for UDP on port {UDP_PORT} ...")

# =========================
# VPYTHON SCENE
# =========================
scene.title = WINDOW_TITLE
scene.width = 1100
scene.height = 700
scene.background = color.black
scene.center = vector(0, 0, 0)

# Main 3D object (current: box)
board = box(length=4, height=0.25, width=1.5, color=color.cyan)

# Axis helpers
x_axis = box(pos=vector(2.8, 0, 0), length=5.6, height=0.03, width=0.03, color=color.red)
y_axis = box(pos=vector(0, 2.8, 0), length=0.03, height=5.6, width=0.03, color=color.green)
z_axis = box(pos=vector(0, 0, 2.8), length=0.03, height=0.03, width=5.6, color=color.blue)

info = label(
    pos=vector(0, -2.8, 0),
    text="Waiting for IMU data...",
    height=14,
    box=False,
    color=color.white
)

# =========================
# OPTIONAL STL PLACEHOLDER
# =========================
# If later you want a prosthetic leg STL model:
# 1) Place "prosthetic_leg.stl" in same folder
# 2) We can render it with a different 3D engine (PyVista/Open3D) more easily than VPython.
#    VPython is excellent for quick orientation demos but limited for complex meshes.

# =========================
# HELPERS
# =========================
def euler_to_axis_up(heading_deg, roll_deg, pitch_deg):
    """
    Converts BNO055 Euler angles (heading, roll, pitch) into VPython axis/up vectors.
    """
    h = math.radians(heading_deg)
    r = math.radians(roll_deg)
    p = math.radians(pitch_deg)

    cx, sx = math.cos(r), math.sin(r)
    cy, sy = math.cos(p), math.sin(p)
    cz, sz = math.cos(h), math.sin(h)

    # Rotation matrix Rz(h)*Ry(p)*Rx(r)
    R11 = cz * cy
    R13 = cz * sy * cx + sz * sx

    R21 = sz * cy
    R23 = sz * sy * cx - cz * sx

    R31 = -sy
    R33 = cy * cx

    axis_vec = vector(R11, R21, R31)   # forward
    up_vec   = vector(R13, R23, R33)   # up
    return axis_vec, up_vec

def parse_packet(line):
    """
    Accepts either:
    A) heading,roll,pitch
    B) time_ms,heading,roll,pitch,ax,ay,az,gx,gy,gz
    Returns dict with available fields.
    """
    parts = [p.strip() for p in line.split(",")]
    if len(parts) == 3:
        heading, roll, pitch = map(float, parts)
        return {
            "time_ms": "",
            "heading": heading,
            "roll": roll,
            "pitch": pitch,
            "ax": "",
            "ay": "",
            "az": "",
            "gx": "",
            "gy": "",
            "gz": "",
        }
    elif len(parts) >= 10:
        return {
            "time_ms": parts[0],
            "heading": float(parts[1]),
            "roll": float(parts[2]),
            "pitch": float(parts[3]),
            "ax": parts[4],
            "ay": parts[5],
            "az": parts[6],
            "gx": parts[7],
            "gy": parts[8],
            "gz": parts[9],
        }
    return None

# =========================
# CSV SETUP
# =========================
headers = ["pc_time_iso", "time_ms", "heading", "roll", "pitch", "ax", "ay", "az", "gx", "gy", "gz", "activity", "subject", "trial"]

start_time = datetime.now()
rows_written = 0
last_rates = deque(maxlen=30)

print("\nRecording started. Press Ctrl+C to stop.\n")

try:
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        while True:
            rate(60)

            # Optional timed stop
            if RECORD_SECONDS is not None:
                if (datetime.now() - start_time).total_seconds() >= RECORD_SECONDS:
                    print("Reached fixed recording duration.")
                    break

            try:
                data, addr = sock.recvfrom(BUFFER_SIZE)
                now = datetime.now()
                line = data.decode(errors="ignore").strip()

                parsed = parse_packet(line)
                if parsed is None:
                    continue

                heading = parsed["heading"]
                roll = parsed["roll"]
                pitch = parsed["pitch"]

                # Update 3D orientation
                axis_v, up_v = euler_to_axis_up(heading, roll, pitch)
                board.axis = axis_v
                board.up = up_v

                # Update on-screen info
                info.text = (
                    f"IP: {addr[0]}:{addr[1]}\n"
                    f"heading={heading:.2f}  roll={roll:.2f}  pitch={pitch:.2f}\n"
                    f"rows={rows_written}"
                )

                # Write CSV row
                row = {
                    "pc_time_iso": now.isoformat(timespec="milliseconds"),
                    "time_ms": parsed["time_ms"],
                    "heading": heading,
                    "roll": roll,
                    "pitch": pitch,
                    "ax": parsed["ax"],
                    "ay": parsed["ay"],
                    "az": parsed["az"],
                    "gx": parsed["gx"],
                    "gy": parsed["gy"],
                    "gz": parsed["gz"],
                    "activity": activity,
                    "subject": subject,
                    "trial": trial,
                }
                writer.writerow(row)
                rows_written += 1

            except socket.timeout:
                pass
            except ValueError:
                # skip malformed numeric packets
                continue

except KeyboardInterrupt:
    print("\nStopped by user (Ctrl+C).")

finally:
    sock.close()
    print(f"Saved: {csv_path}")
    print(f"Total rows: {rows_written}")