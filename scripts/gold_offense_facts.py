import os
import sys

from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db import get_session


def ensure_table(session):
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS gold_offense_facts (
            id INT AUTO_INCREMENT PRIMARY KEY,
            state_abbr VARCHAR(2) NOT NULL,
            offense_code VARCHAR(10) NOT NULL,
            year INT NOT NULL,
            month INT NOT NULL,
            actual_count INT NULL,
            clearance_count INT NULL,
            clearance_rate DECIMAL(6,4) NULL,
            rate_per_100k DECIMAL(10,4) NULL,
            population INT NULL,
            UNIQUE KEY uq_state_offense_month (state_abbr, offense_code, year, month),
            FOREIGN KEY (state_abbr) REFERENCES gold_dim_state(state_abbr),
            FOREIGN KEY (offense_code) REFERENCES gold_dim_offense(offense_code)
        )
    """))
    session.commit()


def run():
    session = get_session()
    ensure_table(session)

    result = session.execute(text("""
        INSERT INTO gold_offense_facts
            (state_abbr, offense_code, year, month,
             actual_count, clearance_count, clearance_rate,
             rate_per_100k, population)
        SELECT
            state_abbr, offense_code, year, month,
            state_actual_count,
            state_clearance_count,
            CASE
                WHEN state_actual_count IS NULL OR state_actual_count = 0 THEN NULL
                ELSE state_clearance_count / state_actual_count
            END,
            state_rate_per_100k,
            population
        FROM silver_summarized_offenses
        ON DUPLICATE KEY UPDATE
            actual_count = VALUES(actual_count),
            clearance_count = VALUES(clearance_count),
            clearance_rate = VALUES(clearance_rate),
            rate_per_100k = VALUES(rate_per_100k),
            population = VALUES(population)
    """))

    session.commit()
    session.close()
    print(f"Done. {result.rowcount} offense fact rows affected.")


if __name__ == "__main__":
    run()