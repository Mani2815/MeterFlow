#!/usr/bin/env python3
"""
seed_generator.py
=================
Deterministic synthetic data generator for the Utility Meter-to-Cash platform.

Design invariant — reproducibility
-----------------------------------
Every random choice routes through one of two seeded generators:
  • rng  (random.Random)  – all structural / numeric decisions
  • fake (Faker)          – all human-readable text (names, addresses, etc.)

Both are seeded from SEED before any data is generated.  For a given SEED and
entity counts the output is byte-for-byte identical across runs and machines.

Key rule: for each entity at index i, EXACTLY the same number of rng and fake
calls are made in EXACTLY the same order, regardless of branching logic.
Where a value would be conditionally skipped (e.g. date_of_birth for COMMERCIAL
customers), the generator still calls the underlying function and discards the
result.  This keeps the call sequence constant.

Usage
-----
  # Default scale (10 k customers, 100 k readings):
  python3 scripts/seed_generator.py

  # Full scale:
  NUM_CUSTOMERS=100000 NUM_METER_READINGS=1000000 python3 scripts/seed_generator.py

  # Custom seed:
  SEED=7 NUM_CUSTOMERS=5000 python3 scripts/seed_generator.py

Environment variables
---------------------
  DATABASE_URL           PostgreSQL DSN
  SEED                   Integer random seed (default 42)
  NUM_CUSTOMERS          (default 10000)
  NUM_METER_READINGS     (default 100000)
  BATCH_SIZE             Rows per INSERT batch (default 5000)
"""

from __future__ import annotations

import os
import sys
import uuid
import random
import logging
import time
from datetime import datetime, date, timedelta, timezone
from typing import List, Tuple, NamedTuple

import psycopg2
from psycopg2.extras import execute_values
from faker import Faker
from dotenv import load_dotenv
from tqdm import tqdm

# ── Environment ───────────────────────────────────────────────────────────────
load_dotenv()

SEED               = int(os.getenv("SEED",                 "42"))
NUM_CUSTOMERS      = int(os.getenv("NUM_CUSTOMERS",         "10000"))
NUM_METER_READINGS = int(os.getenv("NUM_METER_READINGS",    "100000"))
BATCH_SIZE         = int(os.getenv("BATCH_SIZE",            "5000"))
DATABASE_URL       = os.getenv(
    "DATABASE_URL",
    "postgresql://meter_user:meter_pass@localhost:5432/meter_to_cash",
)

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("seed_generator")

# ── Random state (seeded before any call) ─────────────────────────────────────
rng = random.Random(SEED)
Faker.seed(SEED)
fake = Faker("en_US")

# ── UUID namespace (fixed constant) ───────────────────────────────────────────
# uuid.uuid5 with a fixed namespace + deterministic name → deterministic UUID.
_NS = uuid.UUID("a1b2c3d4-e5f6-7890-abcd-ef1234567890")


def make_uuid(entity: str, index: int) -> str:
    """Return a deterministic UUID for (entity, SEED, index)."""
    return str(uuid.uuid5(_NS, f"{entity}:{SEED}:{index}"))


# ── Time helpers ──────────────────────────────────────────────────────────────
_TZ = timezone.utc

DT_6Y_AGO = datetime(2018,  1,  1, tzinfo=_TZ)
DT_4Y_AGO = datetime(2020,  1,  1, tzinfo=_TZ)
DT_2Y_AGO = datetime(2022,  7,  1, tzinfo=_TZ)
DT_1Y_AGO = datetime(2023,  1,  1, tzinfo=_TZ)
DT_NOW     = datetime(2025,  6, 30, tzinfo=_TZ)


def rand_dt(start: datetime, end: datetime) -> datetime:
    """Uniform random TIMESTAMPTZ in [start, end)."""
    delta_s = int((end - start).total_seconds())
    return start + timedelta(seconds=rng.randint(0, max(delta_s - 1, 0)))


def rand_date(start: date, end: date) -> date:
    delta = (end - start).days
    return start + timedelta(days=rng.randint(0, max(delta - 1, 0)))


# ── Bulk insert helper ────────────────────────────────────────────────────────

