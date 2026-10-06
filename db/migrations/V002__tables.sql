-- V002__tables.sql
-- Core schema: all 9 operational tables for the Meter-to-Cash domain.
-- Relationship chain:
--   customers → accounts → (premises, contracts) → service_points → meters
--                                                       → meter_readings
--   accounts + contracts → bills → payments

-- ═══════════════════════════════════════════════════════════════════════════════
-- 1. CUSTOMERS
--    Master record for an individual or organisation that holds utility services.
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE utility.customers (
    customer_id     UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Human-readable reference printed on correspondence (e.g. CUST-0000001)
    customer_number VARCHAR(20)  UNIQUE NOT NULL,
    first_name      VARCHAR(100) NOT NULL,
    last_name       VARCHAR(100) NOT NULL,
    -- email is operationally unique in the CRM but we use a UNIQUE index (not
    -- constraint) to allow the CDC generator to demonstrate duplicate-email errors
    -- being caught at the application layer rather than the DB layer.
    email           VARCHAR(255) NOT NULL,
    phone           VARCHAR(30),
    customer_type   VARCHAR(20)  NOT NULL
        CHECK (customer_type IN ('RESIDENTIAL', 'COMMERCIAL', 'INDUSTRIAL')),
    date_of_birth   DATE,
    status          VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'INACTIVE', 'DECEASED')),
    -- Timestamps use TIMESTAMPTZ so CDC events carry correct UTC offset.
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_customers_updated_at
    BEFORE UPDATE ON utility.customers
    FOR EACH ROW EXECUTE FUNCTION utility.set_updated_at();

