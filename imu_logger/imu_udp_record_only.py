# save as imu_udp_record_only.py
import socket, csv, os
from datetime import datetime

UDP_PORT = 4210
BUFFER = 512

activity = input("Activity label: ").strip() or "unlabeled"
subject  = input("Subject ID: ").strip() or "subject_unknown"
trial    = input("Trial number: ").strip() or "01"

os.makedirs("recordings", exist_ok=True)
ts = datetime.now().strftime("%Y%m%d_%H%M%S")
path = f"recordings/{activity}_{subject}_trial{trial}_{ts}.csv"
print("Saving ->", path)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.bind(("0.0.0.0", UDP_PORT))
print(f"Listening UDP {UDP_PORT} ... Ctrl+C to stop")

headers = ["pc_time_iso","time_ms","heading","roll","pitch","ax","ay","az","gx","gy","gz","activity","subject","trial"]
rows=0

with open(path, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=headers)
    w.writeheader()
    try:
        while True:
            data,_ = sock.recvfrom(BUFFER)
            p = data.decode(errors="ignore").strip().split(",")
            if len(p)==3:
                t,h,r,pit = "",p[0],p[1],p[2]
                ax=ay=az=gx=gy=gz=""
            elif len(p)>=10:
                t,h,r,pit,ax,ay,az,gx,gy,gz = p[:10]
            else:
                continue

            w.writerow({
                "pc_time_iso": datetime.now().isoformat(timespec="milliseconds"),
                "time_ms": t, "heading": h, "roll": r, "pitch": pit,
                "ax": ax, "ay": ay, "az": az, "gx": gx, "gy": gy, "gz": gz,
                "activity": activity, "subject": subject, "trial": trial
            })
            rows += 1
            if rows % 50 == 0:
                print("rows:", rows)
    except KeyboardInterrupt:
        pass

sock.close()
print("Saved rows:", rows)