#!/usr/bin/env python3
"""
cdc_change_generator.py
=======================
Generates a realistic, logged mix of INSERT / UPDATE / DELETE operations
against the utility source database to simulate ongoing operational changes.

Run this AFTER seed_generator.py has completed.
In Phase 2 these changes will be observed as WAL events via Datastream.

Change log
----------
Every change is recorded in a local JSON file (cdc_changes.json) so you can
cross-reference against Datastream events captured in Phase 2.

Usage
-----
  python3 scripts/cdc_change_generator.py

  # Preview what would be changed without touching the DB:
  DRY_RUN=1 python3 scripts/cdc_change_generator.py
"""

from __future__ import annotations

import os
import sys
import uuid
import json
import random
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import psycopg2
import psycopg2.extras
from dotenv import load_dotenv

# ── Environment ───────────────────────────────────────────────────────────────
load_dotenv()

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://meter_user:meter_pass@localhost:5432/meter_to_cash",
)
DRY_RUN = os.getenv("DRY_RUN", "0") == "1"
CDC_SEED = int(os.getenv("CDC_SEED", "99"))          # separate seed for CDC changes
CHANGE_LOG_PATH = os.getenv("CHANGE_LOG", "cdc_changes.json")

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("cdc_generator")

# ── Random state ──────────────────────────────────────────────────────────────
rng = random.Random(CDC_SEED)
_TZ = timezone.utc


# ── Change log ────────────────────────────────────────────────────────────────

class ChangeLog:
    def __init__(self):
        self.entries: List[Dict[str, Any]] = []

    def record(self, operation: str, table: str, pk: str, detail: Dict[str, Any]) -> None:
        self.entries.append({
            "timestamp": datetime.now(_TZ).isoformat(),
            "operation": operation,
            "table": table,
            "pk": pk,
            "detail": detail,
        })
        icon = {"INSERT": "➕", "UPDATE": "✏️ ", "DELETE": "🗑️ "}.get(operation, "?")
        log.info("  %s %-8s utility.%-20s pk=%s", icon, operation, table, pk[:8] + "...")

    def save(self, path: str) -> None:
        with open(path, "w") as f:
            json.dump({"generated_at": datetime.now(_TZ).isoformat(), "changes": self.entries}, f, indent=2)
        log.info("Change log written → %s  (%d entries)", path, len(self.entries))


changelog = ChangeLog()


# ── Helpers ───────────────────────────────────────────────────────────────────

def execute(conn, sql: str, params: tuple = ()) -> List[tuple]:
    """Execute SQL, returning rows for SELECT or [] for DML."""
    if DRY_RUN and not sql.strip().upper().startswith("SELECT"):
        log.debug("[DRY RUN] %s", sql[:120])
        return []
    with conn.cursor() as cur:
        cur.execute(sql, params)
        if cur.description:
            return cur.fetchall()
        return []


def commit(conn) -> None:
    if not DRY_RUN:
        conn.commit()


def sample_ids(conn, table: str, pk_col: str, n: int, where: str = "TRUE") -> List[str]:
    """Return up to n random PKs from table matching where clause."""
    rows = execute(
        conn,
        f"SELECT {pk_col} FROM utility.{table} WHERE {where} ORDER BY random() LIMIT %s",
        (n,),
    )
    return [str(r[0]) for r in rows]


def new_uuid() -> str:
    return str(uuid.uuid4())


# ── Phase 1: INSERTs ──────────────────────────────────────────────────────────