def bulk_insert(conn, table: str, cols: List[str], rows: List[tuple]) -> None:
    """INSERT rows into table using psycopg2 execute_values (fast batch insert)."""
    if not rows:
        return
    col_list = ", ".join(cols)
    sql = f"INSERT INTO {table} ({col_list}) VALUES %s"
    with conn.cursor() as cur:
        execute_values(cur, sql, rows, page_size=BATCH_SIZE)
    conn.commit()


# ── Domain reference data ──────────────────────────────────────────────────────

CUSTOMER_TYPES    = ["RESIDENTIAL"] * 65 + ["COMMERCIAL"] * 25 + ["INDUSTRIAL"] * 10
BILLING_CYCLES    = ["MONTHLY"] * 70  + ["QUARTERLY"] * 20 + ["ANNUAL"] * 10
PAYMENT_METHODS   = ["DIRECT_DEBIT"] * 40 + ["CREDIT_CARD"] * 35 + ["BANK_TRANSFER"] * 20 + ["CHEQUE"] * 5
ACCOUNT_STATUSES  = ["ACTIVE"] * 94  + ["SUSPENDED"] * 4 + ["CLOSED"] * 2

GRID_ZONES        = [f"ZONE-{z}" for z in ["A", "B", "C", "D", "E", "F", "G", "H"]]

COMMODITY_WEIGHTS = {
    "first":  (["ELECTRICITY", "GAS", "WATER"], [80, 15, 5]),
    "second": (["GAS", "WATER"],                [70, 30]),
}

TARIFF_CODES = {
    "ELECTRICITY": ["RESI-FLAT-E1", "RESI-TOU-E2", "COMM-FLAT-CE1", "COMM-TOU-CE2", "IND-DEMAND-IE1"],
    "GAS":         ["RESI-FLAT-G1", "RESI-BUDGET-G2", "COMM-FLAT-CG1", "IND-LARGE-IG1"],
    "WATER":       ["RESI-TIERED-W1", "COMM-FLAT-CW1", "IND-LARGE-IW1"],
}

RATE_CLASSES = {
    "ELECTRICITY": ["R-1", "R-2", "C-1", "C-2", "I-1"],
    "GAS":         ["G-1", "G-2", "GC-1", "GI-1"],
    "WATER":       ["W-1", "WC-1", "WI-1"],
}

UNIT_RATES = {         # USD per unit (approximate realistic values)
    "ELECTRICITY": (0.10, 0.30),
    "GAS":         (0.80, 1.50),
    "WATER":       (0.003, 0.012),
}
STANDING_CHARGES = {
    "ELECTRICITY": (8.0, 20.0),
    "GAS":         (10.0, 25.0),
    "WATER":       (5.0, 15.0),
}

METER_TYPE_WEIGHTS = {
    "ELECTRICITY": (["AMI", "AMR", "MANUAL"], [60, 30, 10]),
    "GAS":         (["AMI", "AMR", "MANUAL"], [20, 50, 30]),
    "WATER":       (["AMI", "AMR", "MANUAL"], [15, 45, 40]),
}

MANUFACTURERS = ["Itron", "Landis+Gyr", "Honeywell", "Elster", "Aclara", "Sensus"]
MODELS = {
    "AMI":    ["RIVA C2SO", "E650", "CF-Series", "Alpha A3", "FOCUS AXR-SD"],
    "AMR":    ["CENTRON II", "OpenWay", "MTX", "GALLUS G4"],
    "MANUAL": ["Classic 3A", "Standard-1", "MechaRead X"],
}

UOM = {
    "ELECTRICITY": "kWh",
    "GAS":         "therms",
    "WATER":       "gallons",
}

# Monthly usage ranges by commodity (units consumed per month)
MONTHLY_USAGE = {
    "ELECTRICITY": (200,  2500),
    "GAS":         (5,    150),
    "WATER":       (1500, 15000),
}

BILL_STATUSES = ["ISSUED"] * 55 + ["PAID"] * 30 + ["OVERDUE"] * 8 + \
                ["PARTIALLY_PAID"] * 4 + ["DISPUTED"] * 2 + ["CANCELLED"] * 1

EMAIL_DOMAINS = [
    "gmail.com", "yahoo.com", "outlook.com", "hotmail.com",
    "icloud.com", "protonmail.com", "company.com", "corp.net",
]

US_STATES = [
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY",
]

# ── Generator functions ────────────────────────────────────────────────────────

class MeterMeta(NamedTuple):
    meter_id:       str
    commodity_type: str
    meter_type:     str
    install_date:   date


