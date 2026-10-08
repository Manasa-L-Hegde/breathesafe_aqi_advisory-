# Demo Script — BreatheSafe (Timed 3-Minute Video)

> **Format:** 3-Minute Video Presentation (Screen share with voiceover).  
> **Target Track:** Bharat Builds Tour: Environmental Hacks (Track 1 — Air).  
> **Rehearsal Mode:** Open `http://localhost:8000/?mock=true` for 100% offline rehearsal.

---

## ⏱️ [0:00 – 0:30] The Problem (First 30 Seconds)

**Visual:** Start on BreatheSafe dashboard or news headline showing winter smog over Indian schools.

**Voiceover:**
> *"Every winter across India — from Delhi and Lucknow to Ludhiana and Patna — millions of school children step outside for morning assembly, PE, and recess, breathing air that is 10 to 20 times above WHO safe limits.*
>
> *The tragedy isn't just the pollution — it's the lack of proactive information. School principals and teachers are forced to rely on guesswork or discover hazardous air spikes hours after children have already been exposed.*
>
> *Schools don't need complex raw sensor charts — they need a simple, proactive decision: Should our kids be outside tomorrow morning, or not?*
>
> *That is why we built **BreatheSafe**."*

---

## ⏱️ [0:30 – 2:00] The Live Demo (Middle 90 Seconds)

### Part 1: Interactive Map & Search (0:30 – 0:55)
**Visual:** BreatheSafe full-screen map centered over India.  
**Action:** Type `"Delhi"` into the search bar, select **Anand Vihar, Delhi**. The map smoothly pans and the side panel slides in.

**Voiceover:**
> *"Here is the BreatheSafe live dashboard. We have station monitoring covering all major Indian regions.*
>
> *Let's search for Anand Vihar in East Delhi. Instantly, the side drawer opens. The current AQI is severe — 245. But notice: BreatheSafe doesn't just display historical readings. Our forecast engine computes tomorrow's projected AQI and provides an unambiguous decision badge:*
>
> ***NO-GO.** A bold red pill with a clear school action checklist: cancel morning assembly, move PE indoors, seal classroom doors, run purifiers, and advise N95 masks for student commute."*

### Part 2: Demonstrating GO & CAUTION Across Regions (0:55 – 1:25)
**Visual:** Click the **Maharashtra** quick-filter chip, select **Colaba, Mumbai**. Then click **Uttar Pradesh**, select **Talkatora, Lucknow**.

**Voiceover:**
> *"Now let's switch regions. Clicking Maharashtra brings us to Colaba, Mumbai. Here, the forecast AQI is 92:*
>
> ***GO.** A vibrant green badge. Outdoor morning assembly and sports activities can proceed safely without health restrictions.*
>
> *Clicking on Lucknow shows **CAUTION** — Moderate-to-Poor air. The advisory instructs teachers to cap outdoor running to 20 minutes and keep asthmatic students indoors.*
>
> *The forecast uses Exponentially Weighted Moving Average (EWMA), placing higher mathematical weight on recent air trajectories to predict tomorrow's morning peak before school gates open."*

### Part 3: Automated Alert Firing via Amazon SNS (1:25 – 2:00)
**Visual:** In the side panel, click **Simulate Principal Alert (Amazon SNS)**.  
**Action:** The `#sns-toast` notification animates onto the screen displaying the formatted advisory message.

**Voiceover:**
> *"Principals shouldn't have to check a website every morning. BreatheSafe runs automatically.*
>
> *[Clicks 'Simulate Principal Alert'] Watch this: at 6:30 AM every day, an automated alert fires directly to the principal's inbox via Amazon SNS.*
>
> *The message contains the exact school action plan — clear, concise, and actionable before the morning buses leave."*

---

## ⏱️ [2:00 – 2:30] AWS Architecture & Services Used (Last 30 Seconds)

**Visual:** Switch to the AWS Architecture diagram slide or README architecture section.

**Voiceover:**
> *"Under the hood, BreatheSafe is built on 5 serverless AWS services:*
>
> 1. ***Amazon API Gateway*** — routes dashboard queries while keeping third-party API tokens 100% confidential.
> 2. ***AWS Lambda*** — runs our pure Python EWMA forecast and CPCB decision engine with zero external dependencies.
> 3. ***Amazon S3*** — hosts the static dashboard and caches live station payloads, providing seamless fallback if upstream APIs go down.
> 4. ***Amazon SNS*** — dispatches daily morning alerts directly to school principals.
> 5. ***Amazon EventBridge*** — schedules the automated daily cron evaluation at 6:30 AM IST.
>
> *The entire system is serverless, auto-scaling, and costs less than two rupees per month to protect an entire school campus."*

---

## ⏱️ [2:30 – 3:00] Impact & Conclusion (Closing Buffer)

**Visual:** Back to the BreatheSafe live map with all-India station markers active.

**Voiceover:**
> *"Every child has the right to breathe clean air — and every school administrator deserves the clarity to protect them.*
>
> *BreatheSafe transforms raw pollution data into life-saving school protocols.*
>
> *Thank you."*

---

## 📋 Recording Checklist & Rehearsal Tips

| Item | Recommendation |
| :--- | :--- |
| **URL for Rehearsal** | `http://localhost:8000/?mock=true` (zero network latency, guarantees 100% reliable demo) |
| **Screen Resolution** | 1920 × 1080 (1080p), browser zoom set to 100% or 90% |
| **Demo Cities** | **Delhi** (NO-GO, Red) → **Mumbai** (GO, Green) → **Lucknow** (CAUTION, Amber) |
| **Alert Action** | Click **"Simulate Principal Alert (Amazon SNS)"** button in the side drawer |
| **Target Timing** | Rehearse to complete by 2:45 to leave comfortable breathing room under the 3-minute cap |
