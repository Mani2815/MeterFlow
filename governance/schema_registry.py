import copy
from typing import Dict, Any, List

class IncompatibleSchemaError(Exception):
    pass

class SchemaRegistry:
    def __init__(self):
        # Maps table_name -> list of schema versions
        self.schemas: Dict[str, List[Dict[str, Any]]] = {}

    def register_schema(self, table: str, schema_dict: Dict[str, str], version: str = "1.0"):
        if table not in self.schemas:
            self.schemas[table] = []
        self.schemas[table].append({"version": version, "fields": schema_dict})

    def get_latest_schema(self, table: str) -> Dict[str, Any]:
        if table not in self.schemas or not self.schemas[table]:
            return None
        # Return the last registered schema
        return self.schemas[table][-1]

    def detect_evolution(self, table: str, new_fields: Dict[str, str]) -> bool:
        """
        Compares new_fields against the latest schema.
        Returns True if schema evolved safely (backward compatible).
        Raises IncompatibleSchemaError if breaking changes are detected.
        """
        latest = self.get_latest_schema(table)
        if not latest:
            self.register_schema(table, new_fields)
            return True
            
        old_fields = latest["fields"]
        
        # Check for removed fields or changed types (Incompatible)
        for field, dtype in old_fields.items():
            if field not in new_fields:
                raise IncompatibleSchemaError(f"Field '{field}' was removed. This is a breaking change.")
            if new_fields[field] != dtype:
                raise IncompatibleSchemaError(f"Field '{field}' changed type from {dtype} to {new_fields[field]}.")

        # Check for added fields (Compatible)
        added_fields = {k: v for k, v in new_fields.items() if k not in old_fields}
        
        if added_fields:
            # We assume added fields are inherently nullable in JSON payloads.
            # Increment minor version
            current_version = float(latest["version"])
            new_version = str(round(current_version + 0.1, 1))
            self.register_schema(table, new_fields, version=new_version)
            return True
            
        return False # No changes

    def validate_payload(self, table: str, payload: Dict[str, Any]):
        """
        Validates payload against latest schema types.
        Allows missing fields (treats them as null), but fails on type mismatch for existing fields.
        """
        latest = self.get_latest_schema(table)
        if not latest:
            return
            
        fields = latest["fields"]
        for key, val in payload.items():
            if key in fields and val is not None:
                expected_type = fields[key]
                actual_type = type(val).__name__
                # Basic type mapping verification (str, int, float, bool)
                if expected_type == "int" and not isinstance(val, int):
                    raise TypeError(f"Field '{key}' expected int, got {actual_type}")
                if expected_type == "float" and not isinstance(val, (float, int)):
                    raise TypeError(f"Field '{key}' expected float, got {actual_type}")
                if expected_type == "str" and not isinstance(val, str):
                    raise TypeError(f"Field '{key}' expected str, got {actual_type}")
