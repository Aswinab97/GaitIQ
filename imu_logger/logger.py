import serial
from datetime import datetime

PORT = "COM3"          # change if needed
BAUD = 115200
SECONDS = 60           # recording duration in seconds

filename = f"bno055_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

with serial.Serial(PORT, BAUD, timeout=1) as ser, open(filename, "w", newline="") as f:
    f.write("time_ms,heading,roll,pitch,ax,ay,az,gx,gy,gz\n")
    print(f"Recording to {filename} ...")
    start = datetime.now()

    while (datetime.now() - start).total_seconds() < SECONDS:
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue
        if line[0].isdigit():
            f.write(line + "\n")
            print(line)

print("Done.")