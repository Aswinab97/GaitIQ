# --- replace your current file with this full version ---
import socket
import csv
import os
import math
from datetime import datetime

import numpy as np
import pyvista as pv

UDP_PORT = 4210
BUFFER_SIZE = 512
MODEL_FILE = "prosthetic_leg.glb"
RECORD_SECONDS = None

activity = input("Activity label: ").strip() or "unlabeled"
subject = input("Subject ID: ").strip() or "subject_unknown"
trial = input("Trial number: ").strip() or "01"

os.makedirs("recordings", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
csv_path = f"recordings/{activity}_{subject}_trial{trial}_{ts}.csv"
print("CSV ->", csv_path)

if not os.path.exists(MODEL_FILE):
    raise FileNotFoundError(f"{MODEL_FILE} not found.")

dataset = pv.read(MODEL_FILE)

def collect_polydata(obj, out_list):
    if obj is None:
        return
    if isinstance(obj, pv.MultiBlock):
        for i in range(obj.n_blocks):
            collect_polydata(obj[i], out_list)
    else:
        try:
            surf = obj.extract_surface().triangulate()
            if surf.n_points > 0:
                out_list.append(surf)
        except Exception:
            pass

parts = []
collect_polydata(dataset, parts)

if not parts:
    raise RuntimeError("No valid geometry found in model.")

mesh0 = parts[0].copy(deep=True)
for p in parts[1:]:
    mesh0 = mesh0.merge(p, merge_points=False)

center = np.array(mesh0.center)
mesh_base = mesh0.copy(deep=True)
mesh_base.translate(-center, inplace=True)
mesh_live = mesh_base.copy(deep=True)

plotter = pv.Plotter(window_size=(1200, 800))
plotter.set_background("#202020")
plotter.add_mesh(mesh_live, smooth_shading=True)
plotter.add_axes()
plotter.add_text("IMU Prosthetic Live (PyVista)", font_size=12, color="white")

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", UDP_PORT))
sock.settimeout(0.02)
print(f"Listening UDP on {UDP_PORT} ...")

def parse_packet(line):
    p = [x.strip() for x in line.split(",")]
    if len(p) == 3:
        h, r, pit = map(float, p)
        return {"time_ms":"", "heading":h, "roll":r, "pitch":pit,
                "ax":"", "ay":"", "az":"", "gx":"", "gy":"", "gz":""}
    if len(p) >= 10:
        return {"time_ms":p[0], "heading":float(p[1]), "roll":float(p[2]), "pitch":float(p[3]),
                "ax":p[4], "ay":p[5], "az":p[6], "gx":p[7], "gy":p[8], "gz":p[9]}
    return None

def R_from_euler(heading, roll, pitch):
    h, r, p = map(math.radians, [heading, roll, pitch])
    cz, sz = math.cos(h), math.sin(h)
    cy, sy = math.cos(p), math.sin(p)
    cx, sx = math.cos(r), math.sin(r)
    Rz = np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])
    Ry = np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    Rx = np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
    return Rz @ Ry @ Rx

headers = ["pc_time_iso","time_ms","heading","roll","pitch","ax","ay","az","gx","gy","gz","activity","subject","trial"]

rows = 0
start = datetime.now()

with open(csv_path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=headers)
    w.writeheader()

    plotter.show(auto_close=False, interactive_update=True)

    try:
        while True:
            if RECORD_SECONDS and (datetime.now()-start).total_seconds() >= RECORD_SECONDS:
                break

            try:
                data, _ = sock.recvfrom(BUFFER_SIZE)
                d = parse_packet(data.decode(errors="ignore").strip())
                if d is None:
                    continue

                R = R_from_euler(d["heading"], d["roll"], d["pitch"])
                mesh_live.points = np.asarray(mesh_base.points) @ R.T
                plotter.render()

                now = datetime.now()
                w.writerow({
                    "pc_time_iso": now.isoformat(timespec="milliseconds"),
                    "time_ms": d["time_ms"],
                    "heading": d["heading"], "roll": d["roll"], "pitch": d["pitch"],
                    "ax": d["ax"], "ay": d["ay"], "az": d["az"],
                    "gx": d["gx"], "gy": d["gy"], "gz": d["gz"],
                    "activity": activity, "subject": subject, "trial": trial
                })
                rows += 1

            except socket.timeout:
                plotter.update()

    except KeyboardInterrupt:
        pass
    finally:
        sock.close()
        plotter.close()
        print(f"Saved CSV: {csv_path}")
        print(f"Rows written: {rows}")