-- V003__indexes.sql
-- Secondary indexes for operational query patterns and CDC watermark columns.
-- Primary keys already have implicit B-tree indexes; this file adds the rest.

-- ── customers ─────────────────────────────────────────────────────────────────
CREATE INDEX idx_customers_customer_number ON utility.customers(customer_number);
CREATE INDEX idx_customers_email           ON utility.customers(email);
CREATE INDEX idx_customers_status          ON utility.customers(status);
CREATE INDEX idx_customers_customer_type   ON utility.customers(customer_type);
-- Watermark index: Datastream uses updated_at for incremental sync ordering
CREATE INDEX idx_customers_updated_at      ON utility.customers(updated_at);

-- ── accounts ──────────────────────────────────────────────────────────────────
CREATE INDEX idx_accounts_customer_id   ON utility.accounts(customer_id);
CREATE INDEX idx_accounts_account_number ON utility.accounts(account_number);
CREATE INDEX idx_accounts_status        ON utility.accounts(account_status);
CREATE INDEX idx_accounts_updated_at    ON utility.accounts(updated_at);

-- ── premises ──────────────────────────────────────────────────────────────────
CREATE INDEX idx_premises_account_id  ON utility.premises(account_id);
CREATE INDEX idx_premises_postal_code ON utility.premises(postal_code);
CREATE INDEX idx_premises_state       ON utility.premises(state);
CREATE INDEX idx_premises_updated_at  ON utility.premises(updated_at);

-- ── contracts ─────────────────────────────────────────────────────────────────
CREATE INDEX idx_contracts_account_id     ON utility.contracts(account_id);
CREATE INDEX idx_contracts_premise_id     ON utility.contracts(premise_id);
CREATE INDEX idx_contracts_status         ON utility.contracts(contract_status);
CREATE INDEX idx_contracts_commodity_type ON utility.contracts(commodity_type);
CREATE INDEX idx_contracts_start_date     ON utility.contracts(start_date);
CREATE INDEX idx_contracts_updated_at     ON utility.contracts(updated_at);

-- ── service_points ────────────────────────────────────────────────────────────
CREATE INDEX idx_service_points_premise_id    ON utility.service_points(premise_id);
CREATE INDEX idx_service_points_contract_id   ON utility.service_points(contract_id);
CREATE INDEX idx_service_points_commodity_type ON utility.service_points(commodity_type);
CREATE INDEX idx_service_points_updated_at    ON utility.service_points(updated_at);

-- ── meters ────────────────────────────────────────────────────────────────────
CREATE INDEX idx_meters_service_point_id    ON utility.meters(service_point_id);
CREATE INDEX idx_meters_meter_serial_number ON utility.meters(meter_serial_number);
CREATE INDEX idx_meters_status              ON utility.meters(status);
CREATE INDEX idx_meters_meter_type          ON utility.meters(meter_type);
CREATE INDEX idx_meters_installation_date   ON utility.meters(installation_date);
CREATE INDEX idx_meters_updated_at          ON utility.meters(updated_at);

-- ── meter_readings ────────────────────────────────────────────────────────────
-- Composite (meter_id, read_at DESC) is the primary operational index:
-- used by queries like "latest N readings for a meter".
CREATE INDEX idx_meter_readings_meter_read_at
    ON utility.meter_readings(meter_id, read_at DESC);

CREATE INDEX idx_meter_readings_read_at    ON utility.meter_readings(read_at);
CREATE INDEX idx_meter_readings_quality_flag ON utility.meter_readings(quality_flag)
    WHERE quality_flag != 'VALID';   -- partial index; only suspect/rejected rows
CREATE INDEX idx_meter_readings_created_at ON utility.meter_readings(created_at);

-- ── bills ─────────────────────────────────────────────────────────────────────
CREATE INDEX idx_bills_account_id   ON utility.bills(account_id);
CREATE INDEX idx_bills_contract_id  ON utility.bills(contract_id);
CREATE INDEX idx_bills_bill_date    ON utility.bills(bill_date);
CREATE INDEX idx_bills_due_date     ON utility.bills(due_date);
CREATE INDEX idx_bills_status       ON utility.bills(bill_status);
-- Partial index: operational queries focus on open (unpaid) bills
CREATE INDEX idx_bills_open         ON utility.bills(due_date, account_id)
    WHERE bill_status IN ('ISSUED', 'OVERDUE', 'PARTIALLY_PAID');
CREATE INDEX idx_bills_updated_at   ON utility.bills(updated_at);

-- ── payments ──────────────────────────────────────────────────────────────────
CREATE INDEX idx_payments_bill_id        ON utility.payments(bill_id);
CREATE INDEX idx_payments_account_id     ON utility.payments(account_id);
CREATE INDEX idx_payments_payment_date   ON utility.payments(payment_date);
CREATE INDEX idx_payments_payment_status ON utility.payments(payment_status);
CREATE INDEX idx_payments_settled_at     ON utility.payments(settled_at)
    WHERE settled_at IS NOT NULL;  -- partial: only settled payments