def insert_new_customers(conn, n: int = 10) -> List[str]:
    """Insert n new CDC-test customers with linked accounts, premises, contracts,
    service points, meters (leaf entities needed for reading / deletion tests).
    Returns list of new customer_ids.
    """
    log.info("── Phase 1a: INSERT %d new customers (with full hierarchy)", n)

    EMAIL_DOMAINS = ["testutil.dev", "cdctest.local", "example.net"]
    new_customer_ids: List[str] = []

    for i in range(n):
        cid    = new_uuid()
        ctype  = rng.choice(["RESIDENTIAL", "COMMERCIAL"])
        fname  = rng.choice(["Alice", "Bob", "Carol", "David", "Eve",
                              "Frank", "Grace", "Hank", "Iris", "Jack"])
        lname  = rng.choice(["Testman", "CDCTest", "Changeme", "Newuser", "Deltarow"])
        email  = f"{fname.lower()}.{lname.lower()}.cdc{i}@{rng.choice(EMAIL_DOMAINS)}"

        execute(conn, """
            INSERT INTO utility.customers
              (customer_id, customer_number, first_name, last_name, email,
               customer_type, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE', NOW(), NOW())
        """, (cid, f"CUST-CDC-{i+1:04d}", fname, lname, email, ctype))

        # Account
        aid = new_uuid()
        pm  = rng.choice(["DIRECT_DEBIT", "CREDIT_CARD", "BANK_TRANSFER"])
        execute(conn, """
            INSERT INTO utility.accounts
              (account_id, account_number, customer_id, account_status,
               billing_cycle, payment_method, created_at, updated_at)
            VALUES (%s, %s, %s, 'ACTIVE', 'MONTHLY', %s, NOW(), NOW())
        """, (aid, f"ACCT-CDC-{i+1:04d}", cid, pm))

        # Premise
        pid = new_uuid()
        execute(conn, """
            INSERT INTO utility.premises
              (premise_id, premise_number, account_id, address_line_1,
               city, state, postal_code, country, premise_type, grid_zone,
               created_at, updated_at)
            VALUES (%s, %s, %s, %s, 'Testville', 'CA', '90000', 'US', %s, 'ZONE-T', NOW(), NOW())
        """, (pid, f"PREM-CDC-{i+1:04d}", aid, f"{100 + i} CDC Street", ctype))

        # Contract
        ctid  = new_uuid()
        comm  = rng.choice(["ELECTRICITY", "GAS"])
        execute(conn, """
            INSERT INTO utility.contracts
              (contract_id, contract_number, account_id, premise_id,
               tariff_code, commodity_type, rate_class, start_date,
               contract_status, unit_rate, standing_charge,
               created_at, updated_at)
            VALUES (%s, %s, %s, %s, 'CDC-FLAT-1', %s, 'R-1',
                    CURRENT_DATE - INTERVAL '30 days',
                    'ACTIVE', 0.15, 10.00, NOW(), NOW())
        """, (ctid, f"CONT-CDC-{i+1:04d}", aid, pid, comm))

        # Service Point
        spid = new_uuid()
        execute(conn, """
            INSERT INTO utility.service_points
              (service_point_id, service_point_number, premise_id,
               contract_id, commodity_type, status, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, 'ACTIVE', NOW(), NOW())
        """, (spid, f"SP-CDC-{i+1:05d}", pid, ctid, comm))

        # Meter
        mid = new_uuid()
        execute(conn, """
            INSERT INTO utility.meters
              (meter_id, service_point_id, meter_serial_number,
               meter_type, commodity_type, manufacturer, status,
               installation_date, created_at, updated_at)
            VALUES (%s, %s, %s, 'AMI', %s, 'Itron', 'ACTIVE',
                    CURRENT_DATE - INTERVAL '15 days', NOW(), NOW())
        """, (mid, spid, f"CDC-METER-{i+1:06d}", comm))

        commit(conn)
        new_customer_ids.append(cid)
        changelog.record("INSERT", "customers", cid, {"email": email, "customer_type": ctype})
        changelog.record("INSERT", "accounts",  aid, {"account_number": f"ACCT-CDC-{i+1:04d}"})
        changelog.record("INSERT", "premises",  pid, {"premise_number": f"PREM-CDC-{i+1:04d}"})
        changelog.record("INSERT", "contracts", ctid, {"commodity_type": comm})
        changelog.record("INSERT", "service_points", spid, {})
        changelog.record("INSERT", "meters",    mid, {"meter_serial_number": f"CDC-METER-{i+1:06d}"})

    return new_customer_ids


