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

# --- CONFIGURATION & CONSTANTS ---
# 1. Update with your Phone's IP from the sensor app
URL ="" # The IP

# 2. Update with your AWS API Gateway Invoke URL
CLOUD_DB_URL = "" #Your API link

R_DISTANCE = 0.015  # 1.5cm sensing distance
VOLTAGE = 230       # Standard AC Voltage
MU_0 = 4 * np.pi * 1e-7

# --- GMAIL AUTOMATION SETUP ---
SENDER_EMAIL = "" # Sender mail -id
SENDER_PASSWORD ="" # Your 16-digit Google App Password

# --- TNEB BI-MONTHLY BILLING ENGINE ---
def calculate_tneb_cost(monthly_units):
    """Calculates cost based on TNEB Bi-monthly slabs without the 100-unit free rule."""
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

# --- CORE FUNCTIONS ---
def get_mag():
    """Fetches raw magnetic data from the smartphone sensor."""
    try:
        resp = requests.get(URL, timeout=0.8).json()
        mx = resp['buffer']['magX']['buffer'][0]
        my = resp['buffer']['magY']['buffer'][0]
        mz = resp['buffer']['magZ']['buffer'][0]
        return math.sqrt(mx ** 2 + my ** 2 + mz ** 2)
    except:
        return None

def get_historical_watts(filename, appliance_name):
    """Reads local CSV for historical appliance data."""
    history = []
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['Appliance'].lower() == appliance_name.lower():
                    val = row.get('Watts') or row.get('Power')
                    if val: history.append(float(val))
    return history

# --- AWS CLOUD SYNC FUNCTION ---
def sync_data_to_aws(mail_id, app, watts, units, bill):
    """Transmits data to AWS DynamoDB via API Gateway & Lambda."""
    payload = {
        "user_id": mail_id,
        "timestamp": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "appliance": app.upper(),
        "watts": round(watts, 2),
        "units": round(units, 2),
        "bill": round(bill, 2)
    }
    try:
        response = requests.post(CLOUD_DB_URL, json=payload, timeout=5)
        if response.status_code == 200:
            print(">>> AWS Cloud Sync: SUCCESSFUL")
            return True
        else:
            print(f">>> AWS Cloud Sync: FAILED (Status: {response.status_code})")
    except Exception as e:
        print(f">>> AWS Cloud Sync: ERROR ({str(e)})")
    return False

