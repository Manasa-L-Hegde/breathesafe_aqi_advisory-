# Event Day Execution Checklist — BreatheSafe

> **IMPORTANT:** Do NOT begin any of the items below before the hackathon clock officially starts!  
> This file lists **only** the actions reserved for the event window.

---

## ⏰ Phase 1: Git Repository Initialization & First Commit

- [ ] Run `git init` in the project root directory.
- [ ] Verify `.gitignore` ignores `__pycache__`, `.env`, and OS artifacts.
- [ ] Stage all verified local files:
  ```bash
  git add .
  ```
- [ ] Create initial commit:
  ```bash
  git commit -m "feat: initial commit of BreatheSafe school AQI advisory system"
  ```
- [ ] Create GitHub repository under event guidelines (e.g., `breathesafe-schools`).
- [ ] Add remote and push:
  ```bash
  git remote add origin https://github.com/YOUR_USERNAME/breathesafe-schools.git
  git branch -M main
  git push -u origin main
  ```

---

## ☁️ Phase 2: Live AWS Cloud Deployment (Exact Console Order)

- [ ] **Step 1 — Amazon S3:**
  - Create S3 bucket: `breathesafe-data-YOURNAME` (region: `ap-south-1` Mumbai).
  - Enable Static Website Hosting (or keep private if running dashboard locally).
  - Upload `dashboard/index.html`.
- [ ] **Step 2 — AWS Lambda:**
  - Create function: `breathesafe-advisory` (Python 3.12, timeout: 10s).
  - Deploy `lambda_function.py` and `forecast.py`.
  - Configure environment variables:
    - `AQICN_TOKEN` (from [aqicn.org/data-platform/token/](https://aqicn.org/data-platform/token/))
    - `S3_BUCKET` (`breathesafe-data-YOURNAME`)
    - `SCHOOL_NAME` (`School Campus`)
    - `AQI_CITY` (`delhi`)
- [ ] **Step 3 — IAM Execution Role:**
  - Attach S3 permissions (`s3:PutObject`, `s3:GetObject`).
  - Attach SNS permissions (`sns:Publish`).
- [ ] **Step 4 — Amazon SNS:**
  - Create Standard Topic: `breathesafe-school-alerts`.
  - Create Email Subscription with target school principal email.
  - Confirm subscription via verification link sent to email inbox.
  - Copy Topic ARN into Lambda's `SNS_TOPIC_ARN` environment variable.
- [ ] **Step 5 — Amazon EventBridge:**
  - Create Schedule Rule: `breathesafe-morning-advisory` (`cron(0 1 * * ? *)`).
  - Set Target to `breathesafe-advisory` Lambda function.
- [ ] **Step 6 — Amazon API Gateway:**
  - Create HTTP API: `breathesafe-api`.
  - Add Lambda proxy integration to `breathesafe-advisory`.
  - Configure CORS (`*`, `GET, OPTIONS`).
  - Copy Invoke URL into `dashboard/index.html` (via gear icon settings).

---

## 🧪 Phase 3: Live Verification & Testing

- [ ] Run `python test_local.py` (confirm 9/9 tests pass).
- [ ] Test Lambda function via AWS Console test event.
- [ ] Confirm SNS alert email arrives in inbox with formatted advisory.
- [ ] Confirm live search and station feed return through API Gateway.

---

## 🎥 Phase 4: Video Recording & Final Submission

- [ ] **Record 3-Minute Demo Video:**
  - Follow [`docs/demo-script.md`](file:///c:/Users/manas/OneDrive/Documents/Projects/BreatheSafe%20%E2%80%94%20School%20AQI%20Advisory%20System/docs/demo-script.md) timing:
    - 0:00 – 0:30: The Problem
    - 0:30 – 2:00: Live Demo (Delhi NO-GO, Mumbai GO, Lucknow CAUTION, SNS alert simulation)
    - 2:00 – 2:30: AWS Architecture & 5 services named
    - 2:30 – 3:00: Impact & Closing
  - Upload video to YouTube (unlisted) or Loom / Google Drive.
- [ ] **Write Submission Writeup:**
  - Project Title: **BreatheSafe — School AQI Advisory System**
  - Track: **Track 1 — Air (Environmental Hacks)**
  - Architecture Summary from [`docs/architecture.md`](file:///c:/Users/manas/OneDrive/Documents/Projects/BreatheSafe%20%E2%80%94%20School%20AQI%20Advisory%20System/docs/architecture.md)
  - GitHub Repo Link
  - Demo Video Link
  - Live Demo / Dashboard Link
