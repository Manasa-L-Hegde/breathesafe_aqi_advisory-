"""
forecast.py — BreatheSafe Forecast & Decision Engine

WHY THIS FILE EXISTS:
    lambda_function.py (our AWS Lambda handler) imports this file to compute
    advisories for any Indian station requested via API Gateway or EventBridge.
    Keeping logic pure Python (standard library only) guarantees immediate
    compatibility in AWS Lambda without layers or build steps.

DECISION THRESHOLDS (based on India's National AQI / CPCB breakpoints):
    AQI 0–100    → GO        (Good / Satisfactory — outdoor activities proceed)
    AQI 101–200  → CAUTION   (Moderate / Poor — limit prolonged outdoor exertion)
    AQI 201+     → NO-GO     (Very Poor / Severe / Hazardous — strictly indoors)
"""

from datetime import datetime, timezone
import math
import sys

# Exponential smoothing factor for EWMA (recent values carry higher weight)
ALPHA = 0.6

# Indian National AQI Breakpoints
THRESHOLD_GO = 100       # Up to 100 is Satisfactory/Good
THRESHOLD_CAUTION = 200  # Up to 200 is Moderate; above is Poor/Very Poor/Severe


def compute_forecast(readings):
    """
    Compute forecasted AQI value using Exponentially Weighted Moving Average (EWMA).
    Order: oldest first -> newest last.
    """
    if not readings:
        raise ValueError("Need at least one AQI reading to compute forecast.")

    valid_readings = [float(r) for r in readings if r is not None and not math.isnan(float(r))]
    if not valid_readings:
        return 100.0

    if len(valid_readings) == 1:
        return round(valid_readings[0], 1)

    n = len(valid_readings)
    weights = [ALPHA ** i for i in range(n)]
    weights.reverse()  # Newest reading receives highest weight

    weighted_sum = sum(r * w for r, w in zip(valid_readings, weights))
    total_weight = sum(weights)
    return round(weighted_sum / total_weight, 1)


def get_aqi_category(aqi_val):
    """Return official Indian National AQI category and color code."""
    try:
        val = round(float(aqi_val))
    except (ValueError, TypeError):
        val = 0

    if val <= 50:
        return {"category": "Good", "color": "#10b981", "badge_class": "aqi-good"}
    elif val <= 100:
        return {"category": "Satisfactory", "color": "#22c55e", "badge_class": "aqi-satisfactory"}
    elif val <= 200:
        return {"category": "Moderate", "color": "#eab308", "badge_class": "aqi-moderate"}
    elif val <= 300:
        return {"category": "Poor", "color": "#f97316", "badge_class": "aqi-poor"}
    elif val <= 400:
        return {"category": "Very Poor", "color": "#ef4444", "badge_class": "aqi-very-poor"}
    else:
        return {"category": "Severe", "color": "#881337", "badge_class": "aqi-severe"}


def decide(forecast_aqi):
    """
    Turn a forecasted AQI value into a clear school advisory.
    Returns decision, color, summary, and action items.
    """
    aqi = round(float(forecast_aqi))

    if aqi <= THRESHOLD_GO:
        return {
            "decision": "GO",
            "color": "green",
            "badge_color": "#10b981",
            "summary": f"Air quality expected to be Good/Satisfactory (AQI ≈ {aqi}). Outdoor school activities safe to proceed.",
            "actions": [
                "Morning outdoor assembly may proceed normally.",
                "Standard sports, PE, and outdoor recess permitted.",
                "Normal classroom ventilation and window opening allowed.",
                "No health restrictions for students."
            ]
        }
    elif aqi <= THRESHOLD_CAUTION:
        return {
            "decision": "CAUTION",
            "color": "amber",
            "badge_color": "#f59e0b",
            "summary": f"Air quality expected to be Moderate-to-Poor (AQI ≈ {aqi}). Limit prolonged outdoor exertion.",
            "actions": [
                "Cap outdoor PE and running sessions to 20 minutes maximum.",
                "Consider holding morning assembly inside an auditorium or classrooms.",
                "Students with asthma or sensitive respiratory conditions must stay indoors.",
                "Keep windows closed during peak traffic hours; monitor classroom ventilation."
            ]
        }
    else:
        return {
            "decision": "NO-GO",
            "color": "red",
            "badge_color": "#ef4444",
            "summary": f"Air quality expected to be Hazardous / Severe (AQI ≈ {aqi}). All outdoor school activities must be cancelled.",
            "actions": [
                "CANCEL all outdoor sports, morning assembly, and outdoor recess.",
                "Keep all classroom windows and external doors closed.",
                "Run classroom air purifiers if school is equipped.",
                "Issue advisory notification to parents regarding elevated pollution levels.",
                "Advise N95 masks for children during travel to and from school."
            ]
        }


