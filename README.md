# ⚡ NILM Smart Billing System

### *IoT-based Energy Auditing using Smartphone Magnetometers*

## 📌 How it Works
1. **Sensing:** Uses the smartphone magnetometer as a non-contact current probe.
2. **Analysis:** Python processes the magnetic delta into real-time Wattage.
3. **Cloud:** Data is synced to **AWS DynamoDB** via **API Gateway**.
4. **Billing:** Calculates monthly costs based on **TNEB** domestic tariff slabs.

## 🛠️ Tech Stack
* **Language:** Python
* **Cloud:** AWS (Lambda, DynamoDB, API Gateway)
* **Hardware:** Smartphone Hall Effect Sensor
