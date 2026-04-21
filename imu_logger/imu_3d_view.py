import socket
import math
from vpython import box, vector, color, rate, scene

PORT = 4210

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", PORT))
sock.settimeout(1.0)

scene.title = "BNO055 Live 3D Orientation"
scene.width = 900
scene.height = 600
scene.background = color.black

board = box(length=4, height=0.2, width=2, color=color.cyan)

def euler_to_axis_up(heading, roll, pitch):
    h = math.radians(heading)
    r = math.radians(roll)
    p = math.radians(pitch)

    cx, sx = math.cos(r), math.sin(r)
    cy, sy = math.cos(p), math.sin(p)
    cz, sz = math.cos(h), math.sin(h)

    # Rz(h)*Ry(p)*Rx(r)
    R11 = cz * cy
    R13 = cz * sy * cx + sz * sx

    R21 = sz * cy
    R23 = sz * sy * cx - cz * sx

    R31 = -sy
    R33 = cy * cx

    axis = vector(R11, R21, R31)
    up = vector(R13, R23, R33)
    return axis, up

print("Listening on UDP port 4210...")

while True:
    rate(60)
    try:
        data, _ = sock.recvfrom(256)
        line = data.decode(errors="ignore").strip()
        parts = line.split(",")
        if len(parts) != 3:
            continue
        heading, roll, pitch = map(float, parts)
        axis, up = euler_to_axis_up(heading, roll, pitch)
        board.axis = axis
        board.up = up
    except socket.timeout:
        pass
    except Exception as e:
        print("Parse error:", e)