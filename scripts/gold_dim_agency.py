import os
import sys

from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db import get_session


def ensure_table(session):
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS gold_dim_agency (
            ori VARCHAR(20) PRIMARY KEY,
            agency_name VARCHAR(255) NOT NULL,
            agency_type_name VARCHAR(50),
            county VARCHAR(100),
            state_abbr VARCHAR(2) NOT NULL,
            latitude DECIMAL(9,6) NULL,
            longitude DECIMAL(9,6) NULL,
            is_nibrs BOOLEAN,
            nibrs_start_date DATE NULL
        )
    """))
    session.commit()


def run():
    session = get_session()
    ensure_table(session)

    result = session.execute(text("""
        INSERT INTO gold_dim_agency
            (ori, agency_name, agency_type_name, county, state_abbr,
             latitude, longitude, is_nibrs, nibrs_start_date)
        SELECT
            ori, agency_name, agency_type_name, county, state_abbr,
            latitude, longitude, is_nibrs, nibrs_start_date
        FROM silver_agencies
        ON DUPLICATE KEY UPDATE
            agency_name = VALUES(agency_name),
            agency_type_name = VALUES(agency_type_name),
            county = VALUES(county),
            latitude = VALUES(latitude),
            longitude = VALUES(longitude),
            is_nibrs = VALUES(is_nibrs),
            nibrs_start_date = VALUES(nibrs_start_date)
    """))

    session.commit()
    session.close()
    print(f"Done. {result.rowcount} agency dimension rows affected.")


if __name__ == "__main__":
    run()