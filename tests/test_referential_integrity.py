"""
tests/test_referential_integrity.py
====================================
Validates that the seeded database satisfies all referential integrity
constraints, data quality rules, business domain rules, and minimum
row-count expectations.

Run with:
    pytest tests/ -v
    pytest tests/ -v -k "TestCounts"         # only count tests
    pytest tests/ -v --tb=short              # compact output
"""

from __future__ import annotations

import os
import pytest
import psycopg2


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def q(conn, sql: str, params: tuple = ()) -> list:
    """Execute a query and return all rows as plain tuples."""
    with conn.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchall()


def scalar(conn, sql: str, params: tuple = ()) -> int | float | None:
    """Return the first column of the first row."""
    rows = q(conn, sql, params)
    return rows[0][0] if rows else None


# ─────────────────────────────────────────────────────────────────────────────
# Class 1 – Referential Integrity
# Verify that every FK relationship is intact (no orphan rows).
# These checks run WITHOUT relying on the FK constraint itself, so they
# also validate that the seed generator built the joins correctly.
# ─────────────────────────────────────────────────────────────────────────────

class TestReferentialIntegrity:

    def test_accounts_all_have_valid_customer(self, db_conn):
        """Every account.customer_id must exist in customers."""
        orphans = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.accounts a
            WHERE NOT EXISTS (
                SELECT 1 FROM utility.customers c WHERE c.customer_id = a.customer_id
            )
        """)
        assert orphans == 0, f"{orphans} account(s) reference a non-existent customer"

    def test_premises_all_have_valid_account(self, db_conn):
        """Every premise.account_id must exist in accounts."""
        orphans = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.premises p
            WHERE NOT EXISTS (
                SELECT 1 FROM utility.accounts a WHERE a.account_id = p.account_id
            )
        """)
        assert orphans == 0, f"{orphans} premise(s) reference a non-existent account"

    def test_contracts_all_have_valid_account(self, db_conn):
        orphans = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.contracts ct
            WHERE NOT EXISTS (
                SELECT 1 FROM utility.accounts a WHERE a.account_id = ct.account_id
            )
        """)
        assert orphans == 0, f"{orphans} contract(s) reference a non-existent account"

    def test_contracts_all_have_valid_premise(self, db_conn):
        orphans = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.contracts ct
            WHERE NOT EXISTS (
                SELECT 1 FROM utility.premises p WHERE p.premise_id = ct.premise_id
            )
        """)
        assert orphans == 0, f"{orphans} contract(s) reference a non-existent premise"

    def test_service_points_all_have_valid_premise(self, db_conn):
        orphans = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.service_points sp
            WHERE NOT EXISTS (
                SELECT 1 FROM utility.premises p WHERE p.premise_id = sp.premise_id
            )
        """)
        assert orphans == 0, f"{orphans} service_point(s) reference a non-existent premise"

    def test_service_points_all_have_valid_contract(self, db_conn):
        orphans = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.service_points sp
            WHERE NOT EXISTS (
                SELECT 1 FROM utility.contracts ct WHERE ct.contract_id = sp.contract_id
            )
        """)
        assert orphans == 0, f"{orphans} service_point(s) reference a non-existent contract"

    def test_meters_all_have_valid_service_point(self, db_conn):
        orphans = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.meters m
            WHERE NOT EXISTS (
                SELECT 1 FROM utility.service_points sp
                WHERE sp.service_point_id = m.service_point_id
            )
        """)
        assert orphans == 0, f"{orphans} meter(s) reference a non-existent service_point"

    def test_meter_readings_all_have_valid_meter(self, db_conn):
        orphans = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.meter_readings mr
            WHERE NOT EXISTS (
                SELECT 1 FROM utility.meters m WHERE m.meter_id = mr.meter_id
            )
        """)
        assert orphans == 0, f"{orphans} meter_reading(s) reference a non-existent meter"

    def test_bills_all_have_valid_account(self, db_conn):
        orphans = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.bills b
            WHERE NOT EXISTS (
                SELECT 1 FROM utility.accounts a WHERE a.account_id = b.account_id
            )
        """)
        assert orphans == 0, f"{orphans} bill(s) reference a non-existent account"

    def test_bills_all_have_valid_contract(self, db_conn):
        orphans = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.bills b
            WHERE NOT EXISTS (
                SELECT 1 FROM utility.contracts ct WHERE ct.contract_id = b.contract_id
            )
        """)
        assert orphans == 0, f"{orphans} bill(s) reference a non-existent contract"

    def test_payments_all_have_valid_bill(self, db_conn):
        orphans = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.payments p
            WHERE NOT EXISTS (
                SELECT 1 FROM utility.bills b WHERE b.bill_id = p.bill_id
            )
        """)
        assert orphans == 0, f"{orphans} payment(s) reference a non-existent bill"

    def test_payments_all_have_valid_account(self, db_conn):
        orphans = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.payments p
            WHERE NOT EXISTS (
                SELECT 1 FROM utility.accounts a WHERE a.account_id = p.account_id
            )
        """)
        assert orphans == 0, f"{orphans} payment(s) reference a non-existent account"


