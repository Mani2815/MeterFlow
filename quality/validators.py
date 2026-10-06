import json
from datetime import datetime
from typing import Dict, Any, List

class DataValidator:
    def validate_record(self, table: str, payload: Dict[str, Any]) -> List[str]:
        errors = []
        
        # 1. Required fields & Null checks
        if not payload.get('id') and not payload.get(f"{table[:-1]}_id") and not payload.get(f"{table}_id"):
            errors.append("Missing primary key / ID field")
            
        # 2. Impossible meter readings or negative quantities
        if table == "meter_readings":
            val = payload.get("reading_value")
            if val is not None:
                try:
                    if float(val) < 0:
                        errors.append("Negative reading_value not allowed")
                    if float(val) > 999999:
                        errors.append("reading_value exceeds realistic maximum")
                except ValueError:
                    errors.append("reading_value must be numeric")
                    
            if not payload.get("read_at"):
                errors.append("read_at timestamp is required")
                
        # 3. Negative quantities in billing/payments
        if table in ("bills", "payments"):
            amt = payload.get("total_amount") or payload.get("amount")
            if amt is not None:
                try:
                    if float(amt) < 0:
                        errors.append("Financial amount cannot be negative")
                except ValueError:
                    errors.append("Amount must be numeric")
                    
        # 4. Invalid timestamps
        for k, v in payload.items():
            if isinstance(k, str) and ("date" in k or "_at" in k) and v:
                if isinstance(v, str) and len(v) > 0:
                    if v.startswith("0000"):
                        errors.append(f"Invalid zero-timestamp in {k}")
                    
        return errors
