"""
IASW - Intelligent Account Servicing Workflow
FastAPI Backend Application
"""

import asyncio
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import shutil

from backend.models.schemas import (
    ChangeRequest,
    ChangeType,
    CheckerDecision,
    RequestStatus,
    PendingRequest
)
from backend.models.auth import (
    LoginRequest,
    LoginResponse,
    UserRole,
    ChangePasswordRequest,
    AccountDetailsResponse
)
from backend.agents.validation_agent import ValidationAgent
from backend.agents.document_processor_agent import DocumentProcessorAgent
from backend.agents.confidence_scorer_agent import ConfidenceScorerAgent
from backend.services.database import get_database_service
from backend.services.rps_service import get_rps_service
from backend.models.database import PendingRequestDB
from backend.services.auth_service import get_auth_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/iasw.log')
    ]
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="IASW - Intelligent Account Servicing Workflow",
    description="AI-powered account servicing with Human-in-the-Loop approval",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify actual origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
db_service = get_database_service()
rps_service = get_rps_service()
auth_service = get_auth_service()

# Initialize agents
validation_agent = ValidationAgent(rps_service=rps_service)
document_processor = DocumentProcessorAgent()
confidence_scorer = ConfidenceScorerAgent()

# Security
security = HTTPBearer()


def get_current_user(authorization: HTTPAuthorizationCredentials = Depends(security)):
    """Dependency to get current authenticated user"""
    token = authorization.credentials
    user = auth_service.validate_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


def require_role(required_role: UserRole):
    """Dependency factory to require specific role"""
    def role_checker(user = Depends(get_current_user)):
        if user["role"] != required_role and user["role"] != UserRole.ADMIN:
            raise HTTPException(status_code=403, detail=f"Requires {required_role} role")
        return user
    return role_checker

# Ensure required directories exist
Path("data/documents").mkdir(parents=True, exist_ok=True)
Path("logs").mkdir(parents=True, exist_ok=True)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IASW - Intelligent Account Servicing Workflow",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@app.post("/api/auth/login", response_model=LoginResponse)
async def login(login_request: LoginRequest):
    """
    User login endpoint.

    Returns access token on successful authentication.
    """
    logger.info(f"Login attempt for user: {login_request.username}")

    auth_result = auth_service.authenticate(
        username=login_request.username,
        password=login_request.password
    )

    if not auth_result:
        raise HTTPException(status_code=401, detail="Invalid username or password")

    return LoginResponse(
        success=True,
        token=auth_result["token"],
        user_id=auth_result["user_id"],
        username=auth_result["username"],
        role=auth_result["role"],
        customer_id=auth_result.get("customer_id")
    )


@app.post("/api/auth/logout")
async def logout(user = Depends(get_current_user), authorization: HTTPAuthorizationCredentials = Depends(security)):
    """Logout current user"""
    token = authorization.credentials
    auth_service.logout(token)
    return {"success": True, "message": "Logged out successfully"}


@app.get("/api/auth/me")
async def get_current_user_info(user = Depends(get_current_user)):
    """Get current user information"""
    return {
        "user_id": user["user_id"],
        "username": user["username"],
        "role": user["role"],
        "customer_id": user.get("customer_id")
    }


@app.post("/api/auth/change-password")
async def change_password(
    password_request: ChangePasswordRequest,
    user = Depends(get_current_user)
):
    """Change user password"""
    success = auth_service.change_password(
        username=user["username"],
        old_password=password_request.old_password,
        new_password=password_request.new_password
    )

    if not success:
        raise HTTPException(status_code=400, detail="Invalid old password")

    return {"success": True, "message": "Password changed successfully"}


# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/api/users")
async def get_all_users(user = Depends(require_role(UserRole.CHECKER))):
    """
    Get all users in the system (Checker only).
    Passwords are never returned.
    """
    users = auth_service.get_all_users()
    return {"success": True, "count": len(users), "users": users}


# ============================================================================
# ACCOUNT DETAILS ENDPOINTS
# ============================================================================

