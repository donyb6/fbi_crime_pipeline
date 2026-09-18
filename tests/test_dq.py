import os
import sys

import pytest
from sqlalchemy import text

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.db import get_session

@pytest.fixture
def session():
    """A fresh DB session for each test, closed automatically after."""
    s = get_session()
    yield s
    s.close()
    
# bronze layer tests
def test_bronze_agencies_has_four_states(session):
    result = session.execute(text("SELECT COUNT(DISTINCT state_abbr) FROM bronze_agencies")).scalar()
    assert result == 4, f"Expected 4 states in bronze_agencies, found {result}"


def test_bronze_summarized_all_calls_succeeded(session):
    failed = session.execute(
        text("SELECT COUNT(*) FROM bronze_summarized_offenses WHERE http_status != 200")
    ).scalar()
    assert failed == 0, f"{failed} bronze_summarized_offenses rows failed with non-200 status"
    
    
# silver layer tests
def test_silver_agencies_no_duplicate_oris(session):
    total = session.execute(text("SELECT COUNT(*) FROM silver_agencies")).scalar()
    distinct = session.execute(text("SELECT COUNT(DISTINCT ori) FROM silver_agencies")).scalar()
    assert total == distinct, "Duplicate ORI codes found in silver_agencies"


def test_silver_offenses_row_count_reasonable(session):
    total = session.execute(text("SELECT COUNT(*) FROM silver_summarized_offenses")).scalar()
    # 4 states x 10 offenses x ~73 months = ~2920, allow some tolerance
    assert 2800 <= total <= 3000, f"Unexpected silver_summarized_offenses row count: {total}"


def test_silver_offenses_no_negative_counts(session):
    bad = session.execute(text("""
        SELECT COUNT(*) FROM silver_summarized_offenses
        WHERE state_actual_count < 0 OR state_clearance_count < 0
    """)).scalar()
    assert bad == 0, f"{bad} rows have negative offense/clearance counts"


# gold layer tests
def test_gold_fact_rows_match_silver(session):
    silver_count = session.execute(text("SELECT COUNT(*) FROM silver_summarized_offenses")).scalar()
    gold_count = session.execute(text("SELECT COUNT(*) FROM gold_offense_facts")).scalar()
    assert silver_count == gold_count, (
        f"Row count mismatch: silver={silver_count}, gold={gold_count}"
    )


def test_gold_facts_have_no_orphaned_states(session):
    orphans = session.execute(text("""
        SELECT COUNT(*) FROM gold_offense_facts f
        LEFT JOIN gold_dim_state s ON f.state_abbr = s.state_abbr
        WHERE s.state_abbr IS NULL
    """)).scalar()
    assert orphans == 0, f"{orphans} fact rows reference a state not in gold_dim_state"


def test_gold_facts_have_no_orphaned_offenses(session):
    orphans = session.execute(text("""
        SELECT COUNT(*) FROM gold_offense_facts f
        LEFT JOIN gold_dim_offense o ON f.offense_code = o.offense_code
        WHERE o.offense_code IS NULL
    """)).scalar()
    assert orphans == 0, f"{orphans} fact rows reference an offense not in gold_dim_offense"


def test_gold_clearance_rate_within_valid_range(session):
    bad = session.execute(text("""
        SELECT COUNT(*) FROM gold_offense_facts
        WHERE clearance_rate < 0
    """)).scalar()
    assert bad == 0, f"{bad} rows have an out-of-range clearance_rate"


def test_gold_dim_agency_matches_silver(session):
    silver_count = session.execute(text("SELECT COUNT(*) FROM silver_agencies")).scalar()
    gold_count = session.execute(text("SELECT COUNT(*) FROM gold_dim_agency")).scalar()
    assert silver_count == gold_count, (
        f"Row count mismatch: silver_agencies={silver_count}, gold_dim_agency={gold_count}"
    )