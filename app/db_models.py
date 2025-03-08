from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base
import uuid
from datetime import datetime

class PANVerification(Base):
    """
    SQLAlchemy model for PAN verification records
    """
    __tablename__ = "pan_verifications"

    id = Column(Integer, primary_key=True, index=True)
    pan = Column(String(10), index=True)
    full_name = Column(String(255))
    category = Column(String(50))
    aadhaar_seeding_status = Column(String(50), nullable=True)
    first_name = Column(String(100), nullable=True)
    middle_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    status = Column(String(50))
    message = Column(Text, nullable=True)
    trace_id = Column(String(100), index=True)
    created_at = Column(DateTime, default=func.now())

class ReversePennyDrop(Base):
    """
    SQLAlchemy model for Reverse Penny Drop requests
    """
    __tablename__ = "reverse_penny_drops"

    id = Column(String(100), primary_key=True, index=True)
    short_url = Column(String(255))
    status = Column(String(50))
    trace_id = Column(String(100), index=True)
    upi_bill_id = Column(String(100))
    upi_link = Column(Text)
    valid_upto = Column(String(100))
    created_at = Column(DateTime, default=func.now())
    
    # Relationship with payments
    payments = relationship("Payment", back_populates="penny_drop")

class Payment(Base):
    """
    SQLAlchemy model for payment records
    """
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(100), ForeignKey("reverse_penny_drops.id"))
    payment_status = Column(Boolean, default=False)
    trace_id = Column(String(100), index=True)
    created_at = Column(DateTime, default=func.now())
    
    # Relationship with reverse penny drop
    penny_drop = relationship("ReversePennyDrop", back_populates="payments") 