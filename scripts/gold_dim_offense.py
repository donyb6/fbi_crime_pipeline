#GOLD LAYER
import os
import sys

from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db import get_session

OFFENSE_DIMENSION = [
    {"offense_code": "V",   "offense_name": "Violent Crime (All)",   "category": "Violent"},
    {"offense_code": "HOM", "offense_name": "Homicide",              "category": "Violent"},
    {"offense_code": "RPE", "offense_name": "Rape",                  "category": "Violent"},
    {"offense_code": "ROB", "offense_name": "Robbery",               "category": "Violent"},
    {"offense_code": "ASS", "offense_name": "Aggravated Assault",    "category": "Violent"},
    {"offense_code": "P",   "offense_name": "Property Crime (All)",  "category": "Property"},
    {"offense_code": "BUR", "offense_name": "Burglary",              "category": "Property"},
    {"offense_code": "LAR", "offense_name": "Larceny-Theft",         "category": "Property"},
    {"offense_code": "MVT", "offense_name": "Motor Vehicle Theft",   "category": "Property"},
    {"offense_code": "ARS", "offense_name": "Arson",                 "category": "Property"},
]


def ensure_table(session):
    session.execute(text("""
        CREATE TABLE IF NOT EXISTS gold_dim_offense (
            offense_code VARCHAR(10) PRIMARY KEY,
            offense_name VARCHAR(50) NOT NULL,
            category VARCHAR(20) NOT NULL
        )
    """))
    session.commit()
