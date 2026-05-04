"""
SQLAlchemy database models for IASW
"""

from sqlalchemy import Column, String, Float, Boolean, DateTime, Text, JSON, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from datetime import datetime
import enum

Base = declarative_base()


class ChangeTypeEnum(enum.Enum):
    """Change types"""
    legal_name = "legal_name"
    address = "address"
    date_of_birth = "date_of_birth"
    contact_email = "contact_email"


class RequestStatusEnum(enum.Enum):
    """Request status"""
    initiated = "initiated"
    ai_processing = "ai_processing"
    ai_verified_pending_human = "ai_verified_pending_human"
    approved = "approved"
    rejected = "rejected"
    failed = "failed"


class PendingRequestDB(Base):
    """Pending requests table - awaiting checker approval"""
    __tablename__ = "pending_requests"

    request_id = Column(String(100), primary_key=True)
    customer_id = Column(String(100), nullable=False, index=True)
    change_type = Column(SQLEnum(ChangeTypeEnum), nullable=False)
    old_value = Column(String(500), nullable=False)
    new_value = Column(String(500), nullable=False)

    # Document info
    document_id = Column(String(100), nullable=False)
    filenet_reference = Column(String(200), nullable=False)

    # Confidence scoring
    overall_confidence = Column(Float, nullable=False)
    field_scores = Column(JSON, nullable=False)  # List of FieldConfidence objects
    forgery_check_passed = Column(Boolean, nullable=False)
    forgery_confidence = Column(Float, nullable=False)
    ai_recommendation = Column(String(50), nullable=False)
    ai_summary = Column(Text, nullable=False)

    # Status and workflow
    status = Column(SQLEnum(RequestStatusEnum), nullable=False, default=RequestStatusEnum.initiated)

    # Human checker info
    checker_id = Column(String(100), nullable=True)
    checker_decision = Column(String(50), nullable=True)
    checker_notes = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    processed_at = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Audit trail
    staff_id = Column(String(100), nullable=False)
    request_notes = Column(Text, nullable=True)


class ApprovedRequestDB(Base):
    """Approved requests - final record"""
    __tablename__ = "approved_requests"

    request_id = Column(String(100), primary_key=True)
    customer_id = Column(String(100), nullable=False, index=True)
    change_type = Column(SQLEnum(ChangeTypeEnum), nullable=False)
    old_value = Column(String(500), nullable=False)
    new_value = Column(String(500), nullable=False)

    # Approval info
    checker_id = Column(String(100), nullable=False)
    checker_decision = Column(String(50), nullable=False)
    checker_notes = Column(Text, nullable=True)

    # Reference
    filenet_reference = Column(String(200), nullable=False)
    confidence_score = Column(Float, nullable=False)

    # RPS update status
    rps_updated = Column(Boolean, default=False)
    rps_update_timestamp = Column(DateTime(timezone=True), nullable=True)
    rps_response = Column(JSON, nullable=True)

    # Timestamps
    approved_at = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), nullable=False)


class AuditLogDB(Base):
    """Audit log for all system actions"""
    __tablename__ = "audit_logs"

    id = Column(String(100), primary_key=True)
    request_id = Column(String(100), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    actor = Column(String(100), nullable=False)  # "ai_agent" or user ID
    details = Column(JSON, nullable=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