def insert_new_meter_readings(conn, n: int = 500) -> List[str]:
    """Insert n new meter readings for randomly selected existing meters."""
    log.info("── Phase 1b: INSERT %d new meter readings", n)

    meter_ids = sample_ids(conn, "meters", "meter_id", n * 3,
                           "status = 'ACTIVE'")
    if not meter_ids:
        log.warning("  No active meters found; skipping reading inserts.")
        return []

    # Also fetch commodity types
    rows = execute(conn, """
        SELECT meter_id, commodity_type FROM utility.meters
        WHERE status = 'ACTIVE' ORDER BY random() LIMIT %s
    """, (n * 3,))
    meter_comm = {str(r[0]): r[1] for r in rows}

    UOM = {"ELECTRICITY": "kWh", "GAS": "therms", "WATER": "gallons"}
    new_reading_ids: List[str] = []

    for i in range(n):
        mid   = rng.choice(list(meter_comm.keys()))
        comm  = meter_comm[mid]
        rid   = new_uuid()
        val   = round(rng.uniform(0.1, 50.0), 4)
        read_at = datetime.now(_TZ) - timedelta(minutes=rng.randint(1, 60))
        quality = rng.choices(
            ["VALID", "ESTIMATED", "SUSPECT"],
            weights=[95, 3, 2]
        )[0]

        execute(conn, """
            INSERT INTO utility.meter_readings
              (reading_id, meter_id, reading_value, unit_of_measure,
               reading_type, read_at, received_at, source_system,
               quality_flag, created_at)
            VALUES (%s, %s, %s, %s, 'INTERVAL', %s, NOW(),
                    'CDC_GENERATOR', %s, NOW())
        """, (rid, mid, val, UOM.get(comm, "kWh"), read_at, quality))

        if i % 100 == 0:
            commit(conn)

        new_reading_ids.append(rid)
        changelog.record("INSERT", "meter_readings", rid,
                         {"meter_id": mid[:8], "reading_value": val, "quality_flag": quality})

    commit(conn)
    return new_reading_ids


# ── Phase 2: UPDATEs ──────────────────────────────────────────────────────────

def update_customer_contacts(conn, n: int = 20) -> None:
    """Update email and phone for n random customers (contact-change event)."""
    log.info("── Phase 2a: UPDATE %d customer contacts (email / phone)", n)
    ids = sample_ids(conn, "customers", "customer_id", n)

    NEW_DOMAINS = ["newmail.com", "updated-email.net", "changedemail.org"]
    for cid in ids:
        new_email = f"updated.{cid[:6]}@{rng.choice(NEW_DOMAINS)}"
        new_phone = f"(555) {rng.randint(100, 999)}-{rng.randint(1000, 9999)}"
        execute(conn, """
            UPDATE utility.customers
               SET email = %s, phone = %s
             WHERE customer_id = %s
        """, (new_email, new_phone, cid))
        changelog.record("UPDATE", "customers", cid,
                         {"field": "email,phone", "new_email": new_email})

    commit(conn)


def suspend_then_reactivate_accounts(conn) -> None:
    """Suspend 8 accounts, then immediately reactivate 5 of them.
    Tests that Datastream captures both UPDATE events.
    """
    log.info("── Phase 2b: UPDATE account_status → SUSPENDED then re-ACTIVE")
    ids = sample_ids(conn, "accounts", "account_id", 8, "account_status = 'ACTIVE'")

    for aid in ids:
        execute(conn, """
            UPDATE utility.accounts SET account_status = 'SUSPENDED' WHERE account_id = %s
        """, (aid,))
        changelog.record("UPDATE", "accounts", aid, {"account_status": "SUSPENDED"})

    commit(conn)

    # Reactivate 5 of them
    for aid in ids[:5]:
        execute(conn, """
            UPDATE utility.accounts SET account_status = 'ACTIVE' WHERE account_id = %s
        """, (aid,))
        changelog.record("UPDATE", "accounts", aid, {"account_status": "ACTIVE"})

    commit(conn)


def terminate_contracts(conn, n: int = 5) -> None:
    """Terminate n active contracts — sets status + end_date."""
    log.info("── Phase 2c: UPDATE %d contracts → TERMINATED", n)
    ids = sample_ids(conn, "contracts", "contract_id", n, "contract_status = 'ACTIVE'")

    for cid in ids:
        execute(conn, """
            UPDATE utility.contracts
               SET contract_status = 'TERMINATED',
                   end_date = CURRENT_DATE
             WHERE contract_id = %s
        """, (cid,))
        changelog.record("UPDATE", "contracts", cid,
                         {"contract_status": "TERMINATED", "end_date": "CURRENT_DATE"})

    commit(conn)


