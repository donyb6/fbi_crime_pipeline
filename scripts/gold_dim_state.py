import os
import sys

from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db import get_session

STATE_DIMENSION = [
    {"state_abbr": "CA", "state_name": "California", "region": "West"},
    {"state_abbr": "TX", "state_name": "Texas",       "region": "South"},
    {"state_abbr": "WY", "state_name": "Wyoming",      "region": "West"},
    {"state_abbr": "VT", "state_name": "Vermont",      "region": "Northeast"},
]

def ensure_table(session):
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS gold_dim_state (
            state_abbr VARCHAR(2) PRIMARY KEY,
            state_name VARCHAR(100),
            region VARCHAR(50)
        )
    """))
    session.commit()
    
def run():
    session = get_session()
    ensure_table(session)
    
    for row in STATE_DIMENSION:
        session.execute(
            text("""
                 INSERT INTO gold_dim_state (state_abbr, state_name, region)
                 VALUES (:state_abbr, :state_name, :region)
                 ON DUPLICATE KEY UPDATE
                    state_name = VALUES(state_name),
                    region = VALUES(region)
            """),
            row
        )
        
    session.commit()
    session.close()
    print(f"Done. {len(STATE_DIMENSION)} state rows written.")
    
if __name__ == "__main__":
    run()