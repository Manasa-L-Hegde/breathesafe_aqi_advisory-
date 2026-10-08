"""
test_local.py — Offline Test Suite for BreatheSafe

WHY THIS FILE EXISTS:
    Tests the entire serverless pipeline completely offline:
    1. Mocks real aqicn.org (WAQI) search & feed JSON payloads.
    2. Tests API Gateway event routing (search, feed, national overview, CORS).
    3. Tests S3 caching fallback when the external API times out or fails.
    4. Validates the 5 core EWMA forecast and GO / CAUTION / NO-GO decision scenarios.

Run anytime with:
    python test_local.py
No internet connection, API keys, or AWS account required.
"""

import json
import io
import unittest
from unittest.mock import patch, MagicMock

# Import the Lambda handler and core decision engine
import lambda_function
from forecast import generate_advisory, compute_forecast, decide, format_advisory_text

# ── Mock WAQI API Payloads ──────────────────────────────────────────────────
MOCK_SEARCH_RESPONSE = {
    "status": "ok",
    "data": [
        {
            "uid": 8675,
            "aqi": "185",
            "time": {"stime": "2026-09-29 18:00:00", "tz": "+05:30"},
            "station": {
                "name": "Anand Vihar, Delhi, India",
                "geo": [28.6469, 77.3160],
                "url": "delhi/anand-vihar",
            }
        },
        {
            "uid": 8680,
            "aqi": "245",
            "time": {"stime": "2026-09-29 18:00:00", "tz": "+05:30"},
            "station": {
                "name": "Punjabi Bagh, Delhi, India",
                "geo": [28.6720, 77.1310],
                "url": "delhi/punjabi-bagh",
            }
        },
        {
            "uid": 8685,
            "aqi": "85",
            "time": {"stime": "2026-09-29 18:00:00", "tz": "+05:30"},
            "station": {
                "name": "Nehru Nagar, Delhi, India",
                "geo": [28.5678, 77.2505],
                "url": "delhi/nehru-nagar",
            }
        }
    ]
}

MOCK_FEED_RESPONSE_DELHI = {
    "status": "ok",
    "data": {
        "aqi": 185,
        "idx": 8675,
        "city": {
            "name": "Anand Vihar, Delhi, India",
            "geo": [28.6469, 77.3160],
            "url": "https://aqicn.org/city/delhi/anand-vihar"
        },
        "dominentpol": "pm25",
        "time": {
            "s": "2026-09-29 18:00:00",
            "tz": "+05:30",
            "v": 1727632800
        },
        "forecast": {
            "daily": {
                "pm25": [
                    {"avg": 165, "day": "2026-09-27", "max": 195, "min": 130},
                    {"avg": 175, "day": "2026-09-28", "max": 210, "min": 140},
                    {"avg": 185, "day": "2026-09-29", "max": 225, "min": 150},
                    {"avg": 210, "day": "2026-09-30", "max": 250, "min": 165}
                ]
            }
        }
    }
}

MOCK_FEED_RESPONSE_CLEAN = {
    "status": "ok",
    "data": {
        "aqi": 48,
        "idx": 8121,
        "city": {
            "name": "BTM Layout, Bengaluru, India",
            "geo": [12.9166, 77.6101]
        },
        "dominentpol": "pm25",
        "forecast": {
            "daily": {
                "pm25": [
                    {"avg": 42, "day": "2026-09-28", "max": 55, "min": 30},
                    {"avg": 46, "day": "2026-09-29", "max": 60, "min": 35},
                    {"avg": 48, "day": "2026-09-30", "max": 65, "min": 38}
                ]
            }
        }
    }
}


def mock_urlopen_router(url_or_request, *args, **kwargs):
    """Intercepts urllib.request.urlopen and returns mock responses based on URL."""
    url = url_or_request.full_url if hasattr(url_or_request, "full_url") else str(url_or_request)

    mock_resp = MagicMock()
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    if "search/?keyword=" in url:
        body = json.dumps(MOCK_SEARCH_RESPONSE).encode("utf-8")
        mock_resp.read.return_value = body
        return mock_resp

    elif "feed/" in url:
        if "bengaluru" in url.lower() or "8121" in url:
            body = json.dumps(MOCK_FEED_RESPONSE_CLEAN).encode("utf-8")
        else:
            body = json.dumps(MOCK_FEED_RESPONSE_DELHI).encode("utf-8")
        mock_resp.read.return_value = body
        return mock_resp

    # Default fallback
    mock_resp.read.return_value = json.dumps({"status": "ok", "data": []}).encode("utf-8")
    return mock_resp