def decommission_meters(conn, n: int = 3) -> List[str]:
    """Decommission n meters — key event that triggers reading cascade in Phase 3."""
    log.info("── Phase 2d: UPDATE %d meters → DECOMMISSIONED", n)
    ids = sample_ids(conn, "meters", "meter_id", n, "status = 'ACTIVE'")

    for mid in ids:
        execute(conn, """
            UPDATE utility.meters
               SET status = 'DECOMMISSIONED',
                   decommission_date = CURRENT_DATE
             WHERE meter_id = %s
        """, (mid,))
        changelog.record("UPDATE", "meters", mid,
                         {"status": "DECOMMISSIONED", "decommission_date": "CURRENT_DATE"})

    commit(conn)
    return ids


def mark_bills_paid(conn, n: int = 50) -> List[str]:
    """Transition n ISSUED or OVERDUE bills → PAID."""
    log.info("── Phase 2e: UPDATE %d bills → PAID", n)
    rows = execute(conn, """
        SELECT bill_id, account_id, total_amount, due_date
          FROM utility.bills
         WHERE bill_status IN ('ISSUED', 'OVERDUE')
         ORDER BY random()
         LIMIT %s
    """, (n,))

    if not rows:
        log.warning("  No open bills found.")
        return []

    bill_ids = []
    for bill_id, account_id, total_amount, due_date in rows:
        execute(conn, """
            UPDATE utility.bills SET bill_status = 'PAID' WHERE bill_id = %s
        """, (str(bill_id),))
        changelog.record("UPDATE", "bills", str(bill_id), {"bill_status": "PAID"})
        bill_ids.append(str(bill_id))

    commit(conn)
    return bill_ids


def insert_payments_for_paid_bills(conn, bill_ids: List[str]) -> List[str]:
    """Create payment records for bills just marked PAID."""
    log.info("── Phase 2f: INSERT %d payments for newly-paid bills", len(bill_ids))
    if not bill_ids:
        return []

    payment_ids = []
    for bid in bill_ids:
        rows = execute(conn, """
            SELECT b.account_id, b.total_amount, b.due_date
              FROM utility.bills b
             WHERE b.bill_id = %s
        """, (bid,))
        if not rows:
            continue

        aid, amount, due_date = rows[0]
        pid    = new_uuid()
        pm     = rng.choice(["DIRECT_DEBIT", "CREDIT_CARD", "ONLINE"])
        pay_dt = datetime.now(_TZ) - timedelta(days=rng.randint(1, 5))
        settled = pay_dt + timedelta(days=rng.randint(1, 3))
        ref    = f"AUTOPAY-{pid[:12].upper()}"

        execute(conn, """
            INSERT INTO utility.payments
              (payment_id, payment_reference, bill_id, account_id,
               amount, currency, payment_method, payment_status,
               payment_date, settled_at, created_at)
            VALUES (%s, %s, %s, %s, %s, 'USD', %s, 'CLEARED', %s, %s, NOW())
        """, (pid, ref, bid, str(aid), float(amount), pm, pay_dt, settled))

        payment_ids.append(pid)
        changelog.record("INSERT", "payments", pid,
                         {"bill_id": bid[:8], "amount": float(amount), "payment_method": pm})

    commit(conn)
    return payment_ids


# ── Phase 3: DELETEs ──────────────────────────────────────────────────────────