@app.get("/api/account/details")
async def get_account_details(user = Depends(get_current_user)):
    """
    Get account details based on user role.

    - Account Holder: Can see ALL details including balance
    - Checker: Can see all details EXCEPT balance
    - Others: No access
    """
    # Get customer_id based on user role
    if user["role"] == UserRole.ACCOUNT_HOLDER:
        customer_id = user.get("customer_id")
        if not customer_id:
            raise HTTPException(status_code=404, detail="Customer ID not found for user")
    elif user["role"] == UserRole.CHECKER:
        # Checker needs to specify customer_id as query param
        raise HTTPException(status_code=400, detail="Checker must specify customer_id as query parameter")
    else:
        raise HTTPException(status_code=403, detail="Access denied")

    # Get customer details from RPS
    customer_data = rps_service.get_customer_details(customer_id)

    if not customer_data:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Include balance only for account holder
    include_balance = (user["role"] == UserRole.ACCOUNT_HOLDER)

    return {
        "customer_id": customer_data["customer_id"],
        "name": customer_data["name"],
        "email": customer_data["email"],
        "address": customer_data["address"],
        "dob": customer_data["dob"],
        "phone": customer_data.get("phone"),
        "account_number": customer_data.get("account_number"),
        "account_type": customer_data.get("account_type"),
        "balance": customer_data.get("balance") if include_balance else None
    }


@app.get("/api/account/details/{customer_id}")
async def get_customer_details_by_id(
    customer_id: str,
    user = Depends(require_role(UserRole.CHECKER))
):
    """
    Get customer account details by customer ID (Checker only).
    Checker can see all details EXCEPT balance.
    """
    customer_data = rps_service.get_customer_details(customer_id)

    if not customer_data:
        raise HTTPException(status_code=404, detail="Customer not found")

    # Checkers cannot see balance
    return {
        "customer_id": customer_data["customer_id"],
        "name": customer_data["name"],
        "email": customer_data["email"],
        "address": customer_data["address"],
        "dob": customer_data["dob"],
        "phone": customer_data.get("phone"),
        "account_number": customer_data.get("account_number"),
        "account_type": customer_data.get("account_type"),
        "balance": None  # Hidden from checker
    }


