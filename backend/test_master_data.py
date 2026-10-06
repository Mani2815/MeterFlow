import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.master_data import SyntheticCustomer, SyntheticAccount, SyntheticServicePoint, SyntheticContract, SyntheticMeter
from app.processing.standardize import AsyncSessionLocal

async def test_master_data():
    db = AsyncSessionLocal()
    
    # 1. Fetch all meters with their relationships loaded up to Customer
    # Meter -> ServicePoint -> Contract -> Account -> Customer
    # Wait, Meter points to ServicePoint. Contract points to ServicePoint and Account.
    # To get from Meter to Customer, we go: Meter.service_point -> ServicePoint.contracts -> Contract.account -> Account.customer
    query = select(SyntheticMeter).options(
        selectinload(SyntheticMeter.service_point)
    )
    result = await db.execute(query)
    meters = result.scalars().all()
    
    print("--- REFERENTIAL INTEGRITY & MAPPING REPORT ---")
    for meter in meters:
        sp = meter.service_point
        
        # Load contracts for this SP
        ctr_query = select(SyntheticContract).where(SyntheticContract.service_point_id == sp.id).options(selectinload(SyntheticContract.account).selectinload(SyntheticAccount.customer))
        ctr_result = await db.execute(ctr_query)
        contracts = ctr_result.scalars().all()
        
        for ctr in contracts:
            acc = ctr.account
            cus = acc.customer
            print(f"household: {meter.source_household_id}")
            print(f"meter: {meter.id}")
            print(f"service_point: {sp.id}")
            print(f"contract: {ctr.id}")
            print(f"account: {acc.id}")
            print(f"customer: {cus.id}")
            print(f"tariff: {meter.tariff_code}")
            print("---------------------------------")
            
            # Assertions
            assert acc.customer_id == cus.id, "Account -> Customer FK failed"
            assert ctr.account_id == acc.id, "Contract -> Account FK failed"
            assert ctr.service_point_id == sp.id, "Contract -> SP FK failed"
            assert meter.service_point_id == sp.id, "Meter -> SP FK failed"
            assert meter.tariff_code in ["Std", "ToU"], "Invalid tariff mapping"
            
    # Source coverage: Count total meters vs unique households
    from generate_master_data import get_unique_households
    df_unique = get_unique_households()
    assert len(meters) == len(df_unique), f"Source coverage mismatch: expected {len(df_unique)}, got {len(meters)}"
    
    print("ALL TESTS PASSED")
    
if __name__ == "__main__":
    asyncio.run(test_master_data())