def delete_failed_payments(conn, n: int = 10) -> None:
    """Hard-delete FAILED payment records — payments have no dependents."""
    log.info("── Phase 3a: DELETE %d FAILED payments", n)
    ids = sample_ids(conn, "payments", "payment_id", n, "payment_status = 'FAILED'")

    if not ids:
        log.warning("  No FAILED payments found; inserting test ones first.")
        # Create some test FAILED payments to delete
        rows = execute(conn, """
            SELECT b.bill_id, b.account_id, b.total_amount
              FROM utility.bills b
             WHERE b.bill_status != 'CANCELLED'
             ORDER BY random() LIMIT %s
        """, (n,))
        for bill_id, account_id, total_amount in rows:
            pid = new_uuid()
            execute(conn, """
                INSERT INTO utility.payments
                  (payment_id, payment_reference, bill_id, account_id,
                   amount, currency, payment_method, payment_status,
                   payment_date, created_at)
                VALUES (%s, %s, %s, %s, %s, 'USD', 'DIRECT_DEBIT', 'FAILED',
                        NOW() - INTERVAL '1 day', NOW())
            """, (pid, f"FAILED-TEST-{pid[:8]}", str(bill_id), str(account_id), float(total_amount)))
            ids.append(pid)
        commit(conn)

    for pid in ids[:n]:
        execute(conn, "DELETE FROM utility.payments WHERE payment_id = %s", (pid,))
        changelog.record("DELETE", "payments", pid, {"reason": "FAILED payment cleanup"})

    commit(conn)


def delete_suspect_readings(conn, n: int = 30) -> None:
    """Hard-delete REJECTED quality meter readings — demonstrates reading DELETEs."""
    log.info("── Phase 3b: DELETE %d REJECTED / SUSPECT meter readings", n)
    ids = sample_ids(conn, "meter_readings", "reading_id", n,
                     "quality_flag IN ('REJECTED', 'SUSPECT')")

    if not ids:
        log.warning("  No suspect readings found; skipping.")
        return

    for rid in ids:
        execute(conn, "DELETE FROM utility.meter_readings WHERE reading_id = %s", (rid,))
        changelog.record("DELETE", "meter_readings", rid, {"reason": "quality_flag = SUSPECT/REJECTED"})

    commit(conn)


# ── Connectivity ──────────────────────────────────────────────────────────────

def connect(dsn: str, retries: int = 15, delay: float = 2.0):
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(dsn)
            conn.autocommit = False
            return conn
        except psycopg2.OperationalError as exc:
            log.warning("DB not ready (%s). Retry %d/%d...", exc.__class__.__name__, attempt, retries)
            time.sleep(delay)
    log.error("Cannot connect to database.")
    sys.exit(1)


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    if DRY_RUN:
        log.info("DRY RUN mode — no changes will be committed.")

    log.info("=" * 60)
    log.info("Meter-to-Cash CDC Change Generator  (CDC_SEED=%d)", CDC_SEED)
    log.info("=" * 60)

    conn = connect(DATABASE_URL)

    # Verify data exists
    rows = execute(conn, "SELECT COUNT(*) FROM utility.customers")
    n_cust = rows[0][0] if rows else 0
    if n_cust == 0:
        log.error("No data found. Run seed_generator.py first.")
        sys.exit(1)
    log.info("Source DB has %d customers. Starting CDC changes...", n_cust)

    # ── Phase 1: INSERTs ─────────────────────────────────────────────────────
    insert_new_customers(conn, n=10)
    insert_new_meter_readings(conn, n=500)

    # ── Phase 2: UPDATEs ─────────────────────────────────────────────────────
    update_customer_contacts(conn, n=20)
    suspend_then_reactivate_accounts(conn)
    terminate_contracts(conn, n=5)
    decommission_meters(conn, n=3)
    paid_bill_ids = mark_bills_paid(conn, n=50)
    insert_payments_for_paid_bills(conn, paid_bill_ids)

    # ── Phase 3: DELETEs ─────────────────────────────────────────────────────
    delete_failed_payments(conn, n=10)
    delete_suspect_readings(conn, n=30)

    changelog.save(CHANGE_LOG_PATH)

    log.info("=" * 60)
    log.info("CDC changes complete. %d events logged to %s", len(changelog.entries), CHANGE_LOG_PATH)
    log.info("")
    log.info("To verify in psql:")
    log.info("  SELECT * FROM utility.customers WHERE customer_number LIKE 'CUST-CDC-%%';")
    log.info("  SELECT * FROM utility.accounts  WHERE account_status = 'SUSPENDED';")
    log.info("  SELECT * FROM utility.contracts WHERE contract_status = 'TERMINATED';")
    log.info("  SELECT * FROM utility.meters    WHERE status = 'DECOMMISSIONED';")
    log.info("=" * 60)

    conn.close()


if __name__ == "__main__":
    main()
