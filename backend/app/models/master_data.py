from sqlalchemy import Column, String, DateTime, ForeignKey, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.models.core import Base

class SyntheticCustomer(Base):
    __tablename__ = "synth_customer"
    
    id = Column(String, primary_key=True)
    status = Column(String, default="ACTIVE")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    accounts = relationship("SyntheticAccount", back_populates="customer")

class SyntheticAccount(Base):
    __tablename__ = "synth_account"
    
    id = Column(String, primary_key=True)
    customer_id = Column(String, ForeignKey("synth_customer.id"), nullable=False)
    status = Column(String, default="ACTIVE")
    opened_at = Column(DateTime, default=datetime.utcnow)
    currency = Column(String, default="GBP")
    
    customer = relationship("SyntheticCustomer", back_populates="accounts")
    contracts = relationship("SyntheticContract", back_populates="account")

class SyntheticServicePoint(Base):
    __tablename__ = "synth_service_point"
    
    id = Column(String, primary_key=True)
    region_code = Column(String, default="REGION-LONDON")
    status = Column(String, default="ACTIVE")
    
    meters = relationship("SyntheticMeter", back_populates="service_point")

class SyntheticContract(Base):
    __tablename__ = "synth_contract"
    
    id = Column(String, primary_key=True)
    account_id = Column(String, ForeignKey("synth_account.id"), nullable=False)
    service_point_id = Column(String, ForeignKey("synth_service_point.id"), nullable=False)
    status = Column(String, default="ACTIVE")
    contract_start = Column(DateTime, default=datetime.utcnow)
    contract_end = Column(DateTime, nullable=True)
    
    account = relationship("SyntheticAccount", back_populates="contracts")

class SyntheticMeter(Base):
    __tablename__ = "synth_meter"
    
    id = Column(String, primary_key=True)
    source_household_id = Column(String, unique=True, nullable=False)
    service_point_id = Column(String, ForeignKey("synth_service_point.id"), nullable=False)
    tariff_code = Column(String, nullable=True)
    meter_type = Column(String, default="SMART_ELECTRICITY")
    installation_date = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default="ACTIVE")
    
    service_point = relationship("SyntheticServicePoint", back_populates="meters")
    
    __table_args__ = (
        Index("idx_meter_household", "source_household_id"),
    )
