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


def flatten_offenses(raw_json: dict, state_abbr: str) -> list[dict]:
    """Turn the mm-yyyy time series offense dict into a flat list of offense rows."""
    state_name = STATE_NAMES.get(state_abbr, "Unknown")
    
    actuals = raw_json.get("offenses", {}).get("actuals", {})
    rates = raw_json.get("offenses", {}).get("rates", {})
    populations = raw_json.get("populations", {})
    
    state_actuals = actuals.get(f"{state_name} Offenses", {})