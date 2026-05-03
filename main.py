import requests
import numpy as np
import time
from datetime import datetime

# --- CONFIGURATION ---
# Replace with your actual Phone IP and AWS Endpoint
SENSOR_URL = "http://192.168.x.x:8080/sensors.json" 
AWS_ENDPOINT = "https://your-api-id.execute-api.region.amazonaws.com/prod/energy"
USER_EMAIL = "your-email@example.com"

def get_mag_data():
    try:
        response = requests.get(SENSOR_URL, timeout=2)
        data = response.json()
        # Extracting Magnetometer XYZ values
        mag = data['mag']['data'][-1] 
        return np.sqrt(mag[1][0]**2 + mag[1][1]**2 + mag[1][2]**2)
    except:
        return None

def sync_to_cloud(payload):
    try:
        res = requests.post(AWS_ENDPOINT, json=payload)
        if res.status_code == 200:
            print(">>> AWS Cloud Sync: SUCCESSFUL")
        else:
            print(f">>> AWS Cloud Sync: FAILED (Status: {res.status_code})")
    except Exception as e:
        print(f"Sync Error: {e}")

# --- MAIN EXECUTION ---
print("[PHASE 0] CALIBRATING...")
baseline = np.mean([get_mag_data() for _ in range(20) if get_mag_data() is not None])
print(f"Baseline established: {baseline:.2f} uT")

input("[PHASE 1] Turn on appliance and press Enter...")
active_val = np.mean([get_mag_data() for _ in range(20) if get_mag_data() is not None])
delta_uT = abs(active_val - baseline)

# Simplified Physics: Watts = Delta_uT * Calibration_Factor
# (Replace 5.5 with your derived calibration constant)
watts = delta_uT * 5.5 
bill = (watts / 1000) * 4.50 # Example TNEB slab

payload = {
    "user_id": USER_EMAIL,
    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "appliance": "TEST_DEVICE",
    "watts": round(watts, 2),
    "bill": round(bill, 2)
}

sync_to_cloud(payload)
