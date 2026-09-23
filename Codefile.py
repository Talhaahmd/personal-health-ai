"""
Personal Health AI — Fitbit / Health Data + Claude + WhatsApp

ARCHITECTURE

Health/Fitbit API
       ↓
   Python Backend
       ↓
  Health Data Store
       ↓
    Claude API
       ↓
  Actionable Report
       ↓
 Zernio WhatsApp API

IMPORTANT:
- Replace all API placeholders before running.
- This is a personal health-data experiment, not a medical device.
- AI-generated recommendations should not be treated as medical advice.
"""

import os
import json
import sqlite3
import requests
from datetime import datetime, timedelta
from flask import Flask, request, jsonify

# ============================================================
# CONFIGURATION
# ============================================================

app = Flask(__name__)

# ------------------------------------------------------------
# API KEYS
# ------------------------------------------------------------

CLAUDE_API_KEY = os.getenv(
    "CLAUDE_API_KEY",
    "YOUR_CLAUDE_API_KEY"
)

ZERNIO_API_KEY = os.getenv(
    "ZERNIO_API_KEY",
    "YOUR_ZERNIO_API_KEY"
)

# ------------------------------------------------------------
# API ENDPOINTS
# ------------------------------------------------------------

CLAUDE_API_URL = os.getenv(
    "CLAUDE_API_URL",
    "https://api.anthropic.com/v1/messages"
)

ZERNIO_API_URL = os.getenv(
    "ZERNIO_API_URL",
    "YOUR_ZERNIO_WHATSAPP_ENDPOINT"
)

# ------------------------------------------------------------
# HEALTH API
#
# Replace these with the API you're actually using.
#
# For example:
# - Fitbit Web API
# - Google Health Connect data exported through your backend
# - Google Health API / approved health-data integration
# ------------------------------------------------------------

HEALTH_API_BASE_URL = os.getenv(
    "HEALTH_API_BASE_URL",
    "YOUR_HEALTH_API_BASE_URL"
)

HEALTH_ACCESS_TOKEN = os.getenv(
    "HEALTH_ACCESS_TOKEN",
    "YOUR_HEALTH_ACCESS_TOKEN"
)

# Your WhatsApp number
WHATSAPP_NUMBER = os.getenv(
    "WHATSAPP_NUMBER",
    "YOUR_WHATSAPP_NUMBER"
)

# ============================================================
# DATABASE
# ============================================================

DB_NAME = "health_ai.db"


def init_database():
    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS health_metrics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            data TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            message TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            report TEXT
        )
    """)

    conn.commit()
    conn.close()


init_database()


# ============================================================
# DATABASE HELPERS
# ============================================================

def save_health_metrics(data):
    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO health_metrics (timestamp, data)
        VALUES (?, ?)
        """,
        (
            datetime.utcnow().isoformat(),
            json.dumps(data)
        )
    )

    conn.commit()
    conn.close()


def save_user_log(message):
    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO user_logs (timestamp, message)
        VALUES (?, ?)
        """,
        (
            datetime.utcnow().isoformat(),
            message
        )
    )

    conn.commit()
    conn.close()


def save_report(report):
    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO reports (timestamp, report)
        VALUES (?, ?)
        """,
        (
            datetime.utcnow().isoformat(),
            report
        )
    )

    conn.commit()
    conn.close()


def get_recent_health_data(hours=24):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cutoff = (
        datetime.utcnow() -
        timedelta(hours=hours)
    ).isoformat()

    cursor.execute(
        """
        SELECT timestamp, data
        FROM health_metrics
        WHERE timestamp >= ?
        ORDER BY timestamp ASC
        """,
        (cutoff,)
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "timestamp": timestamp,
            "data": json.loads(data)
        }
        for timestamp, data in rows
    ]


def get_recent_user_logs(hours=24):

    conn = sqlite3.connect(DB_NAME)

    cursor = conn.cursor()

    cutoff = (
        datetime.utcnow() -
        timedelta(hours=hours)
    ).isoformat()

    cursor.execute(
        """
        SELECT timestamp, message
        FROM user_logs
        WHERE timestamp >= ?
        ORDER BY timestamp ASC
        """,
        (cutoff,)
    )

    rows = cursor.fetchall()

    conn.close()

    return [
        {
            "timestamp": timestamp,
            "message": message
        }
        for timestamp, message in rows
    ]


# ============================================================
# HEALTH DATA
# ============================================================

def get_health_data():

    """
    Fetch health data from your health provider.

    Replace this implementation with your actual API.

    Example Fitbit metrics:

        resting_heart_rate
        hrv
        vo2_max
        cardio_load
        sleep_duration
        sleep_efficiency
        sleep_score
        readiness_score
        steps
        calories
        active_zone_minutes
        sleep_stages
        weight

    """

    headers = {
        "Authorization": f"Bearer {HEALTH_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # --------------------------------------------------------
    # PLACEHOLDER
    # --------------------------------------------------------

    # Example:

    # response = requests.get(
    #     f"{HEALTH_API_BASE_URL}/user/health",
    #     headers=headers
    # )
    #
    # response.raise_for_status()
    #
    # return response.json()

    # --------------------------------------------------------
    # MOCK DATA
    # Remove this when connecting the real API.
    # --------------------------------------------------------

    mock_data = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),

        "readiness_score": 90,

        "sleep": {
            "duration_hours": 6.2,
            "efficiency": 91,
            "quality_score": 88,
            "deep_sleep_hours": 1.2,
            "rem_sleep_hours": 1.6
        },

        "heart": {
            "resting_heart_rate": 61,
            "hrv": 52
        },

        "fitness": {
            "vo2_max": 42.1,
            "cardio_load": 76,
            "steps": 8432,
            "active_zone_minutes": 48
        },

        "body": {
            "weight_kg": 82.0
        },

        "recovery": {
            "stress": "moderate"
        }
    }

    return mock_data


