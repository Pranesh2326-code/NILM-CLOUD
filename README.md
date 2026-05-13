⚡ NILM Smart Billing System (TNEB Integrated)
An IoT-based approach to Non-Intrusive Load Monitoring using Smartphone Magnetometers.
📌 Project Overview
This project presents a cost-effective, non-contact method for monitoring household energy consumption. As a final-year Electrical and Electronics Engineering (EEE) student project, it demonstrates how Digital Signal Processing (DSP) and Cloud Computing can be used to perform energy audits without the need for expensive clip-on ammeters or invasive wiring.

By utilizing the Hall Effect sensor (magnetometer) inside a standard smartphone, we capture the magnetic signature of an appliance. The system then processes this "Energy Fingerprint" to calculate real-time wattage and predict monthly electricity bills based on the TNEB (Tamil Nadu Electricity Board) domestic tariff slabs.

🚀 Key Features
Non-Intrusive Sensing: Uses a smartphone as a current probe via an IP-based sensor bridge.

Hybrid Sensing Logic: Built-in auto-calibration and fallback mode to ensure system stability during network latency.

AWS Cloud Integration: Syncs real-time data (Watts, Units, Bill) to Amazon DynamoDB via AWS API Gateway and Lambda.

Automated Reporting: Generates and emails a professional HTML energy audit report to the user’s Gmail.

TNEB Billing Engine: Accurate bi-monthly billing simulation based on current Tamil Nadu power slabs.

Edge Visualization: Real-time bar charts for instant power and financial analysis.

🛠️ Technical Stack
Language: Python 3.x

Cloud: AWS (Lambda, DynamoDB, API Gateway)

Sensing: Smartphone Magnetometer (via IP Sensor App)

Libraries: NumPy, Matplotlib, Requests, SMTPLib

Database: DynamoDB (Cloud) & CSV (Local Edge)
