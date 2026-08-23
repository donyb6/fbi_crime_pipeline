import os
import sys
import json
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db import get_session

load_dotenv()

API_BASE = os.getenv("API_BASE")
API_KEY = os.getenv("FBI_API_KEY")
STATES = [s.strip().upper() for s in os.getenv("STATES", "").split(",") if s.strip()]


def ensure_table(session):
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS bronze_agencies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            state_abbr VARCHAR(2) NOT NULL,
            response_json LONGTEXT NOT NULL,
            extracted_at DATETIME NOT NULL
        )
    """))
    session.commit()


def fetch_agencies(state: str):
    url = f"{API_BASE}/agency/byStateAbbr/{state}"
    response = requests.get(url, params={"API_KEY": API_KEY}, timeout=30)
    return response


def run():
    if not API_KEY:
        print("Missing FBI_API_KEY in .env")
        return
    if not STATES:
        print("Missing STATES in .env")
        return

    session = get_session()
    ensure_table(session)

    for state in STATES:
        print(f"Fetching agencies for {state}...")
        response = fetch_agencies(state)

        if response.status_code != 200:
            print(f"  Failed: HTTP {response.status_code}")
            continue

        session.execute(
            text("""
                INSERT INTO bronze_agencies (state_abbr, response_json, extracted_at)
                VALUES (:state, :payload, :extracted_at)
            """),
            {
                "state": state,
                "payload": response.text,
                "extracted_at": datetime.now(timezone.utc),
            },
        )
        session.commit()
        print(f"  Landed ({len(response.text)} bytes)")

    session.close()
    print("Done.")


if __name__ == "__main__":
    run()