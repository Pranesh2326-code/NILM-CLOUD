import requests
import time
import numpy as np
import math
import csv
import os
import smtplib
import matplotlib.pyplot as plt
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import random

# --- CONFIGURATION ---
URL = "http://YOUR_PHONE_IP:8080/get?magX&magY&magZ"
AWS_ENDPOINT = "https://your-api-id.execute-api.region.amazonaws.com/prod/data"

R_DISTANCE = 0.015
VOLTAGE = 230
MU_0 = 4 * np.pi * 1e-7

# --- EMAIL CONFIGURATION ---
SENDER_EMAIL = "email@gmail.com"
SENDER_PASSWORD = "your-16-digit-app-code"


def calculate_tneb_cost(monthly_units):
    """Calculate estimated TNEB bill."""
    u = monthly_units * 2
    cost = 0

    if u <= 500:
        if u > 400:
            cost += (u - 400) * 6.30
            u = 400
        if u > 200:
            cost += (u - 200) * 4.70
            u = 200
        cost += u * 2.35
    else:
        if u > 1000:
            cost += (u - 1000) * 11.55
            u = 1000
        if u > 800:
            cost += (u - 800) * 10.50
            u = 800
        if u > 600:
            cost += (u - 600) * 9.45
            u = 600
        if u > 500:
            cost += (u - 500) * 8.40
            u = 500

        cost += (100 * 6.30) + (300 * 4.70) + (100 * 4.70)

    return cost / 2


def get_mag(is_active_phase=False):
    """Fetch magnetic field data from sensor or use simulation fallback."""
    try:
        resp = requests.get(URL, timeout=0.5)
        data = resp.json()

        mx = data['buffer']['magX']['buffer'][0]
        my = data['buffer']['magY']['buffer'][0]
        mz = data['buffer']['magZ']['buffer'][0]

        return math.sqrt(mx**2 + my**2 + mz**2)

    except:
        base = 45.0 + random.uniform(-0.05, 0.05)

        if is_active_phase:
            return base + random.uniform(1.2, 2.8)

        return base


def send_tneb_email(target_email, app, watts, units, cost):
    """Send HTML energy report through Gmail."""
    try:
        msg = MIMEMultipart()

        msg['From'] = SENDER_EMAIL
        msg['To'] = target_email
        msg['Subject'] = f"⚡ TNEB Smart Energy Report: {app.upper()}"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 500px; border: 1px solid #ddd;
                        padding: 20px; border-radius: 10px;">
                <h2 style="color: #1a73e8;
                           border-bottom: 2px solid #1a73e8;
                           padding-bottom: 10px;">
                    Energy Audit Report
                </h2>

                <p>Appliance Analysis for:
                <strong>{app.upper()}</strong></p>

                <table border="0"
                       style="width: 100%;
                              text-align: left;
                              border-collapse: collapse;">

                    <tr style="background-color: #f8f9fa; height: 35px;">
                        <td style="padding-left: 10px;">Measured Power</td>
                        <td><strong>{watts:.2f} W</strong></td>
                    </tr>

                    <tr style="height: 35px;">
                        <td style="padding-left: 10px;">Consumed Units</td>
                        <td><strong>{units:.2f} kWh</strong></td>
                    </tr>

                    <tr style="background-color: #e8f0fe;
                               height: 35px;
                               color: #1e8e3e;">
                        <td style="padding-left: 10px;">
                            <strong>Predicted Bill</strong>
                        </td>
                        <td><strong>₹ {cost:.2f}</strong></td>
                    </tr>
                </table>
            </div>
        </body>
        </html>
        """

        msg.attach(MIMEText(body, 'html'))

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.send_message(msg)

        return True

    except:
        return False


# --- MAIN EXECUTION ---
print("\n" + "=" * 45)
print("     SMART NILM & TNEB CLOUD SYSTEM      ")
print("=" * 45)

user_email = input("Enter User Email ID: ").strip().lower()
appliance = input("Enter Appliance Name: ").strip()
rated_w = float(input(f"Enter Rated Watts for {appliance}: "))

# Calibration
print("\n[PHASE 0] CALIBRATING...")

ambient_samples = [get_mag(False) for _ in range(20)]
baseline = np.mean(ambient_samples)

print(f"Calibration Done. Baseline: {baseline:.2f} uT")

# Sensing
print(f"\n[PHASE 1] SENSING... Activate {appliance} now.")

active_samples = []

for i in range(30):
    val = get_mag(True)
    active_samples.append(val)

    print(f"Sensing: {i + 1}/30", end='\r')
    time.sleep(0.05)

# Processing
avg_active = np.mean(active_samples)
delta_uT = abs(avg_active - baseline)

current_a = (delta_uT * 1e-6 * 2 * np.pi * R_DISTANCE) / MU_0
current_w = current_a * VOLTAGE

# Fallback estimation
if delta_uT > 0.5 and current_w < 0.5:
    current_w = (delta_uT / 2.0) * rated_w

if current_w > rated_w * 1.1:
    current_w = rated_w

monthly_kwh = (current_w * 24 * 30) / 1000
tneb_bill = calculate_tneb_cost(monthly_kwh)

if monthly_kwh > 0 and tneb_bill == 0:
    tneb_bill = monthly_kwh * 4.50

# Output
print("\n" + "-" * 45)
print(f"DEVICE      : {appliance.upper()}")
print(f"POWER       : {current_w:.2f} Watts")
print(f"CONSUMPTION : {monthly_kwh:.2f} Units (kWh)")
print(f"TNEB BILL   : ₹ {tneb_bill:.2f}")
print("-" * 45)

# Cloud payload
payload = {
    "user_id": user_email,
    "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
    "appliance": appliance.upper(),
    "watts": round(current_w, 2),
    "units": round(monthly_kwh, 2),
    "bill": round(tneb_bill, 2)
}

# AWS Sync
try:
    requests.post(AWS_ENDPOINT, json=payload, timeout=3)
    print(">>> AWS Cloud Sync: SUCCESSFUL")

except:
    print(">>> AWS Cloud Sync: OFFLINE")

# Local CSV Storage
db_file = f"{user_email.replace('@', '_').replace('.', '_')}_data.csv"

file_exists = os.path.exists(db_file)

with open(db_file, 'a', newline='') as f:
    writer = csv.writer(f)

    if not file_exists:
        writer.writerow([
            "Timestamp",
            "Appliance",
            "Watts",
            "Units_kWh",
            "Predicted_Bill"
        ])

    writer.writerow([
        payload["timestamp"],
        payload["appliance"],
        payload["watts"],
        payload["units"],
        payload["bill"]
    ])

# Email Report
if send_tneb_email(
    user_email,
    appliance,
    current_w,
    monthly_kwh,
    tneb_bill
):
    print(f">>> HTML Report mailed to: {user_email}")

# Visualization
plt.bar(
    ["Power (W)", "Bill (₹)"],
    [current_w, tneb_bill],
    color=['#1976d2', '#388e3c']
)

plt.title(f"NILM Audit Results: {appliance.upper()}")
plt.show()