def generate_advisory(readings, school_name="School Campus", city="Delhi", station_info=None, is_cached=False, data_source="live"):
    """
    End-to-end pipeline:
    Calculates forecast, evaluates decision, and creates a full JSON payload.
    Supports station metadata, coordinates, daily forecast breakdown, and cache indication.
    """
    if not readings:
        readings = [120]

    forecast_aqi = compute_forecast(readings)
    decision_info = decide(forecast_aqi)
    current_aqi = readings[-1] if readings else forecast_aqi
    cat_info = get_aqi_category(current_aqi)

    station_info = station_info or {}
    now_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return {
        "school": school_name,
        "city": city,
        "station_name": station_info.get("name", city),
        "station_id": station_info.get("id"),
        "coordinates": station_info.get("geo", []),
        "generated_at": now_utc,
        "is_cached": is_cached,
        "data_source": data_source,
        "current_aqi": current_aqi,
        "current_category": cat_info["category"],
        "category_color": cat_info["color"],
        "forecast_aqi": forecast_aqi,
        "readings_history": readings,
        "daily_forecast": station_info.get("daily_forecast", []),
        "dominant_pollutant": station_info.get("dominentpol", "pm25"),
        "decision": decision_info["decision"],
        "color": decision_info["color"],
        "badge_color": decision_info["badge_color"],
        "summary": decision_info["summary"],
        "actions": decision_info["actions"],
    }


def format_advisory_text(adv):
    """Format human-readable alert message for SNS email/SMS distribution."""
    cache_note = " [CACHED / LAST KNOWN DATA]" if adv.get("is_cached") else ""
    lines = [
        "=== BreatheSafe School Advisory ===",
        f"Station : {adv.get('station_name', adv.get('city'))}",
        f"Region  : {adv.get('city')}",
        f"Time    : {adv.get('generated_at')}{cache_note}",
        "",
        f"Current AQI    : {adv['current_aqi']} ({adv.get('current_category', '')})",
        f"Forecasted AQI : {adv['forecast_aqi']}",
        f"Advisory       : {adv['decision']}",
        "",
        f"Summary: {adv['summary']}",
        "",
        "Recommended School Actions:"
    ]
    for i, action in enumerate(adv["actions"], 1):
        lines.append(f"  {i}. {action}")
    lines.append("===================================")
    return "\n".join(lines)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass
    print("\n" + "=" * 65)
    print("  BreatheSafe — School AQI Advisory & Forecast Engine Demo")
    print("=" * 65 + "\n")

    demo_scenarios = [
        {
            "school": "Delhi Public School, R.K. Puram",
            "city": "New Delhi",
            "station": {"name": "Anand Vihar, Delhi", "id": 8675, "geo": [28.6469, 77.3160]},
            "readings": [220, 260, 310, 340, 380, 395],
        },
        {
            "school": "The Cathedral & John Connon School",
            "city": "Mumbai",
            "station": {"name": "Colaba, Mumbai", "id": 8344, "geo": [18.9067, 72.8147]},
            "readings": [115, 125, 140, 130, 145, 150],
        },
        {
            "school": "National Public School, Indiranagar",
            "city": "Bengaluru",
            "station": {"name": "BTM Layout, Bengaluru", "id": 8123, "geo": [12.9165, 77.6101]},
            "readings": [45, 52, 48, 55, 42, 49],
        },
    ]

    for scenario in demo_scenarios:
        advisory = generate_advisory(
            readings=scenario["readings"],
            school_name=scenario["school"],
            city=scenario["city"],
            station_info=scenario["station"],
        )
        print(f"School   : {advisory['school']}")
        print(f"Readings : {scenario['readings']}")
        print(f"Forecast : EWMA AQI = {advisory['forecast_aqi']} ({advisory['current_category']})")
        print(f"Decision : [{advisory['decision']}] (Color: {advisory['color'].upper()})\n")
        print(format_advisory_text(advisory))
        print("\n" + "-" * 65 + "\n")