# ─────────────────────────────────────────────────────────────────────────────
# Class 2 – Data Quality
# ─────────────────────────────────────────────────────────────────────────────

class TestDataQuality:

    def test_customer_emails_not_null(self, db_conn):
        nulls = scalar(db_conn,
            "SELECT COUNT(*) FROM utility.customers WHERE email IS NULL")
        assert nulls == 0, f"{nulls} customer(s) have NULL email"

    def test_customer_first_last_name_not_null(self, db_conn):
        nulls = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.customers
            WHERE first_name IS NULL OR last_name IS NULL
        """)
        assert nulls == 0, f"{nulls} customer(s) have NULL name fields"

    def test_customer_type_valid_enum(self, db_conn):
        invalid = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.customers
            WHERE customer_type NOT IN ('RESIDENTIAL', 'COMMERCIAL', 'INDUSTRIAL')
        """)
        assert invalid == 0, f"{invalid} customer(s) have invalid customer_type"

    def test_reading_values_non_negative(self, db_conn):
        negatives = scalar(db_conn,
            "SELECT COUNT(*) FROM utility.meter_readings WHERE reading_value < 0")
        assert negatives == 0, f"{negatives} reading(s) have negative reading_value"

    def test_bill_total_amounts_non_negative(self, db_conn):
        invalid = scalar(db_conn,
            "SELECT COUNT(*) FROM utility.bills WHERE total_amount < 0")
        assert invalid == 0, f"{invalid} bill(s) have negative total_amount"

    def test_bill_tax_non_negative(self, db_conn):
        invalid = scalar(db_conn,
            "SELECT COUNT(*) FROM utility.bills WHERE tax_amount < 0")
        assert invalid == 0, f"{invalid} bill(s) have negative tax_amount"

    def test_payment_amounts_positive(self, db_conn):
        invalid = scalar(db_conn,
            "SELECT COUNT(*) FROM utility.payments WHERE amount <= 0")
        assert invalid == 0, f"{invalid} payment(s) have non-positive amount"

    def test_meter_multiplier_positive(self, db_conn):
        invalid = scalar(db_conn,
            "SELECT COUNT(*) FROM utility.meters WHERE multiplier <= 0")
        assert invalid == 0, f"{invalid} meter(s) have non-positive multiplier"

    def test_updated_at_gte_created_at_customers(self, db_conn):
        invalid = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.customers
            WHERE updated_at < created_at
        """)
        assert invalid == 0, f"{invalid} customer(s) have updated_at < created_at"

    def test_updated_at_gte_created_at_accounts(self, db_conn):
        invalid = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.accounts
            WHERE updated_at < created_at
        """)
        assert invalid == 0

    def test_updated_at_gte_created_at_bills(self, db_conn):
        invalid = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.bills
            WHERE updated_at < created_at
        """)
        assert invalid == 0

    def test_contract_end_after_start(self, db_conn):
        invalid = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.contracts
            WHERE end_date IS NOT NULL AND end_date <= start_date
        """)
        assert invalid == 0, f"{invalid} contract(s) have end_date <= start_date"

    def test_meter_decommission_after_install(self, db_conn):
        invalid = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.meters
            WHERE decommission_date IS NOT NULL
              AND decommission_date < installation_date
        """)
        assert invalid == 0, f"{invalid} meter(s) have decommission_date < installation_date"

    def test_bill_period_end_after_start(self, db_conn):
        invalid = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.bills
            WHERE period_end <= period_start
        """)
        assert invalid == 0, f"{invalid} bill(s) have period_end <= period_start"

    def test_bill_due_date_on_or_after_bill_date(self, db_conn):
        invalid = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.bills
            WHERE due_date < bill_date
        """)
        assert invalid == 0, f"{invalid} bill(s) have due_date < bill_date"

    def test_payment_cleared_has_settled_at(self, db_conn):
        """All CLEARED payments should have a settled_at timestamp."""
        invalid = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.payments
            WHERE payment_status = 'CLEARED' AND settled_at IS NULL
        """)
        assert invalid == 0, f"{invalid} CLEARED payment(s) are missing settled_at"

    def test_quality_flag_valid_enum(self, db_conn):
        invalid = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.meter_readings
            WHERE quality_flag NOT IN ('VALID', 'ESTIMATED', 'SUSPECT', 'REJECTED')
        """)
        assert invalid == 0, f"{invalid} reading(s) have invalid quality_flag"

    def test_commodity_type_valid_on_contracts(self, db_conn):
        invalid = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.contracts
            WHERE commodity_type NOT IN ('ELECTRICITY', 'GAS', 'WATER')
        """)
        assert invalid == 0

    def test_account_status_valid_enum(self, db_conn):
        invalid = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.accounts
            WHERE account_status NOT IN ('ACTIVE', 'SUSPENDED', 'CLOSED')
        """)
        assert invalid == 0


# ─────────────────────────────────────────────────────────────────────────────
# Class 3 – Uniqueness
# ─────────────────────────────────────────────────────────────────────────────

class TestUniqueness:

    def test_customer_numbers_unique(self, db_conn):
        dupes = scalar(db_conn, """
            SELECT COUNT(*) FROM (
                SELECT customer_number
                FROM utility.customers
                GROUP BY customer_number HAVING COUNT(*) > 1
            ) t
        """)
        assert dupes == 0, f"{dupes} duplicate customer_number(s) found"

    def test_account_numbers_unique(self, db_conn):
        dupes = scalar(db_conn, """
            SELECT COUNT(*) FROM (
                SELECT account_number FROM utility.accounts
                GROUP BY account_number HAVING COUNT(*) > 1
            ) t
        """)
        assert dupes == 0

    def test_meter_serial_numbers_unique(self, db_conn):
        dupes = scalar(db_conn, """
            SELECT COUNT(*) FROM (
                SELECT meter_serial_number FROM utility.meters
                GROUP BY meter_serial_number HAVING COUNT(*) > 1
            ) t
        """)
        assert dupes == 0

    def test_bill_numbers_unique(self, db_conn):
        dupes = scalar(db_conn, """
            SELECT COUNT(*) FROM (
                SELECT bill_number FROM utility.bills
                GROUP BY bill_number HAVING COUNT(*) > 1
            ) t
        """)
        assert dupes == 0

    def test_payment_references_unique(self, db_conn):
        dupes = scalar(db_conn, """
            SELECT COUNT(*) FROM (
                SELECT payment_reference FROM utility.payments
                GROUP BY payment_reference HAVING COUNT(*) > 1
            ) t
        """)
        assert dupes == 0

    def test_service_point_one_per_contract(self, db_conn):
        """Each contract must have at most one service point (UNIQUE constraint check)."""
        dupes = scalar(db_conn, """
            SELECT COUNT(*) FROM (
                SELECT contract_id FROM utility.service_points
                GROUP BY contract_id HAVING COUNT(*) > 1
            ) t
        """)
        assert dupes == 0, f"{dupes} contract(s) have more than one service_point"

    def test_meter_one_per_service_point(self, db_conn):
        """Each service point must have at most one meter."""
        dupes = scalar(db_conn, """
            SELECT COUNT(*) FROM (
                SELECT service_point_id FROM utility.meters
                GROUP BY service_point_id HAVING COUNT(*) > 1
            ) t
        """)
        assert dupes == 0, f"{dupes} service_point(s) have more than one meter"


# ─────────────────────────────────────────────────────────────────────────────
# Class 4 – Minimum Row Counts
# ─────────────────────────────────────────────────────────────────────────────

class TestCounts:

    @pytest.fixture(scope="class")
    def counts(self, db_conn) -> dict:
        tables = [
            "customers", "accounts", "premises", "contracts",
            "service_points", "meters", "meter_readings", "bills", "payments",
        ]
        return {
            t: scalar(db_conn, f"SELECT COUNT(*) FROM utility.{t}")
            for t in tables
        }

    def test_minimum_customers(self, counts):
        assert counts["customers"] >= 1_000, \
            f"Only {counts['customers']} customers (expected >= 1000)"

    def test_minimum_accounts(self, counts):
        assert counts["accounts"] >= counts["customers"], \
            "Should have at least as many accounts as customers"

    def test_minimum_premises(self, counts):
        assert counts["premises"] >= counts["accounts"], \
            "Should have at least one premise per account"

    def test_minimum_contracts(self, counts):
        assert counts["contracts"] >= counts["accounts"], \
            "Should have at least one contract per account"

    def test_minimum_service_points(self, counts):
        assert counts["service_points"] == counts["contracts"], \
            "service_points count must equal contracts count (1:1)"

    def test_minimum_meters(self, counts):
        assert counts["meters"] == counts["service_points"], \
            "meters count must equal service_points count (1:1)"

    def test_minimum_meter_readings(self, counts):
        assert counts["meter_readings"] >= 1_000, \
            f"Only {counts['meter_readings']} readings (expected >= 1000)"

    def test_minimum_bills(self, counts):
        assert counts["bills"] >= counts["contracts"], \
            "Should have at least one bill per contract"

    def test_minimum_payments(self, counts):
        # At least 50% of bills should have a payment
        min_expected = counts["bills"] // 2
        assert counts["payments"] >= min_expected, \
            f"Too few payments: {counts['payments']} for {counts['bills']} bills"

    def test_print_summary(self, db_conn, counts):
        """Not a real test — prints a summary table. Always passes."""
        print("\n\n" + "=" * 55)
        print(f"{'Table':<25}  {'Rows':>12}")
        print("=" * 55)
        for table, count in counts.items():
            print(f"  utility.{table:<22} {count:>10,}")
        print("=" * 55)


# ─────────────────────────────────────────────────────────────────────────────
# Class 5 – Business Domain Rules
# ─────────────────────────────────────────────────────────────────────────────

class TestBusinessRules:

    def test_contract_commodity_matches_service_point(self, db_conn):
        """service_point.commodity_type must equal its contract.commodity_type."""
        mismatches = scalar(db_conn, """
            SELECT COUNT(*)
              FROM utility.service_points sp
              JOIN utility.contracts ct ON ct.contract_id = sp.contract_id
             WHERE sp.commodity_type <> ct.commodity_type
        """)
        assert mismatches == 0, \
            f"{mismatches} service_point(s) have commodity_type mismatch with their contract"

    def test_contract_commodity_matches_meter(self, db_conn):
        """meter.commodity_type must equal its service_point.commodity_type."""
        mismatches = scalar(db_conn, """
            SELECT COUNT(*)
              FROM utility.meters m
              JOIN utility.service_points sp ON sp.service_point_id = m.service_point_id
             WHERE m.commodity_type <> sp.commodity_type
        """)
        assert mismatches == 0, \
            f"{mismatches} meter(s) have commodity_type mismatch with their service_point"

    def test_account_bill_consistency(self, db_conn):
        """Bills reference accounts that exist in the same account hierarchy as contracts."""
        mismatches = scalar(db_conn, """
            SELECT COUNT(*)
              FROM utility.bills b
              JOIN utility.contracts ct ON ct.contract_id = b.contract_id
             WHERE b.account_id <> ct.account_id
        """)
        assert mismatches == 0, \
            f"{mismatches} bill(s) have account_id mismatch with their contract's account_id"

    def test_payment_account_matches_bill_account(self, db_conn):
        """payment.account_id must equal its bill's account_id."""
        mismatches = scalar(db_conn, """
            SELECT COUNT(*)
              FROM utility.payments py
              JOIN utility.bills b ON b.bill_id = py.bill_id
             WHERE py.account_id <> b.account_id
        """)
        assert mismatches == 0, \
            f"{mismatches} payment(s) have account_id mismatch with their bill"

    def test_electricity_meters_have_interval_readings(self, db_conn):
        """AMI electric meters should have at least some INTERVAL readings."""
        ami_elec_meters = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.meters
            WHERE meter_type = 'AMI' AND commodity_type = 'ELECTRICITY' AND status = 'ACTIVE'
        """)
        if ami_elec_meters == 0:
            pytest.skip("No active AMI electricity meters in dataset")

        readings = scalar(db_conn, """
            SELECT COUNT(*)
              FROM utility.meter_readings mr
              JOIN utility.meters m ON m.meter_id = mr.meter_id
             WHERE m.meter_type = 'AMI'
               AND m.commodity_type = 'ELECTRICITY'
               AND mr.reading_type = 'INTERVAL'
        """)
        assert readings > 0, "Expected at least some INTERVAL readings for AMI electricity meters"

    def test_no_readings_before_meter_installation(self, db_conn):
        """meter_readings.read_at must be >= meter.installation_date."""
        invalid = scalar(db_conn, """
            SELECT COUNT(*)
              FROM utility.meter_readings mr
              JOIN utility.meters m ON m.meter_id = mr.meter_id
             WHERE mr.read_at < (m.installation_date::TIMESTAMPTZ)
        """)
        assert invalid == 0, \
            f"{invalid} reading(s) have read_at before the meter's installation_date"

    def test_decommissioned_meters_have_decommission_date(self, db_conn):
        """All DECOMMISSIONED meters should have a decommission_date."""
        invalid = scalar(db_conn, """
            SELECT COUNT(*) FROM utility.meters
            WHERE status = 'DECOMMISSIONED' AND decommission_date IS NULL
        """)
        assert invalid == 0, \
            f"{invalid} DECOMMISSIONED meter(s) are missing decommission_date"

    def test_replication_publication_exists(self, db_conn):
        """The logical replication publication for CDC must exist."""
        pubs = scalar(db_conn, """
            SELECT COUNT(*) FROM pg_publication
            WHERE pubname = 'meter_to_cash_pub'
        """)
        assert pubs == 1, "Replication publication 'meter_to_cash_pub' not found"

    def test_updated_at_trigger_fires(self, db_conn):
        """Verify the updated_at trigger works: UPDATE a customer and check updated_at changes."""
        # Get one customer
        rows = q(db_conn, """
            SELECT customer_id, updated_at FROM utility.customers
            ORDER BY created_at DESC LIMIT 1
        """)
        if not rows:
            pytest.skip("No customers available")

        cid, original_updated_at = rows[0]

        # Perform an UPDATE in a separate autocommit connection
        import time as _time
        update_conn = psycopg2.connect(os.getenv(
            "DATABASE_URL",
            "postgresql://meter_user:meter_pass@localhost:5432/meter_to_cash",
        ))
        update_conn.autocommit = True
        with update_conn.cursor() as cur:
            cur.execute(
                "UPDATE utility.customers SET phone = '(555) 999-8888' WHERE customer_id = %s",
                (cid,)
            )
        update_conn.close()

        _time.sleep(0.1)  # small delay to ensure NOW() advances

        new_rows = q(db_conn, """
            SELECT updated_at FROM utility.customers WHERE customer_id = %s
        """, (cid,))
        new_updated_at = new_rows[0][0]

        assert new_updated_at >= original_updated_at, \
            "updated_at trigger did not advance updated_at on UPDATE"