def send_tneb_email(target_email, app, watts, units, cost):
    """Sends the formatted HTML report via Gmail SMTP."""
    try:
        msg = MIMEMultipart()
        msg['From'] = SENDER_EMAIL
        msg['To'] = target_email
        msg['Subject'] = f"⚡ TNEB Smart Energy Report: {app.upper()}"

        body = f"""
        <html>
        <body style="font-family: Arial, sans-serif;">
            <div style="max-width: 500px; border: 1px solid #ddd; padding: 20px; border-radius: 10px;">
                <h2 style="color: #1a73e8; border-bottom: 2px solid #1a73e8; padding-bottom: 10px;">Energy Audit Report</h2>
                <p>Appliance Analysis for: <strong>{app.upper()}</strong></p>
                <table border="0" style="width: 100%; text-align: left; border-collapse: collapse;">
                    <tr style="background-color: #f8f9fa; height: 35px;">
                        <td style="padding-left: 10px;">Measured Power</td>
                        <td><strong>{watts:.2f} W</strong></td>
                    </tr>
                    <tr style="height: 35px;">
                        <td style="padding-left: 10px;">Consumed Units</td>
                        <td><strong>{units:.2f} kWh</strong></td>
                    </tr>
                    <tr style="background-color: #e8f0fe; height: 35px; color: #1e8e3e;">
                        <td style="padding-left: 10px;"><strong>Predicted Bill</strong></td>
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

# --- MAIN EXECUTION PIPELINE ---
print("\n" + "=" * 45)
print("   NILM SMART SENSING & AWS CLOUD SYSTEM   ")
print("=" * 45)

user_email = input("Enter User Email ID: ").strip().lower()
appliance = input("Enter Appliance Name: ").strip()
rated_w = float(input(f"Enter Rated Watts for {appliance}: "))

db_file = f"{user_email.replace('@', '_').replace('.', '_')}_data.csv"

# PHASE 0: CALIBRATION
print("\n[PHASE 0] CALIBRATING... Keep phone stationary.")
ambient_samples = []
for i in range(30):
    val = get_mag()
    if val: ambient_samples.append(val)
    time.sleep(0.1)
baseline = np.mean(ambient_samples) if ambient_samples else 0
print(f"Calibration Done. Baseline: {baseline:.2f} uT")

# PHASE 1: SENSING
print(f"\n[PHASE 1] SENSING... Activate {appliance} now.")
active_samples = []
for i in range(100):
    val = get_mag()
    if val: active_samples.append(val)
    time.sleep(0.1)

# PHASE 2: ANALYTICS
avg_active = np.mean(active_samples[40:]) if len(active_samples) > 40 else (np.mean(active_samples) if active_samples else baseline)
delta_uT = abs(avg_active - baseline)
current_a = (delta_uT * 1e-6 * 2 * np.pi * R_DISTANCE) / MU_0 if delta_uT > 0.1 else 0 # default is 0.5 instead of 0.1
current_w = current_a * VOLTAGE
if current_w > rated_w * 1.5: current_w = rated_w

past_readings = get_historical_watts(db_file, appliance)
final_avg_watts = np.mean(past_readings + [current_w]) if past_readings else current_w
monthly_kwh = (final_avg_watts * 24 * 30) / 1000
tneb_bill = calculate_tneb_cost(monthly_kwh)

# PHASE 3: MULTI-LAYER DATA ARCHIVING
print("\n" + "-" * 45)
print(f"DEVICE      : {appliance.upper()}")
print(f"POWER       : {current_w:.2f} Watts")
print(f"UNITS       : {monthly_kwh:.2f} kWh")
print(f"TNEB BILL   : ₹ {tneb_bill:.2f}")
print("-" * 45)

# 1. Local Storage (CSV)
file_exists = os.path.exists(db_file)
with open(db_file, 'a', newline='', encoding='utf-8') as f:
    writer = csv.writer(f)
    if not file_exists:
        writer.writerow(["Timestamp", "Appliance", "Watts", "Predicted_Bill"])
    writer.writerow([datetime.now().strftime('%Y-%m-%d %H:%M:%S'), appliance, round(current_w, 2), round(tneb_bill, 2)])

# 2. Cloud Storage (AWS DynamoDB)
sync_data_to_aws(user_email, appliance, current_w, monthly_kwh, tneb_bill)

# 3. User Dispatch (Email)
if send_tneb_email(user_email, appliance, current_w, monthly_kwh, tneb_bill):
    print(f"\n>>> Energy report sent to: {user_email}")

# --- PHASE 4: VISUALIZATION ---
plt.style.use('bmh')
fig = plt.figure(figsize=(14, 8))
grid = plt.GridSpec(2, 3, wspace=0.4, hspace=0.4)
ax1 = fig.add_subplot(grid[0, :2])
ax1.bar(["Current Reading", "Historical Avg"], [current_w, final_avg_watts], color=['#d32f2f', '#1976d2'])
ax1.set_title("Power Analysis (Watts)")
ax2 = fig.add_subplot(grid[1, :2])
ax2.bar(["Monthly Bill Projection"], [tneb_bill], color='#388e3c', width=0.4)
ax2.set_title("Financial Projection")
ax3 = fig.add_subplot(grid[:, 2])
ax3.axis('off')
report_text = (f"ENERGY AUDIT\n{'-'*15}\n"
               f"Appliance: {appliance.upper()}\n"
               f"Power: {current_w:.1f} W\n"
               f"Units: {monthly_kwh:.2f} kWh\n"
               f"Bill: ₹ {tneb_bill:.2f}")
ax3.text(0.05, 0.5, report_text, fontsize=14, family='monospace', bbox=dict(facecolor='#e8f0fe', alpha=0.8))
plt.show()
