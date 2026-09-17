import os
import sys
import json

from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db import get_session


STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
    "CA": "California", "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware",
    "FL": "Florida", "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho",
    "IL": "Illinois", "IN": "Indiana", "IA": "Iowa", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "ME": "Maine", "MD": "Maryland",
    "MA": "Massachusetts", "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi",
    "MO": "Missouri", "MT": "Montana", "NE": "Nebraska", "NV": "Nevada",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
    "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island", "SC": "South Carolina",
    "SD": "South Dakota", "TN": "Tennessee", "TX": "Texas", "UT": "Utah",
    "VT": "Vermont", "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
    "WI": "Wisconsin", "WY": "Wyoming",
}


def ensure_table(session):
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS silver_summarized_offenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            state_abbr VARCHAR(2) NOT NULL,
            offense_code VARCHAR(10) NOT NULL,
            year INT NOT NULL,
            month INT NOT NULL,
            state_actual_count INT NULL,
            state_clearance_count INT NULL,
            state_rate_per_100k DECIMAL(10,4) NULL,
            state_clearance_rate_per_100k DECIMAL(10,4) NULL,
            us_actual_rate DECIMAL(10,4) NULL,
            us_clearance_rate DECIMAL(10,4) NULL,
            population INT NULL,
            participated_population INT NULL,
            UNIQUE KEY uq_state_offense_month (state_abbr, offense_code, year, month)
        )
    """))
    session.commit()


def flatten_offenses(raw_json: dict, state_abbr: str, offense_code: str) -> list[dict]:
    """Turn the nested mm-yyyy time series into a flat list of rows."""
    state_name = STATE_NAMES.get(state_abbr)
    if not state_name:
        print(f"  Warning: no full name mapping for {state_abbr}, skipping")
        return []

    actuals = raw_json.get("offenses", {}).get("actuals", {})
    rates = raw_json.get("offenses", {}).get("rates", {})
    populations = raw_json.get("populations", {})

    state_actuals = actuals.get(f"{state_name} Offenses", {})
    state_clearance_actuals = actuals.get(f"{state_name} Clearances", {})
    us_actuals = actuals.get("United States Offenses", {})
    us_clearance_actuals = actuals.get("United States Clearances", {})

    state_rates = rates.get(f"{state_name} Offenses", {})
    state_clearance_rates = rates.get(f"{state_name} Clearances", {})

    population = populations.get("population", {}).get(state_name, {})
    participated_population = populations.get("participated_population", {}).get(state_name, {})

    rows = []
    for month_key in state_actuals.keys():  # e.g "07-2024"
        month_str, year_str = month_key.split("-")

        rows.append({
            "state_abbr": state_abbr,
            "offense_code": offense_code,
            "year": int(year_str),
            "month": int(month_str),
            "state_actual_count": state_actuals.get(month_key),
            "state_clearance_count": state_clearance_actuals.get(month_key),
            "state_rate_per_100k": state_rates.get(month_key),
            "state_clearance_rate_per_100k": state_clearance_rates.get(month_key),
            "us_actual_rate": us_actuals.get(month_key),
            "us_clearance_rate": us_clearance_actuals.get(month_key),
            "population": population.get(month_key),
            "participated_population": participated_population.get(month_key),
        })
    return rows


def run():
    session = get_session()
    ensure_table(session)

    bronze_rows = session.execute(
        text("""
            SELECT state_abbr, offense_code, response_json
            FROM bronze_summarized_offenses
            WHERE http_status = 200
        """)
    ).fetchall()

    total_inserted = 0

    for state_abbr, offense_code, response_json in bronze_rows:
        raw_json = json.loads(response_json)
        offense_rows = flatten_offenses(raw_json, state_abbr, offense_code)

        for row in offense_rows:
            session.execute(
                text("""
                    INSERT INTO silver_summarized_offenses
                        (state_abbr, offense_code, year, month,
                         state_actual_count, state_clearance_count,
                         state_rate_per_100k, state_clearance_rate_per_100k,
                         us_actual_rate, us_clearance_rate,
                         population, participated_population)
                    VALUES
                        (:state_abbr, :offense_code, :year, :month,
                         :state_actual_count, :state_clearance_count,
                         :state_rate_per_100k, :state_clearance_rate_per_100k,
                         :us_actual_rate, :us_clearance_rate,
                         :population, :participated_population)
                    ON DUPLICATE KEY UPDATE
                        state_actual_count = VALUES(state_actual_count),
                        state_clearance_count = VALUES(state_clearance_count),
                        state_rate_per_100k = VALUES(state_rate_per_100k),
                        state_clearance_rate_per_100k = VALUES(state_clearance_rate_per_100k),
                        us_actual_rate = VALUES(us_actual_rate),
                        us_clearance_rate = VALUES(us_clearance_rate),
                        population = VALUES(population),
                        participated_population = VALUES(participated_population)
                """),
                row,
            )
            total_inserted += 1

        session.commit()
        print(f"{state_abbr}/{offense_code}: {len(offense_rows)} months flattened")

    session.close()
    print(f"Done. {total_inserted} offense rows processed.")


if __name__ == "__main__":
    run()