"""
Data models and schemas for IASW
"""

from datetime import datetime
from enum import Enum
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    """Supported change request types"""
    LEGAL_NAME = "legal_name"
    ADDRESS = "address"
    DATE_OF_BIRTH = "date_of_birth"
    CONTACT_EMAIL = "contact_email"


class DocumentType(str, Enum):
    """Supported document types"""
    MARRIAGE_CERTIFICATE = "marriage_certificate"
    GAZETTE_NOTIFICATION = "gazette_notification"
    DEED_POLL = "deed_poll"
    UTILITY_BILL = "utility_bill"
    LEASE_AGREEMENT = "lease_agreement"
    GOVT_ID = "govt_id"
    BIRTH_CERTIFICATE = "birth_certificate"
    PASSPORT = "passport"
    PAN_CARD = "pan_card"
    CONSENT_FORM = "consent_form"


class RequestStatus(str, Enum):
    """Status of change request"""
    INITIATED = "initiated"
    AI_PROCESSING = "ai_processing"
    AI_VERIFIED_PENDING_HUMAN = "ai_verified_pending_human"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class ChangeRequest(BaseModel):
    """Initial change request from staff"""
    customer_id: str = Field(..., description="Customer identifier")
    change_type: ChangeType
    old_value: str = Field(..., description="Current value in system")
    new_value: str = Field(..., description="Requested new value")
    staff_id: str = Field(..., description="Staff member initiating request")
    notes: Optional[str] = None


class FieldConfidence(BaseModel):
    """Confidence score for a single field"""
    field_name: str
    extracted_value: Optional[str]
    expected_value: str
    confidence_score: float = Field(..., ge=0.0, le=100.0)
    status: str  # "pass", "flag", "fail"
    notes: Optional[str] = None


class ConfidenceScoreCard(BaseModel):
    """Overall confidence assessment"""
    request_id: str
    overall_confidence: float = Field(..., ge=0.0, le=100.0)
    field_scores: List[FieldConfidence]
    forgery_check_passed: bool
    forgery_confidence: float = Field(..., ge=0.0, le=100.0)
    recommendation: str  # "approve", "reject", "manual_review"
    ai_summary: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DocumentProcessingResult(BaseModel):
    """Result from document processor agent"""
    document_id: str
    extracted_data: Dict[str, Any]
    ocr_confidence: float
    forgery_detected: bool
    forgery_score: float
    processing_time_ms: int
    filenet_reference: str


class PendingRequest(BaseModel):
    """Record in pending table awaiting human checker"""
    request_id: str
    customer_id: str
    change_type: ChangeType
    old_value: str
    new_value: str
    document_id: str
    filenet_reference: str
    confidence_score_card: ConfidenceScoreCard
    status: RequestStatus
    created_at: datetime = Field(default_factory=datetime.utcnow)
    processed_at: Optional[datetime] = None
    checker_id: Optional[str] = None
    checker_decision: Optional[str] = None
    checker_notes: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CheckerDecision(BaseModel):
    """Decision from human checker"""
    request_id: str
    checker_id: str
    decision: str  # "approve", "reject"
    notes: Optional[str] = None


class RPSUpdateRequest(BaseModel):
    """Request to update core banking system (RPS)"""
    customer_id: str
    change_type: ChangeType
    old_value: str
    new_value: str
    approved_by: str
    request_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ValidationResult(BaseModel):
    """Result from validation agent"""
    valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    rps_record_found: bool
    rps_current_value: Optional[str] = None
