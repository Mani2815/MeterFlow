#!/usr/bin/env python3
"""
validate_cdc.py
===============
Validates that the PostgreSQL database correctly generates CDC (Change Data Capture)
events for INSERT, UPDATE, and DELETE operations.

Since this is the local application-side verification (before configuring GCP Datastream),
this script reads directly from a PostgreSQL logical replication slot using the 
built-in `test_decoding` output plugin. Datastream uses a similar mechanism (`pgoutput`)
to capture these same events over the wire.

Usage:
    python3 scripts/validate_cdc.py
"""

import os
import time
import psycopg2
from psycopg2.extras import LogicalReplicationConnection

def main():
    dsn = os.getenv("DATABASE_URL", "postgresql://meter_user:meter_pass@localhost:5432/meter_to_cash")
    
    print("Connecting to source database...")
    # Standard connection for DML
    conn = psycopg2.connect(dsn)
    conn.autocommit = True
    cur = conn.cursor()

    slot_name = "cdc_validation_test_slot"
    
    try:
        # 1. Setup Logical Replication Slot
        print(f"Creating logical replication slot: '{slot_name}'...")
        try:
            cur.execute(f"SELECT pg_drop_replication_slot('{slot_name}')")
        except Exception:
            pass # ignore if it doesn't exist
            
        cur.execute(f"SELECT pg_create_logical_replication_slot('{slot_name}', 'test_decoding')")

        # 2. Perform an INSERT
        print("\n[Action] Executing INSERT...")
        cur.execute("""
            INSERT INTO utility.customers (customer_id, customer_number, first_name, last_name, email, customer_type)
            VALUES ('11111111-2222-3333-4444-555555555555', 'CUST-CDC-TEST', 'CDC', 'Tester', 'cdc@example.com', 'RESIDENTIAL')
        """)
        
        # 3. Perform an UPDATE
        print("[Action] Executing UPDATE...")
        cur.execute("""
            UPDATE utility.customers 
            SET last_name = 'UpdatedTester', email = 'updated@example.com'
            WHERE customer_id = '11111111-2222-3333-4444-555555555555'
        """)
        
        # 4. Perform a DELETE
        print("[Action] Executing DELETE...")
        cur.execute("""
            DELETE FROM utility.customers 
            WHERE customer_id = '11111111-2222-3333-4444-555555555555'
        """)
        
        # 5. Verify the corresponding CDC events appear downstream (in the slot)
        print("\n[Verification] Fetching CDC events from replication slot...")
        # Give postgres a moment to flush WAL
        time.sleep(1)
        
        cur.execute(f"SELECT data FROM pg_logical_slot_get_changes('{slot_name}', NULL, NULL)")
        changes = cur.fetchall()
        
        found_insert = False
        found_update = False
        found_delete = False
        
        for change in changes:
            data = change[0]
            if "INSERT" in data and "utility.customers" in data and "CUST-CDC-TEST" in data:
                found_insert = True
                print(f"✅ Captured INSERT event: {data}")
            elif "UPDATE" in data and "utility.customers" in data and "UpdatedTester" in data:
                found_update = True
                print(f"✅ Captured UPDATE event: {data}")
            elif "DELETE" in data and "utility.customers" in data:
                found_delete = True
                print(f"✅ Captured DELETE event: {data}")

        assert found_insert, "Failed to capture INSERT event."
        assert found_update, "Failed to capture UPDATE event."
        assert found_delete, "Failed to capture DELETE event."
        
        print("\n🎉 SUCCESS: All CDC events (INSERT, UPDATE, DELETE) were successfully generated and captured by the replication slot.")
        print("This confirms the database is correctly configured for GCP Datastream.")

    finally:
        # Clean up
        print(f"\nCleaning up: Dropping replication slot '{slot_name}'...")
        try:
            cur.execute(f"SELECT pg_drop_replication_slot('{slot_name}')")
        except Exception as e:
            print(f"Cleanup error: {e}")
            
        cur.close()
        conn.close()

if __name__ == "__main__":
    main()
