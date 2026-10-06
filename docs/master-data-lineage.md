# Master Data Lineage

## Overview
This document specifies the exact origin and nature of the fields mapped between the real UKPN dataset and the synthetic operational master data layer.

## Lineage Table

| Field | Origin | Type | Notes |
|---|---|---|---|
| `source_household_id` | UKPN dataset | Real | Original `LCLid` anchor |
| `stdor_to_u` | UKPN dataset | Real | Preserved precisely |
| `meter_id` | Project generator | Synthetic | Derived dynamically from household ID |
| `customer_id` | Project generator | Synthetic | Derived dynamically from household ID |
| `account_id` | Project generator | Synthetic | Derived dynamically from household ID |
| `contract_id` | Project generator | Synthetic | Derived dynamically from household ID |
| `service_point_id` | Project generator | Synthetic | Derived dynamically from household ID |
| `tariff_code` | Based on source classification | Derived | 1:1 mapping from `stdor_to_u` |

Real UKPN household identifiers, consumption readings and tariff classifications remain source-derived data. The generated IDs are used simply to stand-up a functional SAP-like meter-to-cash architecture around the real smart-meter facts.