def gen_customers(conn, n: int) -> Tuple[List[str], List[str]]:
    """
    Generate n customers.
    Returns (customer_ids, customer_types).
    """
    ids:   List[str] = []
    ctypes: List[str] = []
    batch: List[tuple] = []

    cols = [
        "customer_id", "customer_number", "first_name", "last_name",
        "email", "phone", "customer_type", "date_of_birth",
        "status", "created_at", "updated_at",
    ]

    for i in tqdm(range(n), desc="customers", unit="row", ncols=80):
        cid   = make_uuid("C", i)
        ctype = rng.choice(CUSTOMER_TYPES)

        # — Faker calls are ALWAYS made in this order regardless of ctype —
        fname = fake.first_name()
        lname = fake.last_name()
        dob   = fake.date_of_birth(minimum_age=18, maximum_age=82)  # always called
        phone_raw = fake.numerify(text="(###) ###-####")             # always called

        email = f"{fname.lower()}.{lname.lower()}.{i + 1}@{rng.choice(EMAIL_DOMAINS)}"
        phone = phone_raw if rng.random() > 0.05 else None
        dob_val = dob if ctype == "RESIDENTIAL" else None

        created = rand_dt(DT_6Y_AGO, DT_2Y_AGO)

        ids.append(cid)
        ctypes.append(ctype)
        batch.append((
            cid,
            f"CUST-{i + 1:07d}",
            fname, lname, email, phone,
            ctype, dob_val,
            rng.choices(["ACTIVE", "INACTIVE"], weights=[97, 3])[0],
            created, created,
        ))

        if len(batch) >= BATCH_SIZE:
            bulk_insert(conn, "utility.customers", cols, batch)
            batch = []

    if batch:
        bulk_insert(conn, "utility.customers", cols, batch)

    log.info("  customers: %d rows", n)
    return ids, ctypes


def gen_accounts(
    conn,
    customer_ids:  List[str],
    customer_types: List[str],
    accounts_per_cust: List[int],
) -> Tuple[List[str], List[str], List[str]]:
    """
    Generate accounts.
    Returns (account_ids, parent_customer_ids, account_payment_methods).
    """
    cols = [
        "account_id", "account_number", "customer_id",
        "account_status", "billing_cycle", "payment_method",
        "credit_limit", "deposit_amount", "created_at", "updated_at",
    ]
    ids:      List[str] = []
    cust_map: List[str] = []
    pm_map:   List[str] = []
    batch:    List[tuple] = []
    acct_idx = 0

    for ci, count in enumerate(
        tqdm(accounts_per_cust, desc="accounts ", unit="cust", ncols=80)
    ):
        cust_id   = customer_ids[ci]
        cust_type = customer_types[ci]
        cust_created = None  # not needed for acct creation date

        for _ in range(count):
            aid      = make_uuid("A", acct_idx)
            status   = rng.choices(["ACTIVE", "SUSPENDED", "CLOSED"], weights=[93, 4, 3])[0]
            cycle    = rng.choice(BILLING_CYCLES)
            pm       = rng.choice(PAYMENT_METHODS)
            credit   = round(rng.uniform(0, 2000), 2) if cust_type != "RESIDENTIAL" else 0.0
            deposit  = round(rng.uniform(0, 500),  2) if rng.random() < 0.2 else 0.0
            created  = rand_dt(DT_4Y_AGO, DT_1Y_AGO)

            ids.append(aid)
            cust_map.append(cust_id)
            pm_map.append(pm)
            batch.append((
                aid, f"ACCT-{acct_idx + 1:08d}", cust_id,
                status, cycle, pm,
                credit, deposit, created, created,
            ))
            acct_idx += 1

            if len(batch) >= BATCH_SIZE:
                bulk_insert(conn, "utility.accounts", cols, batch)
                batch = []

    if batch:
        bulk_insert(conn, "utility.accounts", cols, batch)

    log.info("  accounts:  %d rows", len(ids))
    return ids, cust_map, pm_map


