# BreatheSafe — School AQI Advisory System (India)

> AWS-powered real-time AQI forecasting and alert system covering schools across all Indian states. Provides an interactive map and automatic **GO / CAUTION / NO-GO** advisories for outdoor student activities.
> Built for **Bharat Builds Tour: Environmental Hacks (Track 1 — Air)**.

---

## The Problem

During peak pollution months, millions of school children across Indian cities (Delhi NCR, Mumbai, Kolkata, Lucknow, Patna, Ludhiana, etc.) breathe hazardous air during morning assembly, PE, and outdoor recess. School administrators often rely on guesswork or discover hazardous air spikes too late.

**BreatheSafe** bridges this gap:
- Interactive Leaflet map displaying real-time AQI across stations in all Indian states.
- Server-side forecast engine (Exponentially Weighted Moving Average) projecting tomorrow's air quality.
- Unambiguous **GO / CAUTION / NO-GO** badges with tailored school action plans.
- Daily automated email alerts dispatched directly to school principals via Amazon SNS.
- **Enterprise-grade security:** Third-party AQI API tokens remain isolated inside AWS Lambda and are never exposed to client browsers.
- **Resilient S3 caching:** Automatically falls back to last known cached data if external APIs experience downtime.

---

## System Architecture

```
                              ┌──────────────────────────────────────────────┐
                              │            CLIENT BROWSER (S3)               │
                              │  Full-screen Leaflet India Map + Side Drawer │
                              └──────────────────────┬───────────────────────┘
                                                     │
                                       HTTPS Request │ (No tokens in browser)
                                 ?action=search/feed │
                                                     ▼
                                          ┌──────────────────────┐
                                          │  Amazon API Gateway  │
                                          └──────────┬───────────┘
                                                     │
┌─────────────────────────┐  Daily Cron Schedule     │ Proxy Invocation
│   Amazon EventBridge    │ ─────────────────┐       │
└─────────────────────────┘                  ▼       ▼
                                          ┌──────────────────────┐
                                          │      AWS Lambda      │
                                          │     (Python 3.12)    │
                                          └──────────┬───────────┘
                                                     │
                                  ┌──────────────────┼──────────────────┐
                                  │                  │                  │
                             HTTPS Fetch         S3 Cache          SNS Publish
                                  ▼                  ▼                  ▼
                       ┌──────────────────┐   ┌─────────────┐    ┌─────────────┐
                       │    aqicn.org     │   │  Amazon S3  │    │ Amazon SNS  │
                       │   (Live API)     │   │ (Cache &    │    │ (Principal  │
                       │                  │   │  Dashboard) │    │   Alerts)   │
                       └──────────────────┘   └─────────────┘    └─────────────┘
```

---

## Project Structure

```
breathesafe-schools/
├── README.md                 ← Project documentation & AWS Console deployment guide
├── lambda_function.py        ← AWS Lambda handler (API Gateway routing + EventBridge)
├── forecast.py               ← EWMA forecast engine + CPCB-aligned decision logic
├── test_local.py             ← Comprehensive offline mock & regression test suite (9/9 pass)
├── requirements.txt          ← Empty (standard library only; boto3 built into Lambda)
├── dashboard/
│   └── index.html            ← Full-screen Leaflet India map & slide-in advisory drawer
├── docs/
│   ├── architecture.md       ← In-depth architectural data flow & cost breakdown (~$0.02/mo)
│   └── demo-script.md        ← Timed 3-minute video presentation script
└── .gitignore
```

---

## Quick Start (Offline Local Testing)

No AWS account, API tokens, or internet connection required to test locally.

```bash
# 1. Run the offline test suite (mocks API Gateway, aqicn payloads, & S3 caching)
python test_local.py
```

Expected output:
```
=================================================================
  BreatheSafe — Offline Mock & Pipeline Test Suite
  Testing API Gateway, aqicn.org Mocks, Fallback & Decisions
=================================================================
[Test 1] API Gateway: Search Stations -> PASS (Found 3 mock stations)
[Test 2] API Gateway: Station Feed & Advisory -> PASS (Advisory generated)
[Test 3] S3 Cache Fallback on API Timeout -> PASS (Recovered last known data)
[Test 4] CORS Preflight (OPTIONS Request) -> PASS
[Test 5] Validating 5 Core EWMA Forecast Scenarios -> PASS
=================================================================
  RESULTS: 9/9 tests passed (0 failed)
=================================================================
```

### Dashboard Preview & Rehearsal Modes

- **Offline Mock Mode (Default for Rehearsals):**
  Open `dashboard/index.html` in any web browser or with `?mock=true`. Runs 100% offline with zero live AWS or network dependencies. Pre-loaded with stations across all Indian regions (Delhi, Maharashtra, Karnataka, Uttar Pradesh, Punjab, West Bengal, etc.), interactive search, EWMA forecasts, CPCB decision pills, and a "Simulate Principal Alert (Amazon SNS)" button.
- **Live AWS Mode:**
  Click the gear icon in the dashboard header, toggle Mock Mode OFF, and enter your Amazon API Gateway HTTP API Invoke URL. The dashboard routes requests securely through AWS API Gateway to AWS Lambda.

---

## AWS Setup Guide (Event Day Deployment)

Follow these steps in exact order on event day:

### Step 1: Configure Amazon S3 (Caching & Web Hosting)
1. In the **AWS S3 Console**, click **Create bucket** (e.g., `breathesafe-data-YOURNAME`).
2. Region: Choose `ap-south-1` (Mumbai) or your target AWS region.
3. Uncheck *Block all public access* if hosting the dashboard as a public static website, or keep it private if accessing locally.
4. Enable **Static website hosting** under Bucket Properties (Index document: `index.html`).
5. Upload `dashboard/index.html` to the bucket root (or run locally).
6. Note your S3 Bucket Name for Step 2.

### Step 2: Create AWS Lambda Function
1. In the **AWS Lambda Console**, click **Create function** → **Author from scratch**.
2. **Function name:** `breathesafe-advisory`
3. **Runtime:** `Python 3.12` (x86_64 or arm64).
4. Under Code Source:
   - Paste the contents of `lambda_function.py` into the editor.
   - Click **File → New File**, name it `forecast.py`, and paste the contents of `forecast.py`.
   - Click **Deploy**.
5. Under **Configuration → General configuration**:
   - Set **Timeout** to `10 seconds`.
6. Under **Configuration → Environment variables**, add:
   - `AQICN_TOKEN`: Your free API key from [aqicn.org/data-platform/token/](https://aqicn.org/data-platform/token/) (kept secret on AWS; never sent to browser).
   - `S3_BUCKET`: Your S3 bucket name from Step 1.
   - `SNS_TOPIC_ARN`: Left blank for now (will populate in Step 4).
   - `SCHOOL_NAME`: `School Campus` (or school institution name).
   - `AQI_CITY`: `delhi` (default city for daily morning alert).

### Step 3: Configure IAM Permissions
1. Under Lambda function **Configuration → Permissions**, click the **Execution role** name link to open IAM.
2. In IAM, click **Add permissions** → **Attach policies** (or **Create inline policy**):
   - **AmazonS3FullAccess** (or scoped inline policy granting `s3:GetObject` and `s3:PutObject` on `arn:aws:s3:::YOUR_BUCKET/*`).
   - **AmazonSNSFullAccess** (or scoped inline policy granting `sns:Publish` on `arn:aws:sns:*:*:breathesafe-school-alerts`).
3. Click **Save / Attach policy**. Lambda now has permissions to read/write the S3 cache and publish SNS alerts.

### Step 4: Set Up Amazon SNS (Principal Alerts)
1. Go to **Amazon SNS** → **Topics** → **Create topic**.
2. Type: **Standard**.
3. Name: `breathesafe-school-alerts`
4. Click **Create topic** and copy the **Topic ARN** (e.g., `arn:aws:sns:ap-south-1:123456789012:breathesafe-school-alerts`).
5. Click **Create subscription**:
   - Protocol: `Email`
   - Endpoint: Enter the school principal's email address.
   - Click **Create subscription**.
6. Check the principal's inbox and click the **Confirm subscription** verification link.
7. Return to the Lambda function **Configuration → Environment variables**, edit `SNS_TOPIC_ARN`, and paste the copied Topic ARN. Click **Save**.

### Step 5: Configure Amazon EventBridge (Scheduled Morning Cron)
1. Go to **Amazon EventBridge** → **Rules** → **Create rule**.
2. Name: `breathesafe-morning-advisory`
3. Rule type: **Schedule**.
4. Define schedule:
   - Cron expression: `cron(0 1 * * ? *)` (fires at 01:00 UTC = 6:30 AM IST every morning).
5. Select Target:
   - Target type: **AWS service** → **Lambda function**.
   - Function: `breathesafe-advisory`.
6. Click **Next** through review and click **Create rule**.

### Step 6: Create Amazon API Gateway (HTTP API & CORS)
1. Go to **Amazon API Gateway** → **Create API** → Find **HTTP API** → Click **Build**.
2. API Name: `breathesafe-api`
3. Click **Add integration** → Choose **Lambda** → Select `breathesafe-advisory`.
4. Configure routes:
   - Method: `ANY` (or `GET`), Resource path: `/{proxy+}` or `/`.
5. Under API Settings → **CORS**:
   - Access-Control-Allow-Origin: `*`
   - Access-Control-Allow-Methods: `GET, OPTIONS`
   - Access-Control-Allow-Headers: `*`
6. Copy the **Invoke URL** (e.g., `https://xyz123.execute-api.ap-south-1.amazonaws.com`).
7. In `dashboard/index.html`, click the gear icon in the top header, disable Mock Mode, and paste your Invoke URL. Click **Save URL**.

---

## Decision Thresholds (India CPCB Standard)

| Forecast AQI | Decision Pill | Health Implication | School Protocol |
| :---: | :---: | :--- | :--- |
| **0 – 100** | <span style="color:#065f46;background:#ecfdf5;padding:2px 8px;border-radius:12px;font-weight:bold;">GO</span> | Good / Satisfactory | Normal outdoor recess, morning assembly, and sports training. |
| **101 – 200** | <span style="color:#92400e;background:#fffbeb;padding:2px 8px;border-radius:12px;font-weight:bold;">CAUTION</span> | Moderate to Poor | Cap outdoor sessions at 20 mins; sensitive/asthmatic students indoors; keep classroom windows shut during peak hours. |
| **201+** | <span style="color:#991b1b;background:#fef2f2;padding:2px 8px;border-radius:12px;font-weight:bold;">NO-GO</span> | Hazardous / Severe | **Cancel all outdoor activities.** Keep classrooms sealed with purifiers active. Advise N95 masks for commute. |

---

## License

Built under MIT License for **Bharat Builds Tour: Environmental Hacks** (Track 1 — Air).