@app.post("/api/change-request/submit")
async def submit_change_request(
    customer_id: str = Form(...),
    change_type: str = Form(...),
    old_value: str = Form(...),
    new_value: str = Form(...),
    staff_id: str = Form(...),
    notes: str = Form(None),
    document: UploadFile = File(...),
    user = Depends(get_current_user)
):
    """
    Submit a new change request (Step 1 - Initiation).

    This endpoint:
    1. Validates the request against RPS
    2. Processes the uploaded document
    3. Generates confidence scores
    4. Stages the request for human checker approval

    Args:
        customer_id: Customer identifier
        change_type: Type of change (legal_name, address, etc.)
        old_value: Current value
        new_value: Requested new value
        staff_id: Staff member submitting request
        notes: Optional notes
        document: Supporting document (PDF/image)

    Returns:
        Request ID and initial status
    """
    logger.info("=" * 80)
    logger.info("NEW CHANGE REQUEST RECEIVED")
    logger.info("=" * 80)
    logger.info(f"Customer: {customer_id}")
    logger.info(f"Change Type: {change_type}")
    logger.info(f"Old Value: {old_value}")
    logger.info(f"New Value: {new_value}")
    logger.info(f"Staff: {staff_id}")
    logger.info(f"Document: {document.filename}")

    try:
        # Generate unique request ID
        request_id = f"REQ-{int(datetime.utcnow().timestamp())}-{uuid.uuid4().hex[:8]}"

        # Create change request object
        change_request = ChangeRequest(
            customer_id=customer_id,
            change_type=ChangeType(change_type),
            old_value=old_value,
            new_value=new_value,
            staff_id=staff_id,
            notes=notes
        )

        # Step 1: Validate request against RPS
        logger.info("\n🔍 STEP 1: Validating request against RPS...")
        validation_result = await asyncio.to_thread(
            validation_agent.validate_request, change_request
        )

        if not validation_result.valid:
            logger.error(f"❌ Validation failed: {validation_result.errors}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Validation failed",
                    "errors": validation_result.errors,
                    "warnings": validation_result.warnings
                }
            )

        logger.info(f"✅ Validation passed (warnings: {len(validation_result.warnings)})")

        # Save uploaded document
        document_path = f"data/documents/{request_id}_{document.filename}"
        with open(document_path, "wb") as buffer:
            shutil.copyfileobj(document.file, buffer)
        logger.info(f"📄 Document saved: {document_path}")

        # Step 2: Process document with AI (offloaded to thread pool — LLM + OCR are blocking)
        logger.info("\n📝 STEP 2: Processing document with AI...")
        doc_result = await asyncio.to_thread(
            document_processor.process_document,
            document_path,
            change_type,
            "marriage_certificate",  # Would be determined from context
        )
        logger.info(f"✅ Document processed: confidence={doc_result.ocr_confidence:.1f}%")

        # Step 3: Generate confidence score card (offloaded — also calls the LLM for the summary)
        logger.info("\n📊 STEP 3: Generating confidence score card...")
        score_card = await asyncio.to_thread(
            confidence_scorer.generate_score_card,
            change_request,
            doc_result,
            request_id,
        )
        logger.info(f"✅ Score card generated: {score_card.overall_confidence:.1f}% confidence")
        logger.info(f"   Recommendation: {score_card.recommendation}")

        # Step 4: Stage in pending table
        logger.info("\n💾 STEP 4: Staging request for checker approval...")

        with db_service.get_session() as session:
            # Create pending request
            pending_data = {
                "request_id": request_id,
                "customer_id": customer_id,
                "change_type": change_type,
                "old_value": old_value,
                "new_value": new_value,
                "document_id": doc_result.document_id,
                "filenet_reference": doc_result.filenet_reference,
                "overall_confidence": score_card.overall_confidence,
                "field_scores": [f.dict() for f in score_card.field_scores],
                "forgery_check_passed": score_card.forgery_check_passed,
                "forgery_confidence": score_card.forgery_confidence,
                "ai_recommendation": score_card.recommendation,
                "ai_summary": score_card.ai_summary,
                "status": RequestStatus.AI_VERIFIED_PENDING_HUMAN.value,
                "staff_id": staff_id,
                "request_notes": notes
            }

            pending_request = db_service.create_pending_request(session, pending_data)

            # Audit log
            db_service.log_audit(
                session=session,
                request_id=request_id,
                action="request_submitted",
                actor=staff_id,
                details={
                    "change_type": change_type,
                    "confidence": score_card.overall_confidence,
                    "recommendation": score_card.recommendation
                }
            )

        logger.info(f"✅ Request staged: {request_id}")
        logger.info("=" * 80)

        return {
            "success": True,
            "request_id": request_id,
            "status": RequestStatus.AI_VERIFIED_PENDING_HUMAN.value,
            "confidence_score": score_card.overall_confidence,
            "recommendation": score_card.recommendation,
            "filenet_reference": doc_result.filenet_reference,
            "message": "Request submitted and awaiting checker approval"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


def _serialize_pending(req):
    """Shape a PendingRequestDB row for list/detail responses."""
    return {
        "request_id": req.request_id,
        "customer_id": req.customer_id,
        "change_type": req.change_type.value if hasattr(req.change_type, 'value') else req.change_type,
        "old_value": req.old_value,
        "new_value": req.new_value,
        "confidence_score": req.overall_confidence,
        "ai_recommendation": req.ai_recommendation,
        "ai_summary": req.ai_summary,
        "field_scores": req.field_scores,
        "forgery_check_passed": req.forgery_check_passed,
        "filenet_reference": req.filenet_reference,
        "staff_id": req.staff_id,
        "status": req.status.value if hasattr(req.status, 'value') else req.status,
        "checker_id": req.checker_id,
        "checker_decision": req.checker_decision,
        "created_at": req.created_at.isoformat() if req.created_at else None,
        "processed_at": req.processed_at.isoformat() if req.processed_at else None,
    }


@app.get("/api/my-requests")
async def get_my_requests(user = Depends(get_current_user)):
    """List requests scoped to the current user.

    - account_holder sees requests for their customer_id
    - staff sees requests they submitted
    - checker sees every request (admin-like visibility)
    """
    try:
        with db_service.get_session() as session:
            all_rows = session.query(PendingRequestDB).order_by(PendingRequestDB.created_at.desc()).all()
            role = user['role']
            uname = user['username']
            cid = user.get('customer_id')
            filtered = []
            for r in all_rows:
                if role == UserRole.CHECKER or role == UserRole.ADMIN:
                    filtered.append(r)
                elif role == UserRole.ACCOUNT_HOLDER and cid and r.customer_id == cid:
                    filtered.append(r)
                elif role == UserRole.STAFF and r.staff_id == uname:
                    filtered.append(r)
            return {"success": True, "count": len(filtered), "requests": [_serialize_pending(r) for r in filtered]}
    except Exception as e:
        logger.error(f"Error listing my requests: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/my-requests/{request_id}")
async def get_my_request_detail(request_id: str, user = Depends(get_current_user)):
    """Authenticated single-request fetch used by the progress timeline."""
    try:
        with db_service.get_session() as session:
            req = db_service.get_pending_request(session, request_id)
            if not req:
                raise HTTPException(status_code=404, detail="Request not found")
            role = user['role']
            cid = user.get('customer_id')
            uname = user['username']
            if role == UserRole.ACCOUNT_HOLDER and (not cid or req.customer_id != cid):
                raise HTTPException(status_code=403, detail="Not your request")
            if role == UserRole.STAFF and req.staff_id != uname:
                raise HTTPException(status_code=403, detail="Not your request")
            return {"success": True, "request": _serialize_pending(req)}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching my request detail: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/checker/pending-requests")
async def get_pending_requests(user = Depends(require_role(UserRole.CHECKER))):
    """
    Get all pending requests awaiting checker approval (Step 3 - Checker Review).
    Requires CHECKER role.

    Returns:
        List of pending requests with AI analysis
    """
    try:
        with db_service.get_session() as session:
            pending_requests = db_service.get_all_pending_requests(session)

            results = []
            for req in pending_requests:
                results.append({
                    "request_id": req.request_id,
                    "customer_id": req.customer_id,
                    "change_type": req.change_type.value,
                    "old_value": req.old_value,
                    "new_value": req.new_value,
                    "confidence_score": req.overall_confidence,
                    "ai_recommendation": req.ai_recommendation,
                    "ai_summary": req.ai_summary,
                    "forgery_check_passed": req.forgery_check_passed,
                    "filenet_reference": req.filenet_reference,
                    "field_scores": req.field_scores,
                    "created_at": req.created_at.isoformat(),
                    "staff_id": req.staff_id
                })

            return {
                "success": True,
                "count": len(results),
                "pending_requests": results
            }

    except Exception as e:
        logger.error(f"Error fetching pending requests: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/checker/decision")
async def submit_checker_decision(
    decision: CheckerDecision,
    user = Depends(require_role(UserRole.CHECKER))
):
    """
    Submit checker decision (Step 3 - Human Approval).
    Requires CHECKER role.

    CRITICAL: This is the HUMAN-IN-THE-LOOP boundary.
    Only upon explicit human approval will the RPS write-call be triggered.

    Args:
        decision: Checker decision (approve/reject)

    Returns:
        Decision result and RPS update status
    """
    logger.info("=" * 80)
    logger.info("CHECKER DECISION RECEIVED")
    logger.info("=" * 80)
    logger.info(f"Request ID: {decision.request_id}")
    logger.info(f"Checker: {decision.checker_id}")
    logger.info(f"Decision: {decision.decision}")

    try:
        with db_service.get_session() as session:
            # Get pending request
            pending_request = db_service.get_pending_request(session, decision.request_id)

            if not pending_request:
                raise HTTPException(status_code=404, detail="Request not found")

            # Check if status is correct (handle both enum and string)
            status_value = pending_request.status.value if hasattr(pending_request.status, 'value') else pending_request.status
            if status_value != RequestStatus.AI_VERIFIED_PENDING_HUMAN.value:
                raise HTTPException(
                    status_code=400,
                    detail=f"Request is not in pending state: {status_value}"
                )

            # Process decision
            if decision.decision.lower() == "approve":
                logger.info("\n✅ APPROVED - Initiating RPS update...")

                # Update RPS (CRITICAL: Only happens after human approval)
                rps_response = await asyncio.to_thread(
                    rps_service.update_customer_record,
                    pending_request.customer_id,
                    pending_request.change_type.value,
                    pending_request.old_value,
                    pending_request.new_value,
                    decision.checker_id,
                    decision.request_id,
                )

                if rps_response.get("success"):
                    # Sync auth user record so Checker's Users tab reflects the change
                    auth_service.update_user_by_customer_id(
                        customer_id=pending_request.customer_id,
                        field_name=pending_request.change_type.value,
                        new_value=pending_request.new_value,
                    )

                    # Update pending request status
                    db_service.update_request_status(
                        session=session,
                        request_id=decision.request_id,
                        status=RequestStatus.APPROVED.value,
                        checker_id=decision.checker_id,
                        checker_decision="approve",
                        checker_notes=decision.notes
                    )

                    # Create approved request record
                    approved_data = {
                        "request_id": decision.request_id,
                        "customer_id": pending_request.customer_id,
                        "change_type": pending_request.change_type.value,
                        "old_value": pending_request.old_value,
                        "new_value": pending_request.new_value,
                        "checker_id": decision.checker_id,
                        "checker_decision": "approve",
                        "checker_notes": decision.notes,
                        "filenet_reference": pending_request.filenet_reference,
                        "confidence_score": pending_request.overall_confidence,
                        "rps_updated": True,
                        "rps_update_timestamp": datetime.utcnow(),
                        "rps_response": rps_response,
                        "created_at": pending_request.created_at
                    }
                    db_service.create_approved_request(session, approved_data)

                    # Audit log
                    db_service.log_audit(
                        session=session,
                        request_id=decision.request_id,
                        action="approved_and_executed",
                        actor=decision.checker_id,
                        details={"rps_transaction_id": rps_response.get("rps_transaction_id")}
                    )

                    logger.info("✅ Request approved and RPS updated successfully")
                    logger.info("=" * 80)

                    return {
                        "success": True,
                        "message": "Request approved and RPS updated",
                        "request_id": decision.request_id,
                        "rps_transaction_id": rps_response.get("rps_transaction_id"),
                        "status": RequestStatus.APPROVED.value
                    }
                else:
                    logger.error(f"❌ RPS update failed: {rps_response.get('error')}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"RPS update failed: {rps_response.get('error')}"
                    )

            else:  # Reject
                logger.info("\n❌ REJECTED by checker")

                # Update status
                db_service.update_request_status(
                    session=session,
                    request_id=decision.request_id,
                    status=RequestStatus.REJECTED.value,
                    checker_id=decision.checker_id,
                    checker_decision="reject",
                    checker_notes=decision.notes
                )

                # Audit log
                db_service.log_audit(
                    session=session,
                    request_id=decision.request_id,
                    action="rejected",
                    actor=decision.checker_id,
                    details={"reason": decision.notes}
                )

                logger.info("✅ Request rejected")
                logger.info("=" * 80)

                return {
                    "success": True,
                    "message": "Request rejected",
                    "request_id": decision.request_id,
                    "status": RequestStatus.REJECTED.value
                }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error processing checker decision: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/request/{request_id}")
async def get_request_details(request_id: str):
    """
    Get detailed information about a specific request.

    Args:
        request_id: Request identifier

    Returns:
        Request details with full history
    """
    try:
        with db_service.get_session() as session:
            pending_request = db_service.get_pending_request(session, request_id)

            if not pending_request:
                raise HTTPException(status_code=404, detail="Request not found")

            return {
                "success": True,
                "request": {
                    "request_id": pending_request.request_id,
                    "customer_id": pending_request.customer_id,
                    "change_type": pending_request.change_type.value,
                    "old_value": pending_request.old_value,
                    "new_value": pending_request.new_value,
                    "status": pending_request.status.value,
                    "confidence_score": pending_request.overall_confidence,
                    "ai_recommendation": pending_request.ai_recommendation,
                    "ai_summary": pending_request.ai_summary,
                    "field_scores": pending_request.field_scores,
                    "forgery_check_passed": pending_request.forgery_check_passed,
                    "filenet_reference": pending_request.filenet_reference,
                    "checker_id": pending_request.checker_id,
                    "checker_decision": pending_request.checker_decision,
                    "checker_notes": pending_request.checker_notes,
                    "created_at": pending_request.created_at.isoformat(),
                    "processed_at": pending_request.processed_at.isoformat() if pending_request.processed_at else None
                }
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching request details: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