def gen_premises(
    conn,
    account_ids:   List[str],
    customer_types: List[str],   # parallel to account_ids (via cust_map)
    cust_types_for_accounts: List[str],
) -> List[str]:
    """
    Generate one premise per account.
    Returns premise_ids.
    """
    cols = [
        "premise_id", "premise_number", "account_id",
        "address_line_1", "address_line_2", "city",
        "state", "postal_code", "country",
        "premise_type", "grid_zone",
        "latitude", "longitude",
        "created_at", "updated_at",
    ]
    ids:   List[str] = []
    batch: List[tuple] = []

    for i, aid in enumerate(
        tqdm(account_ids, desc="premises  ", unit="row", ncols=80)
    ):
        pid     = make_uuid("P", i)
        ptype   = cust_types_for_accounts[i]
        street  = fake.street_address()
        city    = fake.city()
        state   = rng.choice(US_STATES)
        postal  = fake.postcode()
        addr2   = fake.secondary_address() if rng.random() < 0.15 else None
        zone    = rng.choice(GRID_ZONES)
        lat     = round(rng.uniform(25.0, 49.0), 6)
        lon     = round(rng.uniform(-125.0, -66.0), 6)
        created = rand_dt(DT_4Y_AGO, DT_1Y_AGO)

        ids.append(pid)
        batch.append((
            pid, f"PREM-{i + 1:08d}", aid,
            street, addr2, city,
            state, postal, "US",
            ptype, zone,
            lat, lon,
            created, created,
        ))

        if len(batch) >= BATCH_SIZE:
            bulk_insert(conn, "utility.premises", cols, batch)
            batch = []

    if batch:
        bulk_insert(conn, "utility.premises", cols, batch)

    log.info("  premises:  %d rows", len(ids))
    return ids


def gen_contracts(
    conn,
    account_ids:       List[str],
    premise_ids:       List[str],       # parallel to account_ids (1 premise per account)
    contracts_per_acct: List[int],
) -> Tuple[List[str], List[str], List[str], List[date]]:
    """
    Generate contracts.
    Returns (contract_ids, parent_account_ids, commodity_types, start_dates).
    """
    cols = [
        "contract_id", "contract_number", "account_id", "premise_id",
        "tariff_code", "commodity_type", "rate_class",
        "start_date", "end_date", "contract_status",
        "unit_rate", "standing_charge",
        "created_at", "updated_at",
    ]
    ids:        List[str]  = []
    acct_map:   List[str]  = []
    comm_map:   List[str]  = []
    start_map:  List[date] = []
    batch:      List[tuple] = []
    ct_idx = 0

    for ai, count in enumerate(
        tqdm(contracts_per_acct, desc="contracts ", unit="acct", ncols=80)
    ):
        aid    = account_ids[ai]
        pid    = premise_ids[ai]

        # Assign commodity types; if 2 contracts, ensure different commodities
        # Always consume the same number of rng calls regardless of count.
        first_comm  = rng.choices(*COMMODITY_WEIGHTS["first"])[0]
        second_comm = rng.choices(*COMMODITY_WEIGHTS["second"])[0]
        if first_comm == "GAS":
            second_comm = rng.choices(["ELECTRICITY", "WATER"], weights=[80, 20])[0]
        elif first_comm == "WATER":
            second_comm = rng.choices(["ELECTRICITY", "GAS"], weights=[70, 30])[0]
        commodities = [first_comm] if count == 1 else [first_comm, second_comm]

        for ci_local, comm in enumerate(commodities):
            cid     = make_uuid("CT", ct_idx)
            tariff  = rng.choice(TARIFF_CODES[comm])
            rate_c  = rng.choice(RATE_CLASSES[comm])
            lo, hi  = UNIT_RATES[comm]
            u_rate  = round(rng.uniform(lo, hi), 6)
            s_lo, s_hi = STANDING_CHARGES[comm]
            s_charge = round(rng.uniform(s_lo, s_hi), 4)

            start   = rand_date(date(2019, 1, 1), date(2024, 1, 1))
            # 85% open-ended, 15% have an end date
            end_dt_raw = rand_date(start + timedelta(days=365), date(2026, 12, 31))
            has_end = rng.random() < 0.15
            end_dt  = end_dt_raw if has_end else None
            status  = rng.choices(
                ["ACTIVE", "EXPIRED", "TERMINATED", "PENDING"],
                weights=[85, 8, 5, 2]
            )[0]
            created = rand_dt(DT_4Y_AGO, DT_1Y_AGO)

            ids.append(cid)
            acct_map.append(aid)
            comm_map.append(comm)
            start_map.append(start)
            batch.append((
                cid, f"CONT-{ct_idx + 1:08d}", aid, pid,
                tariff, comm, rate_c,
                start, end_dt, status,
                u_rate, s_charge,
                created, created,
            ))
            ct_idx += 1

            if len(batch) >= BATCH_SIZE:
                bulk_insert(conn, "utility.contracts", cols, batch)
                batch = []

        # If count == 1, still "use" the second commodity slot to keep rng aligned.
        # (Already consumed above; second_comm was generated but not appended.)

    if batch:
        bulk_insert(conn, "utility.contracts", cols, batch)

    log.info("  contracts: %d rows", len(ids))
    return ids, acct_map, comm_map, start_map


