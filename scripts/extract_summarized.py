"""
Bronze layer extraction: pulls Summarized offense-count data from the FBI
Crime Data API for each configured state and offense code, landing the raw
JSON into MySQL untouched.
"""
import os
import sys
import time
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


OFFENSES = ["V", "P", "HOM", "RPE", "ROB", "ASS", "BUR", "LAR", "MVT", "ARS"]

FROM_DATE = "01-2020"
TO_DATE = "01-2026"

SLEEP_BETWEEN_CALLS = 0.5


def ensure_table(session):
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS bronze_summarized_offenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            state_abbr VARCHAR(2) NOT NULL,
            offense_code VARCHAR(10) NOT NULL,
            from_date VARCHAR(7) NOT NULL,
            to_date VARCHAR(7) NOT NULL,
            response_json LONGTEXT,
            http_status INT NOT NULL,
            extracted_at DATETIME NOT NULL
        )
    """))
    session.commit()


def fetch_summarized(state: str, offense: str):
    url = f"{API_BASE}/summarized/state/{state}/{offense}"
    params = {"from": FROM_DATE, "to": TO_DATE, "API_KEY": API_KEY}
    return requests.get(url, params=params, timeout=30)


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
        for offense in OFFENSES:
            print(f"Fetching {state}/{offense}...")
            response = fetch_summarized(state, offense)

            payload = response.text if response.status_code == 200 else None
            if response.status_code != 200:
                print(f"  Failed: HTTP {response.status_code}")

            session.execute(
                text("""
                    INSERT INTO bronze_summarized_offenses
                        (state_abbr, offense_code, from_date, to_date,
                         response_json, http_status, extracted_at)
                    VALUES (:state, :offense, :from_date, :to_date,
                            :payload, :http_status, :extracted_at)
                """),
                {
                    "state": state,
                    "offense": offense,
                    "from_date": FROM_DATE,
                    "to_date": TO_DATE,
                    "payload": payload,
                    "http_status": response.status_code,
                    "extracted_at": datetime.now(timezone.utc),
                },
            )
            session.commit()

            if response.status_code == 200:
                print(f"  Landed ({len(payload)} bytes)")

            time.sleep(SLEEP_BETWEEN_CALLS)

    session.close()
    print("Done.")


if __name__ == "__main__":
    run()