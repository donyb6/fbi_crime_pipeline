import os
import sys
import json

from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db import get_session


def ensure_table(session):
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS silver_agencies (
            ori VARCHAR(20) PRIMARY KEY,
            agency_name VARCHAR(255) NOT NULL,
            agency_type_name VARCHAR(50),
            county VARCHAR(100),
            state_abbr VARCHAR(2) NOT NULL,
            state_name VARCHAR(50),
            latitude DECIMAL(9,6) NULL,
            longitude DECIMAL(9,6) NULL,
            is_nibrs BOOLEAN,
            nibrs_start_date DATE NULL
        )
    """))
    session.commit()


def flatten_agencies(raw_json: dict, state_abbr: str) -> list[dict]:
    """Turn a county-grouped agency dict into a flat list of agency rows."""
    rows = []
    for county, agencies in raw_json.items():
        for agency in agencies:
            rows.append({
                "ori": agency.get("ori"),
                "agency_name": agency.get("agency_name"),
                "agency_type_name": agency.get("agency_type_name"),
                "county": county,
                "state_abbr": state_abbr,
                "state_name": agency.get("state_name"),
                "latitude": agency.get("latitude"),
                "longitude": agency.get("longitude"),
                "is_nibrs": agency.get("is_nibrs"),
                "nibrs_start_date": agency.get("nibrs_start_date"),
            })
    return rows


def run():
    session = get_session()
    ensure_table(session)

    bronze_rows = session.execute(
        text("SELECT state_abbr, response_json FROM bronze_agencies")
    ).fetchall()

    total_inserted = 0

    for state_abbr, response_json in bronze_rows:
        raw_json = json.loads(response_json)
        agency_rows = flatten_agencies(raw_json, state_abbr)

        for row in agency_rows:
            session.execute(
                text("""
                    INSERT INTO silver_agencies
                        (ori, agency_name, agency_type_name, county, state_abbr,
                         state_name, latitude, longitude, is_nibrs, nibrs_start_date)
                    VALUES
                        (:ori, :agency_name, :agency_type_name, :county, :state_abbr,
                         :state_name, :latitude, :longitude, :is_nibrs, :nibrs_start_date)
                    ON DUPLICATE KEY UPDATE
                        agency_name = VALUES(agency_name),
                        agency_type_name = VALUES(agency_type_name),
                        county = VALUES(county),
                        latitude = VALUES(latitude),
                        longitude = VALUES(longitude),
                        is_nibrs = VALUES(is_nibrs),
                        nibrs_start_date = VALUES(nibrs_start_date)
                """),
                row,
            )
            total_inserted += 1

        session.commit()
        print(f"{state_abbr}: {len(agency_rows)} agencies flattened")

    session.close()
    print(f"Done. {total_inserted} agency rows processed.")


if __name__ == "__main__":
    run()