COMMENT ON TABLE  utility.customers IS 'Master customer registry; one row per person or organisation.';
COMMENT ON COLUMN utility.customers.customer_number IS 'Human-readable ID printed on bills and correspondence.';
COMMENT ON COLUMN utility.customers.customer_type   IS 'RESIDENTIAL | COMMERCIAL | INDUSTRIAL';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 2. ACCOUNTS
--    Billing account linking a customer to their utility services.
--    One customer may hold multiple accounts (e.g. home + business).
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE utility.accounts (
    account_id      UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    account_number  VARCHAR(30)  UNIQUE NOT NULL,
    customer_id     UUID         NOT NULL
        REFERENCES utility.customers(customer_id) ON DELETE RESTRICT,
    account_status  VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE'
        CHECK (account_status IN ('ACTIVE', 'SUSPENDED', 'CLOSED')),
    billing_cycle   VARCHAR(20)  NOT NULL DEFAULT 'MONTHLY'
        CHECK (billing_cycle IN ('MONTHLY', 'QUARTERLY', 'ANNUAL')),
    payment_method  VARCHAR(30)  NOT NULL
        CHECK (payment_method IN ('DIRECT_DEBIT', 'CREDIT_CARD', 'CHEQUE', 'BANK_TRANSFER')),
    -- Credit limit in account currency; 0 = pay-in-advance
    credit_limit    NUMERIC(12,2) NOT NULL DEFAULT 0.00 CHECK (credit_limit >= 0),
    deposit_amount  NUMERIC(12,2) NOT NULL DEFAULT 0.00 CHECK (deposit_amount >= 0),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_accounts_updated_at
    BEFORE UPDATE ON utility.accounts
    FOR EACH ROW EXECUTE FUNCTION utility.set_updated_at();

COMMENT ON TABLE utility.accounts IS 'Billing account; FK to customers. Status changes drive SUSPENDED CDC events.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 3. PREMISES
--    Physical address where utility service is delivered.
--    One account typically has one premise; large commercial customers may have
--    several accounts each covering a different premise.
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE utility.premises (
    premise_id      UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    premise_number  VARCHAR(30)   UNIQUE NOT NULL,
    -- The account responsible for service at this premise
    account_id      UUID          NOT NULL
        REFERENCES utility.accounts(account_id) ON DELETE RESTRICT,
    address_line_1  VARCHAR(255)  NOT NULL,
    address_line_2  VARCHAR(255),
    city            VARCHAR(100)  NOT NULL,
    state           CHAR(2)       NOT NULL,
    postal_code     VARCHAR(10)   NOT NULL,
    country         CHAR(2)       NOT NULL DEFAULT 'US',
    premise_type    VARCHAR(20)   NOT NULL
        CHECK (premise_type IN ('RESIDENTIAL', 'COMMERCIAL', 'INDUSTRIAL')),
    -- Grid zone code used by the distribution operator (e.g. ZONE-A, ZONE-7)
    grid_zone       VARCHAR(20),
    -- Optional geo-coordinates for mapping dashboards
    latitude        NUMERIC(9, 6),
    longitude       NUMERIC(9, 6),
    created_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_premises_updated_at
    BEFORE UPDATE ON utility.premises
    FOR EACH ROW EXECUTE FUNCTION utility.set_updated_at();

COMMENT ON TABLE utility.premises IS 'Physical service address. One premise per account in this simulation.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 4. CONTRACTS
--    Service agreement specifying commodity, tariff, and effective dates.
--    An account may have multiple contracts (electricity + gas at same premise).
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE utility.contracts (
    contract_id     UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    contract_number VARCHAR(30)  UNIQUE NOT NULL,
    account_id      UUID         NOT NULL
        REFERENCES utility.accounts(account_id) ON DELETE RESTRICT,
    premise_id      UUID         NOT NULL
        REFERENCES utility.premises(premise_id) ON DELETE RESTRICT,
    -- Tariff code determines the pricing schedule, e.g. RESI-FLAT-E1
    tariff_code     VARCHAR(50)  NOT NULL,
    commodity_type  VARCHAR(20)  NOT NULL
        CHECK (commodity_type IN ('ELECTRICITY', 'GAS', 'WATER')),
    rate_class      VARCHAR(30)  NOT NULL,
    start_date      DATE         NOT NULL,
    -- NULL end_date = open-ended (active) contract
    end_date        DATE,
    contract_status VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE'
        CHECK (contract_status IN ('ACTIVE', 'EXPIRED', 'TERMINATED', 'PENDING')),
    -- Agreed unit rate in USD per commodity unit
    unit_rate       NUMERIC(10, 6) NOT NULL CHECK (unit_rate > 0),
    -- Fixed monthly standing charge in USD
    standing_charge NUMERIC(10, 4) NOT NULL DEFAULT 0.0 CHECK (standing_charge >= 0),
    created_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_contracts_end_after_start
        CHECK (end_date IS NULL OR end_date > start_date)
);

CREATE TRIGGER trg_contracts_updated_at
    BEFORE UPDATE ON utility.contracts
    FOR EACH ROW EXECUTE FUNCTION utility.set_updated_at();

COMMENT ON TABLE utility.contracts IS 'Service contract: links account + premise, holds tariff and pricing.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 5. SERVICE POINTS
--    The physical delivery point for a single commodity at a premise.
--    One service point per contract (ELECTRICITY at a premise ≠ GAS at same premise).
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE utility.service_points (
    service_point_id     UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    service_point_number VARCHAR(30)  UNIQUE NOT NULL,
    premise_id           UUID         NOT NULL
        REFERENCES utility.premises(premise_id) ON DELETE RESTRICT,
    contract_id          UUID         NOT NULL UNIQUE
        REFERENCES utility.contracts(contract_id) ON DELETE RESTRICT,
    commodity_type       VARCHAR(20)  NOT NULL
        CHECK (commodity_type IN ('ELECTRICITY', 'GAS', 'WATER')),
    -- Electrical characteristics (NULL for non-electric commodities)
    voltage_class        VARCHAR(20),
    phase                SMALLINT     CHECK (phase IN (1, 3)),
    status               VARCHAR(20)  NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'INACTIVE', 'DECOMMISSIONED')),
    created_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    updated_at           TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TRIGGER trg_service_points_updated_at
    BEFORE UPDATE ON utility.service_points
    FOR EACH ROW EXECUTE FUNCTION utility.set_updated_at();

COMMENT ON TABLE utility.service_points IS 'Delivery point for one commodity at one premise. 1:1 with contracts.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 6. METERS
--    Physical metering device installed at a service point.
--    Meter type determines reading frequency and CDC change patterns.
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE utility.meters (
    meter_id            UUID          PRIMARY KEY DEFAULT gen_random_uuid(),
    service_point_id    UUID          NOT NULL UNIQUE
        REFERENCES utility.service_points(service_point_id) ON DELETE RESTRICT,
    -- Manufacturer's serial number; the natural key used in AMI messages
    meter_serial_number VARCHAR(50)   UNIQUE NOT NULL,
    meter_type          VARCHAR(20)   NOT NULL
        CHECK (meter_type IN ('AMI', 'AMR', 'MANUAL')),
    commodity_type      VARCHAR(20)   NOT NULL
        CHECK (commodity_type IN ('ELECTRICITY', 'GAS', 'WATER')),
    manufacturer        VARCHAR(100),
    model               VARCHAR(100),
    status              VARCHAR(20)   NOT NULL DEFAULT 'ACTIVE'
        CHECK (status IN ('ACTIVE', 'INACTIVE', 'DECOMMISSIONED', 'FAULTY')),
    installation_date   DATE          NOT NULL,
    decommission_date   DATE,
    -- Reading multiplier applied to raw register value (default 1.0)
    multiplier          NUMERIC(10,4) NOT NULL DEFAULT 1.0 CHECK (multiplier > 0),
    created_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ   NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_meters_decommission_date
        CHECK (decommission_date IS NULL OR decommission_date >= installation_date)
);

CREATE TRIGGER trg_meters_updated_at
    BEFORE UPDATE ON utility.meters
    FOR EACH ROW EXECUTE FUNCTION utility.set_updated_at();

COMMENT ON TABLE utility.meters IS 'Physical metering device. Status changes (e.g. ACTIVE→DECOMMISSIONED) are key CDC events.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 7. METER READINGS
--    Time-series measurements produced by meters.
--    This is the highest-volume table. In Phase 2 it will be fed via Pub/Sub.
--    ON DELETE CASCADE allows the CDC change generator to hard-delete a meter
--    and observe the cascaded reading deletes via Datastream.
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE utility.meter_readings (
    reading_id      UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    meter_id        UUID           NOT NULL
        REFERENCES utility.meters(meter_id) ON DELETE CASCADE,
    -- Cumulative register value (kWh, therms, etc.) – never negative
    reading_value   NUMERIC(15, 4) NOT NULL CHECK (reading_value >= 0),
    unit_of_measure VARCHAR(20)    NOT NULL
        CHECK (unit_of_measure IN ('kWh', 'therms', 'CCF', 'm3', 'gallons', 'kW')),
    reading_type    VARCHAR(20)    NOT NULL
        CHECK (reading_type IN ('INTERVAL', 'CUMULATIVE', 'MANUAL', 'ESTIMATED')),
    -- Device-clock timestamp; the authoritative measurement time
    read_at         TIMESTAMPTZ    NOT NULL,
    -- Time the reading arrived at the collection system
    received_at     TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    source_system   VARCHAR(100)   NOT NULL DEFAULT 'AMI_SIMULATOR',
    quality_flag    VARCHAR(20)    NOT NULL DEFAULT 'VALID'
        CHECK (quality_flag IN ('VALID', 'ESTIMATED', 'SUSPECT', 'REJECTED')),
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW()
    -- No updated_at: readings are immutable once written.
    -- Corrections create a new row with quality_flag = ESTIMATED.
);

COMMENT ON TABLE utility.meter_readings IS 'Immutable time-series fact. Append-only; corrections create new rows.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 8. BILLS
--    Periodic invoice generated by the billing engine for a contract.
--    bill_status transitions (ISSUED → PAID/OVERDUE) are prime CDC events.
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE utility.bills (
    bill_id         UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_number     VARCHAR(30)    UNIQUE NOT NULL,
    account_id      UUID           NOT NULL
        REFERENCES utility.accounts(account_id) ON DELETE RESTRICT,
    contract_id     UUID           NOT NULL
        REFERENCES utility.contracts(contract_id) ON DELETE RESTRICT,
    bill_date       DATE           NOT NULL,
    due_date        DATE           NOT NULL,
    period_start    DATE           NOT NULL,
    period_end      DATE           NOT NULL,
    total_amount    NUMERIC(12, 4) NOT NULL CHECK (total_amount >= 0),
    tax_amount      NUMERIC(12, 4) NOT NULL DEFAULT 0.0 CHECK (tax_amount >= 0),
    -- Commodity units consumed in this billing period
    usage_amount    NUMERIC(15, 4),
    usage_unit      VARCHAR(20),
    currency        CHAR(3)        NOT NULL DEFAULT 'USD',
    bill_status     VARCHAR(20)    NOT NULL DEFAULT 'ISSUED'
        CHECK (bill_status IN ('ISSUED', 'PAID', 'OVERDUE', 'CANCELLED', 'DISPUTED', 'PARTIALLY_PAID')),
    created_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ    NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_bills_period_valid
        CHECK (period_end > period_start),
    CONSTRAINT chk_bills_due_after_issue
        CHECK (due_date >= bill_date)
);

CREATE TRIGGER trg_bills_updated_at
    BEFORE UPDATE ON utility.bills
    FOR EACH ROW EXECUTE FUNCTION utility.set_updated_at();

COMMENT ON TABLE utility.bills IS 'Invoice per contract per billing period. bill_status is the primary mutable field.';

-- ═══════════════════════════════════════════════════════════════════════════════
-- 9. PAYMENTS
--    A payment transaction applied against a bill.
--    Reversals are new rows (payment_status = REVERSED), not in-place updates.
-- ═══════════════════════════════════════════════════════════════════════════════
CREATE TABLE utility.payments (
    payment_id        UUID           PRIMARY KEY DEFAULT gen_random_uuid(),
    -- External payment reference (bank transaction ID, cheque number, etc.)
    payment_reference VARCHAR(50)    UNIQUE NOT NULL,
    bill_id           UUID           NOT NULL
        REFERENCES utility.bills(bill_id) ON DELETE RESTRICT,
    account_id        UUID           NOT NULL
        REFERENCES utility.accounts(account_id) ON DELETE RESTRICT,
    amount            NUMERIC(12, 4) NOT NULL CHECK (amount > 0),
    currency          CHAR(3)        NOT NULL DEFAULT 'USD',
    payment_method    VARCHAR(30)    NOT NULL
        CHECK (payment_method IN ('DIRECT_DEBIT', 'CREDIT_CARD', 'CHEQUE', 'BANK_TRANSFER', 'ONLINE', 'CASH')),
    payment_status    VARCHAR(20)    NOT NULL DEFAULT 'PENDING'
        CHECK (payment_status IN ('PENDING', 'CLEARED', 'REVERSED', 'FAILED', 'REFUNDED')),
    -- Customer-initiated timestamp
    payment_date      TIMESTAMPTZ    NOT NULL,
    -- Fund-settlement timestamp; NULL until bank confirms
    settled_at        TIMESTAMPTZ,
    notes             TEXT,
    created_at        TIMESTAMPTZ    NOT NULL DEFAULT NOW()
    -- No updated_at: status changes (reversals) produce new rows per business rule.
);

COMMENT ON TABLE utility.payments IS 'Payment transaction against a bill. Reversals are new rows, not updates.';