def gen_service_points(
    conn,
    contract_ids:   List[str],
    premise_ids_for_contracts: List[str],  # derived from contract→account→premise
    commodity_types: List[str],
) -> List[str]:
    """One service point per contract. Returns service_point_ids."""
    cols = [
        "service_point_id", "service_point_number",
        "premise_id", "contract_id", "commodity_type",
        "voltage_class", "phase", "status",
        "created_at", "updated_at",
    ]
    ids:   List[str] = []
    batch: List[tuple] = []

    VOLTAGE_CLASSES = ["120V", "240V", "480V", "12kV", "25kV"]

    for i, (cid, pid, comm) in enumerate(
        tqdm(
            zip(contract_ids, premise_ids_for_contracts, commodity_types),
            desc="svc_points", unit="row", total=len(contract_ids), ncols=80,
        )
    ):
        spid = make_uuid("SP", i)

        # Electrical attributes — always call rng regardless of commodity
        v_class_raw = rng.choice(VOLTAGE_CLASSES)
        phase_raw   = rng.choice([1, 3])
        v_class = v_class_raw if comm == "ELECTRICITY" else None
        phase   = phase_raw   if comm == "ELECTRICITY" else None

        status  = rng.choices(["ACTIVE", "INACTIVE", "DECOMMISSIONED"], weights=[94, 4, 2])[0]
        created = rand_dt(DT_4Y_AGO, DT_1Y_AGO)

        ids.append(spid)
        batch.append((
            spid, f"SP-{i + 1:09d}",
            pid, cid, comm,
            v_class, phase, status,
            created, created,
        ))

        if len(batch) >= BATCH_SIZE:
            bulk_insert(conn, "utility.service_points", cols, batch)
            batch = []

    if batch:
        bulk_insert(conn, "utility.service_points", cols, batch)

    log.info("  svc_points:%d rows", len(ids))
    return ids


def gen_meters(
    conn,
    service_point_ids: List[str],
    commodity_types:   List[str],
    contract_start_dates: List[date],
) -> List[MeterMeta]:
    """One meter per service point. Returns list of MeterMeta for reading generation."""
    cols = [
        "meter_id", "service_point_id",
        "meter_serial_number", "meter_type", "commodity_type",
        "manufacturer", "model", "status",
        "installation_date", "decommission_date",
        "multiplier", "created_at", "updated_at",
    ]
    meta:  List[MeterMeta] = []
    batch: List[tuple]     = []

    for i, (spid, comm, start) in enumerate(
        tqdm(
            zip(service_point_ids, commodity_types, contract_start_dates),
            desc="meters    ", unit="row", total=len(service_point_ids), ncols=80,
        )
    ):
        mid      = make_uuid("M", i)
        mfr      = rng.choice(MANUFACTURERS)
        m_types, m_weights = METER_TYPE_WEIGHTS[comm]
        mtype    = rng.choices(m_types, weights=m_weights)[0]
        model    = rng.choice(MODELS[mtype])
        serial   = f"{mfr[:3].upper()}-{SEED:04d}-{i + 1:07d}"
        status   = rng.choices(
            ["ACTIVE", "INACTIVE", "DECOMMISSIONED", "FAULTY"],
            weights=[90, 5, 3, 2]
        )[0]
        install  = start + timedelta(days=rng.randint(0, 14))
        decomm_raw = install + timedelta(days=rng.randint(365, 1825))
        decomm   = decomm_raw if status == "DECOMMISSIONED" else None
        mult     = rng.choice([1.0, 10.0, 100.0]) if comm == "ELECTRICITY" else 1.0
        created  = datetime.combine(install, datetime.min.time()).replace(tzinfo=_TZ)

        meta.append(MeterMeta(mid, comm, mtype, install))
        batch.append((
            mid, spid,
            serial, mtype, comm,
            mfr, model, status,
            install, decomm,
            mult, created, created,
        ))

        if len(batch) >= BATCH_SIZE:
            bulk_insert(conn, "utility.meters", cols, batch)
            batch = []

    if batch:
        bulk_insert(conn, "utility.meters", cols, batch)

    log.info("  meters:    %d rows", len(meta))
    return meta


