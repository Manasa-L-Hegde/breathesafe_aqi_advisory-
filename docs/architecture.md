# Architecture — BreatheSafe 2.0 (Nationwide Air Quality Advisory)

## System Overview

BreatheSafe 2.0 is a serverless, dual-mode air quality intelligence system tailored for schools across India. It operates under two distinct AWS invocation patterns:

1. **Interactive Real-Time Mode (API Gateway → Lambda):**
   - Teachers, parents, and principals query any Indian city or state in real time.
   - The browser **NEVER** communicates directly with third-party AQI APIs, ensuring the `AQICN_TOKEN` remains strictly confidential on AWS.
   - Every live station response is cached to Amazon S3. If the upstream provider experiences network latency or downtime, Lambda transparently serves the cached payload marked **"cached (last known data)"**.

2. **Daily Scheduled Alert Mode (EventBridge → Lambda → SNS):**
   - Every morning, an EventBridge cron rule invokes Lambda to evaluate baseline air quality.
   - Dispatches automated plain-text school advisories to principals via Amazon SNS (email/SMS).
   - Updates `latest-advisory.json` on S3 for static dashboard feeds.

---

## Data Flow Diagram

```
                              ┌────────────────────────────────────────────────────────┐
                              │                    CLIENT BROWSER                      │
                              │  Full-screen Leaflet Map of India + Slide-in Drawer    │
                              └──────────────────────────┬─────────────────────────────┘
                                                         │
                                           HTTPS Query   │  (No API keys exposed in client)
                                     ?action=search/feed │
                                                         ▼
                                              ┌─────────────────────┐
                                              │ Amazon API Gateway  │
                                              │ (HTTP / REST API)   │
                                              └──────────┬──────────┘
                                                         │
┌─────────────────────────┐   EventBridge Cron           │  Proxy Invocation
│  Amazon EventBridge     │ ──────────────────────┐      │
│  (Scheduled Daily Rule) │                       │      │
└─────────────────────────┘                       ▼      ▼
                                              ┌─────────────────────┐
                                              │   AWS Lambda        │
                                              │  (Python 3.12)      │
                                              └──────────┬──────────┘
                                                         │
                                      ┌──────────────────┼──────────────────┐
                                      │                  │                  │
                                 HTTPS Fetch        Read / Write       SNS Publish
                                      ▼                  ▼                  ▼
                           ┌──────────────────┐   ┌─────────────┐    ┌─────────────┐
                           │   aqicn.org      │   │  Amazon S3  │    │ Amazon SNS  │
                           │  (WAQI Live API) │   │ (Cache &    │    │ (School     │
                           │                  │   │  Dashboard) │    │  Principals)│
                           └──────────────────┘   └─────────────┘    └─────────────┘
```

---

## Component Breakdown

### 1. Amazon API Gateway
- **Type:** HTTP API (recommended for low latency and minimal cost) or REST API.
- **Route:** `GET /` with Proxy Integration to the `breathesafe-advisory` Lambda function.
- **CORS:** Enabled (`Access-Control-Allow-Origin: *`, `GET`, `OPTIONS`).
- **Security:** Hides `AQICN_TOKEN` entirely from the client.

### 2. AWS Lambda (`lambda_function.py` + `forecast.py`)
- **Runtime:** Python 3.12 (standard library only; boto3 pre-installed).
- **Environment Variables:**
  - `AQICN_TOKEN`: Token obtained from [aqicn.org/data-platform/token/](https://aqicn.org/data-platform/token/).
  - `S3_BUCKET`: Target S3 bucket used for live cache writes and fallbacks.
  - `SNS_TOPIC_ARN`: ARN for dispatching scheduled school alerts.
  - `SCHOOL_NAME`: Default school campus label.
  - `AQI_CITY`: Default city for scheduled daily alerts (e.g. `delhi`).
- **Endpoints Handled:**
  - `?action=search&keyword={city}`: Searches WAQI for station coordinates and current AQI values across India.
  - `?action=feed&station={id_or_city}`: Retrieves station feed, extracts daily forecast, computes EWMA forecast, and decides **GO / CAUTION / NO-GO**.
  - EventBridge scheduled event: Daily morning evaluation and SNS alert dispatch.

### 3. S3 Caching & Offline Fallback Strategy
- Successful live station queries are automatically serialized and saved to S3 under `cache/feed_{station}.json` and `cache/search_{keyword}.json`.
- When an external API timeout or HTTP error occurs:
  1. Lambda inspects S3 for the matching cache key.
  2. If located, returns the cached advisory payload with `is_cached: true` and `data_source: "cached (last known data)"`.
  3. The frontend prominently surfaces this status via a warning banner so school administrators are informed.

### 4. Interactive Map Dashboard (`dashboard/index.html`)
- **Architecture:** Zero-build static HTML/CSS/JS. Can be hosted on S3 Static Website Hosting or opened locally.
- **Map Engine:** Leaflet.js with Carto Positron / OpenStreetMap light tiles.
- **Color Coding:** Standardized to India's National Air Quality Index (NAQI) breakpoints (CPCB):
  - 0–50: Good (`#10b981`)
  - 51–100: Satisfactory (`#22c55e`)
  - 101–200: Moderate (`#eab308`)
  - 201–300: Poor (`#f97316`)
  - 301–400: Very Poor (`#ef4444`)
  - 401+: Severe (`#881337`)
- **Decision Engine:**
  - **GO (Green Pill):** AQI ≤ 100 — Assembly, outdoor PE, and recess safe.
  - **CAUTION (Amber Pill):** AQI 101–200 — Max 20 min PE, sensitive students indoors.
  - **NO-GO (Red Pill):** AQI > 200 — Strictly cancel all outdoor sports, assembly, and recess.

---

## AWS Monthly Cost Estimate

| Service | Tier / Monthly Volume | Estimated Cost |
| :--- | :--- | :--- |
| **AWS Lambda** | ~10,000 queries + 30 daily crons | $0.00 (within 1M free requests/mo) |
| **API Gateway** | ~10,000 HTTP API requests | $0.01 (within 1M free tier for 12 mos) |
| **Amazon S3** | Cache files & static dashboard hosting (<10 MB) | $0.01 |
| **Amazon SNS** | 30 daily email alerts | $0.00 |
| **Total** | | **~$0.02 / month** |