# ── Test Suite ──────────────────────────────────────────────────────────────
def run_all_tests():
    print("=" * 65)
    print("  BreatheSafe — Offline Mock & Pipeline Test Suite")
    print("  Testing API Gateway, aqicn.org Mocks, Fallback & Decisions")
    print("=" * 65)

    passed = 0
    total = 0

    # 1. Test Mocked Search Endpoint via API Gateway
    total += 1
    print("\n[Test 1] API Gateway: Search Stations (?action=search&keyword=Delhi)")
    with patch("lambda_function.urlopen", side_effect=mock_urlopen_router):
        event = {
            "httpMethod": "GET",
            "queryStringParameters": {"action": "search", "keyword": "Delhi"}
        }
        res = lambda_function.lambda_handler(event, None)
        body = json.loads(res["body"])

        if res["statusCode"] == 200 and len(body.get("stations", [])) == 3:
            print(f"  [PASS] Found {len(body['stations'])} mock stations:")
            for s in body["stations"]:
                print(f"         - {s['station_name']} (AQI: {s['aqi']}, {s['category']['category']})")
            passed += 1
        else:
            print(f"  [FAIL] Unexpected search response: {res}")

    # 2. Test Mocked Feed & Advisory via API Gateway
    total += 1
    print("\n[Test 2] API Gateway: Station Feed & Advisory (?action=feed&station=8675)")
    with patch("lambda_function.urlopen", side_effect=mock_urlopen_router):
        event = {
            "httpMethod": "GET",
            "queryStringParameters": {"action": "feed", "station": "8675"}
        }
        res = lambda_function.lambda_handler(event, None)
        advisory = json.loads(res["body"])

        if res["statusCode"] == 200 and advisory.get("decision") in ["GO", "CAUTION", "NO-GO"]:
            print(f"  [PASS] Station: {advisory['station_name']}")
            print(f"         Current AQI : {advisory['current_aqi']} ({advisory['current_category']})")
            print(f"         Forecast AQI: {advisory['forecast_aqi']}")
            print(f"         Advisory    : {advisory['decision']}")
            print(f"         Actions     : {len(advisory['actions'])} school guidelines provided")
            passed += 1
        else:
            print(f"  [FAIL] Unexpected feed response: {res}")

    # 3. Test S3 Cache Fallback on API Timeout / Failure
    total += 1
    print("\n[Test 3] S3 Cache Fallback on API Timeout")
    # Simulate API failure and mock S3 cache read
    mock_cached_data = {
        "cached_at": "2026-09-29T15:30:00Z",
        "data": {
            "station_name": "Cached Anand Vihar Station",
            "current_aqi": 195,
            "forecast_aqi": 210,
            "decision": "NO-GO",
            "actions": ["Outdoor activities cancelled (cached)."]
        }
    }

    with patch("lambda_function.urlopen", side_effect=Exception("Connection timed out")):
        with patch("lambda_function.read_from_s3_cache", return_value=mock_cached_data):
            event = {
                "httpMethod": "GET",
                "queryStringParameters": {"action": "feed", "station": "anand_vihar"}
            }
            res = lambda_function.lambda_handler(event, None)
            data = json.loads(res["body"])

            if data.get("is_cached") is True and "last known data" in data.get("data_source", ""):
                print(f"  [PASS] Successfully recovered from cached data:")
                print(f"         Data Source : {data['data_source']}")
                print(f"         Decision    : {data['decision']}")
                passed += 1
            else:
                print(f"  [FAIL] Expected cached fallback, got: {data}")

    # 4. Test CORS OPTIONS Preflight
    total += 1
    print("\n[Test 4] CORS Preflight (OPTIONS Request)")
    event = {
        "httpMethod": "OPTIONS",
        "requestContext": {"http": {"method": "OPTIONS"}}
    }
    res = lambda_function.lambda_handler(event, None)
    if res["statusCode"] == 200 and res["headers"].get("Access-Control-Allow-Origin") == "*":
        print("  [PASS] Handled OPTIONS preflight with proper CORS headers.")
        passed += 1
    else:
        print(f"  [FAIL] CORS preflight failed: {res}")

    # 5. Core EWMA Forecast Scenarios (GO / CAUTION / NO-GO)
    print("\n[Test 5] Validating 5 Core EWMA Forecast Scenarios")
    scenarios = [
        ("Clean air week", [42, 55, 48, 60, 38, 45, 50], "GO"),
        ("Moderate pollution", [110, 130, 145, 125, 155, 140, 160], "CAUTION"),
        ("Hazardous smog", [220, 280, 350, 410, 390, 370, 345], "NO-GO"),
        ("Sudden stubble smoke spike", [80, 75, 90, 85, 70, 250, 310], "NO-GO"),
        ("Single reading edge case", [175], "CAUTION")
    ]

    all_scenarios_ok = True
    for name, readings, expected in scenarios:
        total += 1
        adv = generate_advisory(readings=readings, school_name="Test School", city="Delhi")
        if adv["decision"] == expected:
            print(f"  [PASS] {name:<28} -> AQI: {adv['forecast_aqi']:<5} -> {adv['decision']}")
            passed += 1
        else:
            print(f"  [FAIL] {name}: expected {expected}, got {adv['decision']}")
            all_scenarios_ok = False

    # Summary
    print("\n" + "=" * 65)
    print(f"  RESULTS: {passed}/{total} tests passed ({total - passed} failed)")
    if passed == total:
        print("  SUCCESS: Backend logic, mocks, caching, and decisions verified!")
    else:
        print("  WARNING: Some tests failed. Review output above.")
    print("=" * 65)


if __name__ == "__main__":
    run_all_tests()