def gen_meter_readings(conn, meter_meta: List[MeterMeta], n_readings: int) -> None:
    """
    Distribute n_readings across meters, weighted by meter type:
      AMI  → weight 30 (high-frequency smart meters)
      AMR  → weight 5
      MANUAL → weight 1
    """
    cols = [
        "reading_id", "meter_id",
        "reading_value", "unit_of_measure", "reading_type",
        "read_at", "received_at", "source_system",
        "quality_flag", "created_at",
    ]

    WEIGHTS = {"AMI": 30, "AMR": 5, "MANUAL": 1}
    READING_TYPES = {"AMI": "INTERVAL", "AMR": "INTERVAL", "MANUAL": "CUMULATIVE"}
    QUALITY_CHOICES = (
        ["VALID", "ESTIMATED", "SUSPECT", "REJECTED"],
        [96, 2, 1.5, 0.5],
    )

    # Build a weighted pool of meter indices
    pool_indices: List[int] = []
    for idx, m in enumerate(meter_meta):
        pool_indices.extend([idx] * WEIGHTS[m.meter_type])

    batch:   List[tuple] = []
    total    = 0

    for r in tqdm(range(n_readings), desc="readings  ", unit="row", ncols=80):
        pool_idx = rng.choice(pool_indices)
        m        = meter_meta[pool_idx]

        rid      = make_uuid("R", r)
        uom      = UOM[m.commodity_type]
        rtype    = READING_TYPES[m.meter_type]
        quality  = rng.choices(*QUALITY_CHOICES)[0]

        # Generate realistic reading value
        lo, hi   = MONTHLY_USAGE[m.commodity_type]
        if rtype == "INTERVAL":
            # Hourly interval reading (fraction of monthly usage)
            val = round(rng.uniform(lo / 720, hi / 720), 4)
        else:
            # Cumulative register reading — grows from ~12 months of usage
            val = round(rng.uniform(lo * 12, hi * 12), 4)

        # Read timestamp: install_date to simulation end
        install_dt = datetime.combine(m.install_date, datetime.min.time()).replace(tzinfo=_TZ)
        read_at    = rand_dt(install_dt, DT_NOW)
        recv_lag   = timedelta(seconds=rng.randint(1, 3600))
        received   = read_at + recv_lag

        batch.append((
            rid, m.meter_id,
            val, uom, rtype,
            read_at, received,
            "AMI_SIMULATOR" if m.meter_type == "AMI" else "AMR_COLLECTOR",
            quality, received,
        ))
        total += 1

        if len(batch) >= BATCH_SIZE:
            bulk_insert(conn, "utility.meter_readings", cols, batch)
            batch = []

    if batch:
        bulk_insert(conn, "utility.meter_readings", cols, batch)

    log.info("  readings:  %d rows", total)


