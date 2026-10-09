# 🏫 BreatheSafe — School AQI Advisory System (India)

[![Live Demo](https://img.shields.io/badge/Live%20Demo-AWS%20S3%20Hosted-22c55e?style=for-the-badge&logo=amazon-s3)](http://breathesafe-site-manasalshegde.s3-website.ap-south-1.amazonaws.com/)
[![AWS Serverless](https://img.shields.io/badge/AWS-Serverless%20Architecture-FF9900?style=for-the-badge&logo=amazon-aws)](https://aws.amazon.com/)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python)](https://python.org)
[![CPCB Standard](https://img.shields.io/badge/Standard-India%20CPCB%20AQI-0ea5e9?style=for-the-badge)](https://cpcb.nic.in/)
[![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=for-the-badge)](LICENSE)

> **BreatheSafe** is an AWS-powered real-time air quality forecasting and automated health advisory system designed specifically for schools across India. It features an interactive nationwide station map, an Exponentially Weighted Moving Average (EWMA) forecast engine, and clear **GO / CAUTION / NO-GO** advisories with actionable safety protocols for school administrators and principals.
> 
> *Developed for **Bharat Builds Tour: Environmental Hacks (Track 1 — Air)**.*

---

## 🌐 Live Deployment & Endpoints

- 🔗 **Interactive Dashboard (AWS S3):**  
  [http://breathesafe-site-manasalshegde.s3-website.ap-south-1.amazonaws.com/](http://breathesafe-site-manasalshegde.s3-website.ap-south-1.amazonaws.com/)
- ⚡ **Live API Gateway Endpoint:**  
  `https://hkq4cb4v30.execute-api.ap-south-1.amazonaws.com/forecast`
- 🛡️ **Sample Live Station Query:**  
  [`https://hkq4cb4v30.execute-api.ap-south-1.amazonaws.com/forecast?station=8675`](https://hkq4cb4v30.execute-api.ap-south-1.amazonaws.com/forecast?station=8675)

---

## 📌 The Problem

During critical months across India (stubble burning, winter temperature inversions, urban transit congestion), millions of schoolchildren in Delhi-NCR, Mumbai, Kolkata, Lucknow, Patna, and Bengaluru breathe dangerously polluted air during morning assemblies, outdoor physical education, and recess. 

Schools currently face three severe challenges:
1. **Delayed Information:** Generic news apps show city-wide averages from hours earlier, missing hyper-local morning smog spikes.
2. **Analysis Paralysis:** Raw numbers (e.g., `PM2.5: 185 µg/m³`) provide no actionable guidance on whether it is safe for 1st–12th graders to play outdoors.
3. **Security Vulnerabilities:** Traditional web projects often expose third-party API tokens directly in browser source code, leading to key leakage and quota exhaustion.

---

## 💡 The BreatheSafe Solution

- 🗺️ **Nationwide Interactive Map:** Full-screen Leaflet visualization mapping real-time air quality across all Indian states and metropolitan zones.
- 📈 **EWMA Forecast Intelligence:** Runs a server-side Exponentially Weighted Moving Average ($\alpha = 0.35$) model to project tomorrow's AQI before school starts.
- 🚦 **CPCB Decision Protocol:** Translates complex pollutant levels into immediate **GO**, **CAUTION**, or **NO-GO** directives paired with concrete action checklists (e.g., capping outdoor PE to 20 minutes, moving assemblies indoors, mandating N95 masks).
- 📧 **Automated Principal Notifications:** Amazon EventBridge triggers automated daily morning forecasts, dispatching formatted email alerts directly to principals via Amazon SNS.
- 🔐 **Zero-Token Client Security:** Third-party API keys (`AQICN_TOKEN`) remain strictly isolated within AWS Lambda environment variables and are never transmitted to client browsers.
- 🔄 **Autonomous S3 Caching & Fallback:** Every successful upstream response is cached in Amazon S3. If upstream data providers time out, the system seamlessly serves the last known cached data marked `"cached (last known data)"`.

---

## 🏗️ System Architecture

```
                               ┌──────────────────────────────────────────────────┐
                               │             CLIENT BROWSER (AWS S3)              │
                               │    Full-screen Leaflet India Map & Drawer UI     │
                               └────────────────────────┬─────────────────────────┘
                                                        │
                                          HTTPS Request │ (Zero API tokens exposed)
                                     /forecast?station= │
                                                        ▼
                                             ┌──────────────────────┐
                                             │  Amazon API Gateway  │
                                             │  (HTTP API / CORS)   │
                                             └──────────┬───────────┘
                                                        │
┌─────────────────────────┐  Daily Cron Schedule        │ Proxy Invocation
│   Amazon EventBridge    │ ──────────────────┐         │
│  (01:00 UTC / 6:30 IST) │                   │         │
└─────────────────────────┘                   ▼         ▼
                                             ┌──────────────────────┐
                                             │      AWS Lambda      │
                                             │    (Python 3.12)     │
                                             │  - EWMA Forecasting  │
                                             │  - CPCB Decisions    │
                                             └──────────┬───────────┘
                                                        │
                                     ┌──────────────────┼──────────────────┐
                                     │                  │                  │
                                HTTPS Fetch         S3 Cache          SNS Publish
                                     ▼                  ▼                  ▼
                          ┌──────────────────┐   ┌─────────────┐    ┌─────────────┐
                          │    aqicn.org     │   │  Amazon S3  │    │ Amazon SNS  │
                          │    (WAQI API)    │   │  (Bucket)   │    │ (Principals)│
                          └──────────────────┘   └─────────────┘    └─────────────┘
```

---

## 🗂️ Project Structure

```
breathesafe_aqi_advisory/
├── README.md                 # Project overview, architecture, & AWS deployment guide
├── lambda_function.py        # AWS Lambda handler (API Gateway routing, S3 cache & EventBridge)
├── forecast.py               # EWMA forecast model + India CPCB advisory generator
├── server.py                 # Local Python HTTP dev server with /forecast Lambda emulation
├── test_local.py             # Complete offline mock test suite (9/9 pass)
├── requirements.txt          # Minimal requirements (standard library only; boto3 built into Lambda)
├── dashboard/
│   └── index.html            # Production dashboard with Leaflet map & slide-out drawer
├── docs/
│   ├── architecture.md       # Deep architectural breakdown & cost analysis (~$0.02/month)
│   └── demo-script.md        # Timed 3-minute video presentation script
└── .gitignore                # Environment, cache, and artifact exclusions
```

---

## 🚦 Decision Matrix (India CPCB Standard)

| Projected AQI | Decision Pill | Category | Health Protocol for Schools |
| :---: | :---: | :---: | :--- |
| **0 – 100** | <span style="color:#065f46;background:#ecfdf5;padding:3px 10px;border-radius:12px;font-weight:bold;">GO</span> | Good / Satisfactory | Normal outdoor physical activities, playground recess, and morning assemblies permitted. |
| **101 – 200** | <span style="color:#92400e;background:#fffbeb;padding:3px 10px;border-radius:12px;font-weight:bold;">CAUTION</span> | Moderate / Poor | Limit outdoor sports to 20 minutes maximum. Move morning assembly indoors. Students with respiratory sensitivity remain indoors. |
| **201+** | <span style="color:#991b1b;background:#fef2f2;padding:3px 10px;border-radius:12px;font-weight:bold;">NO-GO</span> | Hazardous / Severe | **Cancel all outdoor activities immediately.** Seal classroom windows, activate air purifiers, and recommend N95 masks for commuting. |

---

## 🧪 Local Testing & Offline Verification

The entire system includes an offline test suite that validates all 9 pipeline steps without requiring an AWS account or network connection:

```bash
# Run unit tests and EWMA decision scenarios
python test_local.py
```

```
=================================================================
  BreatheSafe — Offline Mock & Pipeline Test Suite
  Testing API Gateway, aqicn.org Mocks, Fallback & Decisions
=================================================================
[Test 1] API Gateway: Search Stations           -> [PASS]
[Test 2] API Gateway: Station Feed & Advisory   -> [PASS]
[Test 3] S3 Cache Fallback on API Timeout       -> [PASS]
[Test 4] CORS Preflight (OPTIONS Request)       -> [PASS]
[Test 5] Validating 5 Core EWMA Forecast Scenarios
         - Clean air week (AQI 47.8)            -> [PASS] GO
         - Moderate pollution (AQI 148.5)       -> [PASS] CAUTION
         - Hazardous smog (AQI 359.4)           -> [PASS] NO-GO
         - Sudden stubble smoke spike (AQI 216) -> [PASS] NO-GO
         - Single reading edge case (AQI 175)   -> [PASS] CAUTION
=================================================================
  RESULTS: 9/9 tests passed (0 failed)
=================================================================
```

### Running the Local Development Server

To run the dashboard locally with simulated AWS Lambda endpoints:

```bash
python server.py
# Open http://localhost:8000/ in your browser
```

---

## ☁️ AWS Cloud Services Configured

1. **Amazon S3 (`ap-south-1` Mumbai):**
   - Hosts the client dashboard with static website hosting.
   - Caches live station queries under `cache/*.json` for ultra-fast, zero-cost fallback.
2. **AWS Lambda (`breathesafe-advisory`, Python 3.12):**
   - Handles real-time station feeds, executes EWMA forecasting, and produces formatted advisories.
3. **Amazon API Gateway (HTTP API):**
   - Exposes CORS-enabled `/forecast` route with proxy integration to Lambda.
4. **Amazon SNS (`breathesafe-school-alerts`):**
   - Publishes morning advisory digests directly to school principals via email/SMS.
5. **Amazon EventBridge (`breathesafe-morning-advisory`):**
   - Scheduled daily cron rule (`cron(0 1 * * ? *)`) executing daily morning air evaluations.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).  
Built for the **Bharat Builds Tour: Environmental Hacks** (Track 1 — Air).
