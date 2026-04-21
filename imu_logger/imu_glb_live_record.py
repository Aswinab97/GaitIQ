import socket
import csv
import os
import math
from datetime import datetime

import numpy as np
import trimesh
import pyrender

# =========================
# CONFIG
# =========================
UDP_PORT = 4210
BUFFER_SIZE = 512
GLB_FILE = "prosthetic_leg.glb"
RECORD_SECONDS = None   # None = until Ctrl+C

# =========================
# USER METADATA
# =========================
activity = input("Activity label (e.g., walk_normal): ").strip() or "unlabeled"
subject = input("Subject ID (e.g., aswin_01): ").strip() or "subject_unknown"
trial = input("Trial number (e.g., 01): ").strip() or "01"

out_dir = "recordings"
os.makedirs(out_dir, exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_path = os.path.join(out_dir, f"{activity}_{subject}_trial{trial}_{timestamp}.csv")
print(f"\nCSV -> {csv_path}")

# =========================
# LOAD GLB SCENE (preserve part alignment)
# =========================
if not os.path.exists(GLB_FILE):
    raise FileNotFoundError(f"{GLB_FILE} not found in current folder.")

tri_scene = trimesh.load(GLB_FILE, force="scene")

# Compute scene centroid to rotate naturally around center
all_pts = []
for g in tri_scene.geometry.values():
    if hasattr(g, "vertices"):
        all_pts.append(np.asarray(g.vertices))
if len(all_pts) == 0:
    raise RuntimeError("No mesh vertices found in GLB.")
pts = np.vstack(all_pts)
scene_center = pts.mean(axis=0)

# Convert to pyrender scene
pr_scene = pyrender.Scene(bg_color=[0.05, 0.05, 0.07, 1.0], ambient_light=[0.25, 0.25, 0.25])

# Add original meshes as a grouped root node so we can rotate all together
root_node = pyrender.Node(name="root_rotator", matrix=np.eye(4))
pr_scene.add_node(root_node)

for name, geom in tri_scene.geometry.items():
    mesh = pyrender.Mesh.from_trimesh(geom, smooth=True)
    n = pyrender.Node(mesh=mesh, matrix=np.eye(4), name=f"mesh_{name}")
    pr_scene.add_node(n, parent_node=root_node)

# Camera
camera = pyrender.PerspectiveCamera(yfov=np.pi / 3.0)
cam_pose = np.array([
    [1.0, 0.0, 0.0, 0.0],
    [0.0, 1.0, 0.0, -250.0],
    [0.0, 0.0, 1.0, 140.0],
    [0.0, 0.0, 0.0, 1.0]
])
pr_scene.add(camera, pose=cam_pose)

# Lights
light = pyrender.DirectionalLight(color=np.ones(3), intensity=3.0)
pr_scene.add(light, pose=np.array([
    [1,0,0,100],
    [0,1,0,100],
    [0,0,1,200],
    [0,0,0,1]
]))
pr_scene.add(light, pose=np.array([
    [1,0,0,-100],
    [0,1,0,-100],
    [0,0,1,200],
    [0,0,0,1]
]))

viewer = pyrender.Viewer(
    pr_scene,
    use_raymond_lighting=True,
    run_in_thread=True,
    viewport_size=(1100, 760),
    window_title="Prosthetic IMU Live (GLB)"
)

# =========================
# UDP SOCKET
# =========================
sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", UDP_PORT))
sock.settimeout(0.05)
print(f"Listening UDP on {UDP_PORT} ...")

# =========================
# HELPERS
# =========================
def parse_packet(line: str):
    """
    Accepts:
    A) heading,roll,pitch
    B) time_ms,heading,roll,pitch,ax,ay,az,gx,gy,gz
    """
    p = [x.strip() for x in line.split(",")]
    if len(p) == 3:
        h, r, pit = map(float, p)
        return {
            "time_ms": "",
            "heading": h, "roll": r, "pitch": pit,
            "ax": "", "ay": "", "az": "",
            "gx": "", "gy": "", "gz": ""
        }
    if len(p) >= 10:
        return {
            "time_ms": p[0],
            "heading": float(p[1]), "roll": float(p[2]), "pitch": float(p[3]),
            "ax": p[4], "ay": p[5], "az": p[6],
            "gx": p[7], "gy": p[8], "gz": p[9],
        }
    return None

def rot_matrix(heading_deg, roll_deg, pitch_deg):
    """
    R = Rz(heading) * Ry(pitch) * Rx(roll)
    """
    h = math.radians(heading_deg)
    r = math.radians(roll_deg)
    p = math.radians(pitch_deg)

    cz, sz = math.cos(h), math.sin(h)
    cy, sy = math.cos(p), math.sin(p)
    cx, sx = math.cos(r), math.sin(r)

    Rz = np.array([[cz, -sz, 0],
                   [sz,  cz, 0],
                   [ 0,   0, 1]])
    Ry = np.array([[ cy, 0, sy],
                   [  0, 1,  0],
                   [-sy, 0, cy]])
    Rx = np.array([[1,  0,   0],
                   [0, cx, -sx],
                   [0, sx,  cx]])

    return Rz @ Ry @ Rx

def make_transform(R, center):
    """
    Rotate around scene_center:
      T(center) * R * T(-center)
    """
    T1 = np.eye(4)
    T1[:3, 3] = -center

    T2 = np.eye(4)
    T2[:3, 3] = center

    M = np.eye(4)
    M[:3, :3] = R

    return T2 @ M @ T1

# =========================
# CSV
# =========================
headers = [
    "pc_time_iso", "time_ms", "heading", "roll", "pitch",
    "ax", "ay", "az", "gx", "gy", "gz",
    "activity", "subject", "trial"
]

start_time = datetime.now()
rows = 0

print("Running... Press Ctrl+C to stop.\n")

try:
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        while viewer.is_active:
            if RECORD_SECONDS is not None:
                if (datetime.now() - start_time).total_seconds() >= RECORD_SECONDS:
                    break

            try:
                data, _ = sock.recvfrom(BUFFER_SIZE)
                line = data.decode(errors="ignore").strip()
                d = parse_packet(line)
                if d is None:
                    continue

                heading = d["heading"]
                roll = d["roll"]
                pitch = d["pitch"]

                R = rot_matrix(heading, roll, pitch)
                M = make_transform(R, scene_center)

                with viewer.render_lock:
                    root_node.matrix = M

                now = datetime.now()
                writer.writerow({
                    "pc_time_iso": now.isoformat(timespec="milliseconds"),
                    "time_ms": d["time_ms"],
                    "heading": heading,
                    "roll": roll,
                    "pitch": pitch,
                    "ax": d["ax"], "ay": d["ay"], "az": d["az"],
                    "gx": d["gx"], "gy": d["gy"], "gz": d["gz"],
                    "activity": activity, "subject": subject, "trial": trial
                })
                rows += 1

            except socket.timeout:
                pass
            except Exception:
                pass

except KeyboardInterrupt:
    print("\nStopped by user.")

finally:
    sock.close()
    viewer.close_external()
    print(f"Saved CSV: {csv_path}")
    print(f"Rows written: {rows}")