def gen_bills(
    conn,
    contract_ids:      List[str],
    account_ids_map:   List[str],   # parallel to contract_ids
    commodity_types:   List[str],   # parallel to contract_ids
    start_dates:       List[date],
    n_periods:         int = 3,
) -> Tuple[List[str], List[str], List[float], List[date]]:
    """
    Generate n_periods monthly bills per contract.
    Returns (bill_ids, account_ids, amounts, due_dates).
    """
    cols = [
        "bill_id", "bill_number", "account_id", "contract_id",
        "bill_date", "due_date", "period_start", "period_end",
        "total_amount", "tax_amount", "usage_amount", "usage_unit",
        "currency", "bill_status", "created_at", "updated_at",
    ]
    ids:      List[str]   = []
    acct_map: List[str]   = []
    amounts:  List[float] = []
    due_dates: List[date] = []
    batch:    List[tuple] = []
    b_idx = 0

    TAX_RATE = 0.08

    for ci, (cid, aid, comm, start) in enumerate(
        tqdm(
            zip(contract_ids, account_ids_map, commodity_types, start_dates),
            desc="bills     ", unit="contract", total=len(contract_ids), ncols=80,
        )
    ):
        lo, hi = MONTHLY_USAGE[comm]
        uom    = UOM[comm]

        for p in range(n_periods):
            # Bill for calendar month p months after contract start
            period_start = date(
                (start.replace(day=1) + timedelta(days=32 * (p + 1))).year,
                (start.replace(day=1) + timedelta(days=32 * (p + 1))).month,
                1,
            )
            period_end   = (period_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
            bill_dt      = period_end + timedelta(days=5)
            due_dt       = bill_dt   + timedelta(days=21)

            usage        = round(rng.uniform(lo, hi), 4)
            # Intentionally always call rng.uniform for tax even when zero
            unit_rate_   = round(rng.uniform(*UNIT_RATES[comm]), 6)
            usage_charge = round(usage * unit_rate_, 4)
            standing_    = round(rng.uniform(*STANDING_CHARGES[comm]), 4)
            subtotal     = round(usage_charge + standing_, 4)
            tax          = round(subtotal * TAX_RATE, 4)
            total        = round(subtotal + tax, 4)

            status       = rng.choice(BILL_STATUSES)
            # Older periods more likely to be paid
            if p < n_periods - 1 and status == "ISSUED":
                status = rng.choices(["PAID", "OVERDUE"], weights=[75, 25])[0]

            bid      = make_uuid("B", b_idx)
            created  = datetime.combine(bill_dt, datetime.min.time()).replace(tzinfo=_TZ)

            ids.append(bid)
            acct_map.append(aid)
            amounts.append(total)
            due_dates.append(due_dt)
            batch.append((
                bid, f"BILL-{b_idx + 1:09d}", aid, cid,
                bill_dt, due_dt, period_start, period_end,
                total, tax, usage, uom,
                "USD", status, created, created,
            ))
            b_idx += 1

            if len(batch) >= BATCH_SIZE:
                bulk_insert(conn, "utility.bills", cols, batch)
                batch = []

    if batch:
        bulk_insert(conn, "utility.bills", cols, batch)

    log.info("  bills:     %d rows", len(ids))
    return ids, acct_map, amounts, due_dates


def gen_payments(
    conn,
    bill_ids:    List[str],
    account_ids: List[str],
    amounts:     List[float],
    due_dates:   List[date],
    pay_rate:    float = 0.88,
) -> None:
    """Generate payments for approximately pay_rate fraction of bills."""
    cols = [
        "payment_id", "payment_reference",
        "bill_id", "account_id",
        "amount", "currency",
        "payment_method", "payment_status",
        "payment_date", "settled_at",
        "notes", "created_at",
    ]
    batch: List[tuple] = []
    p_idx = 0

    PAY_METHODS = ["DIRECT_DEBIT", "CREDIT_CARD", "BANK_TRANSFER", "ONLINE", "CHEQUE", "CASH"]
    PAY_WEIGHTS = [30, 30, 20, 12, 5, 3]

    for bid, aid, amt, due in tqdm(
        zip(bill_ids, account_ids, amounts, due_dates),
        desc="payments  ", unit="row", total=len(bill_ids), ncols=80,
    ):
        # Consume the same rng slot regardless of whether we generate a payment
        pays_this = rng.random() < pay_rate
        pm        = rng.choices(PAY_METHODS, weights=PAY_WEIGHTS)[0]
        days_late = rng.randint(-7, 35)     # negative = paid early
        settled_lag = rng.randint(1, 3)     # business days to settle

        if not pays_this:
            continue

        pid         = make_uuid("PAY", p_idx)
        pay_dt_raw  = datetime.combine(due, datetime.min.time()).replace(tzinfo=_TZ) \
                      + timedelta(days=days_late)
        pay_status  = rng.choices(
            ["CLEARED", "PENDING", "FAILED"],
            weights=[88, 9, 3]
        )[0]
        settled_at  = pay_dt_raw + timedelta(days=settled_lag) \
                      if pay_status == "CLEARED" else None

        # Partial payments: 5% of payments cover only part of the bill
        pay_amount  = round(amt * rng.uniform(0.5, 0.99), 4) if rng.random() < 0.05 else amt

        batch.append((
            pid, f"PAY-REF-{SEED:04d}-{p_idx + 1:09d}",
            bid, aid,
            pay_amount, "USD",
            pm, pay_status,
            pay_dt_raw, settled_at,
            None, pay_dt_raw,
        ))
        p_idx += 1

        if len(batch) >= BATCH_SIZE:
            bulk_insert(conn, "utility.payments", cols, batch)
            batch = []

    if batch:
        bulk_insert(conn, "utility.payments", cols, batch)

    log.info("  payments:  %d rows", p_idx)


# ── Connectivity ──────────────────────────────────────────────────────────────

def wait_for_db(dsn: str, retries: int = 30, delay: float = 2.0) -> psycopg2.extensions.connection:
    """Block until PostgreSQL accepts connections, then return an open connection."""
    log.info("Connecting to database...")
    for attempt in range(1, retries + 1):
        try:
            conn = psycopg2.connect(dsn)
            conn.autocommit = False
            log.info("Connected (attempt %d).", attempt)
            return conn
        except psycopg2.OperationalError as exc:
            log.warning("Not ready yet (%s). Retrying in %.0fs...", exc.__class__.__name__, delay)
            time.sleep(delay)
    log.error("Could not connect after %d attempts. Is Docker running?", retries)
    sys.exit(1)


def already_seeded(conn) -> bool:
    """Return True if the customers table already has rows."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM utility.customers")
        return cur.fetchone()[0] > 0


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    log.info("=" * 60)
    log.info("Meter-to-Cash Seed Generator")
    log.info("  SEED               = %d", SEED)
    log.info("  NUM_CUSTOMERS      = %d", NUM_CUSTOMERS)
    log.info("  NUM_METER_READINGS = %d", NUM_METER_READINGS)
    log.info("  BATCH_SIZE         = %d", BATCH_SIZE)
    log.info("=" * 60)

    conn = wait_for_db(DATABASE_URL)

    if already_seeded(conn):
        log.warning("Database already contains data. Skipping seed.")
        log.warning("To re-seed: make clean && make up && make seed")
        conn.close()
        return

    t0 = time.monotonic()

    # ── Determine entity counts ───────────────────────────────────────────────
    accounts_per_cust = rng.choices([1, 2, 3], weights=[60, 30, 10], k=NUM_CUSTOMERS)
    n_accounts        = sum(accounts_per_cust)

    contracts_per_acct = rng.choices([1, 2], weights=[70, 30], k=n_accounts)
    n_contracts        = sum(contracts_per_acct)

    log.info(
        "Entity plan: customers=%d, accounts=%d, premises=%d, contracts=%d, meters=%d, "
        "readings=%d",
        NUM_CUSTOMERS, n_accounts, n_accounts, n_contracts, n_contracts, NUM_METER_READINGS,
    )

    # ── Generate entities ─────────────────────────────────────────────────────
    customer_ids, customer_types = gen_customers(conn, NUM_CUSTOMERS)

    # Build per-account customer type (for premise_type)
    cust_types_for_accounts: List[str] = []
    for ci, count in enumerate(accounts_per_cust):
        cust_types_for_accounts.extend([customer_types[ci]] * count)

    account_ids, acct_cust_map, acct_pm_map = gen_accounts(
        conn, customer_ids, customer_types, accounts_per_cust
    )

    premise_ids = gen_premises(conn, account_ids, customer_types, cust_types_for_accounts)

    contract_ids, cont_acct_map, commodity_types, start_dates = gen_contracts(
        conn, account_ids, premise_ids, contracts_per_acct
    )

    # Build premise_ids parallel to contract_ids (via account)
    acct_idx_for_contract: List[str] = []
    for ai, count in enumerate(contracts_per_acct):
        acct_idx_for_contract.extend([premise_ids[ai]] * count)

    service_point_ids = gen_service_points(
        conn, contract_ids, acct_idx_for_contract, commodity_types
    )

    meter_meta = gen_meters(conn, service_point_ids, commodity_types, start_dates)

    gen_meter_readings(conn, meter_meta, NUM_METER_READINGS)

    bill_ids, bill_acct_map, bill_amounts, bill_due_dates = gen_bills(
        conn, contract_ids, cont_acct_map, commodity_types, start_dates
    )

    gen_payments(conn, bill_ids, bill_acct_map, bill_amounts, bill_due_dates)

    elapsed = time.monotonic() - t0
    log.info("=" * 60)
    log.info("Seed complete in %.1f seconds.", elapsed)
    log.info("=" * 60)

    conn.close()


if __name__ == "__main__":
    main()