# ============================================================
# CLAUDE
# ============================================================

def generate_health_report(
    health_data,
    user_logs
):

    prompt = f"""
You are a personal health-data analysis assistant.

Your job is to analyze a user's health metrics together with
their self-reported food, activity, sleep and lifestyle data.

Do NOT diagnose diseases.

Do NOT make medical claims.

Focus on patterns, correlations, habits and practical actions.

USER HEALTH DATA:

{json.dumps(health_data, indent=2)}

USER SELF-REPORTED DATA:

{json.dumps(user_logs, indent=2)}

Generate a concise 24-hour health report.

Structure the report as:

1. OVERALL STATUS

Give a short summary of the user's current state.

2. WHAT IS WORKING

Identify positive patterns.

3. WHAT NEEDS ATTENTION

Identify metrics or habits that may need attention.

4. CONNECTIONS

Explain potential relationships between:

- food
- exercise
- sleep
- stress
- resting heart rate
- HRV
- readiness
- cardio load
- weight

Be careful not to claim causation when the data only shows
a possible correlation.

5. TODAY'S ACTIONS

Give 3-5 practical actions the user can take today.

6. ONE THING TO WATCH

Identify the single most useful metric or habit to monitor.

Keep the report easy to understand.

The user does not want a dashboard full of numbers.

They want to know:

"What should I actually do?"
"""

    headers = {
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }

    payload = {
        "model": "YOUR_CLAUDE_MODEL",
        "max_tokens": 1800,
        "temperature": 0.3,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }

    response = requests.post(
        CLAUDE_API_URL,
        headers=headers,
        json=payload,
        timeout=60
    )

    response.raise_for_status()

    result = response.json()

    # --------------------------------------------------------
    # Claude response extraction
    #
    # Adjust this if your Claude endpoint returns a
    # different structure.
    # --------------------------------------------------------

    report = result["content"][0]["text"]

    return report


# ============================================================
# WHATSAPP / ZERNIO
# ============================================================

def send_whatsapp_message(
    phone_number,
    message
):

    """
    Send the generated report through Zernio.

    Replace the payload fields below with the exact
    Zernio WhatsApp API structure.
    """

    headers = {
        "Authorization": f"Bearer {ZERNIO_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {

        # ----------------------------------------------------
        # PLACEHOLDER
        # ----------------------------------------------------

        "to": phone_number,

        "message": message

        # Example if Zernio requires:
        #
        # "recipient": phone_number,
        # "type": "text",
        # "text": {
        #     "body": message
        # }
    }

    response = requests.post(
        ZERNIO_API_URL,
        headers=headers,
        json=payload,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# DAILY REPORT
# ============================================================

def generate_daily_report():

    print("Fetching health data...")

    health_data = get_health_data()

    save_health_metrics(health_data)

    print("Fetching user activity logs...")

    user_logs = get_recent_user_logs(24)

    print("Generating Claude report...")

    report = generate_health_report(
        health_data,
        user_logs
    )

    save_report(report)

    print("Sending report to WhatsApp...")

    send_whatsapp_message(
        WHATSAPP_NUMBER,
        report
    )

    print("Report generated successfully.")

    return report


# ============================================================
# WHATSAPP WEBHOOK
# ============================================================

@app.route(
    "/webhook/whatsapp",
    methods=["POST"]
)
def whatsapp_webhook():

    """
    Zernio should send incoming WhatsApp messages here.

    Example message:

    "I had eggs and toast for breakfast,
     walked 5000 steps and felt tired."

    """

    data = request.json

    print(
        "Incoming WhatsApp message:",
        json.dumps(data, indent=2)
    )

    # --------------------------------------------------------
    # PLACEHOLDER
    #
    # Extract the message based on Zernio's webhook format.
    # --------------------------------------------------------

    message = data.get(
        "message",
        ""
    )

    phone_number = data.get(
        "from",
        WHATSAPP_NUMBER
    )

    if not message:

        return jsonify({
            "status": "ignored"
        })

    # Save user's message

    save_user_log(message)

    # --------------------------------------------------------
    # Optional:
    #
    # Ask Claude to acknowledge / interpret the message.
    # --------------------------------------------------------

    response_message = (
        "Got it. I've added that to your health log. "
        "I'll include it in your next 24-hour report."
    )

    send_whatsapp_message(
        phone_number,
        response_message
    )

    return jsonify({
        "status": "success"
    })


# ============================================================
# MANUAL REPORT ENDPOINT
# ============================================================

@app.route(
    "/generate-report",
    methods=["POST"]
)
def manual_report():

    try:

        report = generate_daily_report()

        return jsonify({
            "success": True,
            "report": report
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# HEALTH DATA SYNC ENDPOINT
# ============================================================

@app.route(
    "/sync-health",
    methods=["POST"]
)
def sync_health():

    try:

        health_data = get_health_data()

        save_health_metrics(
            health_data
        )

        return jsonify({
            "success": True,
            "data": health_data
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# LOCAL TEST
# ============================================================

@app.route("/")
def home():

    return jsonify({
        "name": "Personal Health AI",
        "status": "running",
        "endpoints": [
            "/webhook/whatsapp",
            "/sync-health",
            "/generate-report"
        ]
    })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=int(
            os.getenv(
                "PORT",
                5000
            )
        ),
        debug=True
    )
