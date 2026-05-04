"""
Database service for IASW
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from backend.models.database import Base, PendingRequestDB, ApprovedRequestDB, AuditLogDB
from contextlib import contextmanager
import uuid
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseService:
    """Manages database connections and operations"""

    def __init__(self, database_url: str = "sqlite:///./iasw.db"):
        """
        Initialize database service.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        logger.info(f"Database service initialized: {database_url}")

    def create_tables(self):
        """Create all tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created")

    @contextmanager
    def get_session(self) -> Session:
        """
        Get database session context manager.

        Yields:
            SQLAlchemy session
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()

    def create_pending_request(self, session: Session, request_data: dict) -> PendingRequestDB:
        """
        Create a new pending request record.

        Args:
            session: Database session
            request_data: Request data dictionary

        Returns:
            Created PendingRequestDB record
        """
        pending_request = PendingRequestDB(**request_data)
        session.add(pending_request)
        session.flush()
        logger.info(f"Created pending request: {pending_request.request_id}")
        return pending_request

    def get_pending_request(self, session: Session, request_id: str) -> PendingRequestDB:
        """
        Get pending request by ID.

        Args:
            session: Database session
            request_id: Request identifier

        Returns:
            PendingRequestDB record or None
        """
        return session.query(PendingRequestDB).filter(
            PendingRequestDB.request_id == request_id
        ).first()

    def get_all_pending_requests(self, session: Session):
        """
        Get all pending requests for checker review.

        Args:
            session: Database session

        Returns:
            List of PendingRequestDB records
        """
        return session.query(PendingRequestDB).filter(
            PendingRequestDB.status == "ai_verified_pending_human"
        ).order_by(PendingRequestDB.created_at.desc()).all()

    def update_request_status(
        self,
        session: Session,
        request_id: str,
        status: str,
        checker_id: str = None,
        checker_decision: str = None,
        checker_notes: str = None
    ):
        """
        Update request status and checker information.

        Args:
            session: Database session
            request_id: Request identifier
            status: New status
            checker_id: Checker user ID
            checker_decision: Checker decision
            checker_notes: Checker notes
        """
        pending_request = self.get_pending_request(session, request_id)
        if pending_request:
            pending_request.status = status
            if checker_id:
                pending_request.checker_id = checker_id
            if checker_decision:
                pending_request.checker_decision = checker_decision
            if checker_notes:
                pending_request.checker_notes = checker_notes
            pending_request.processed_at = datetime.utcnow()
            session.flush()
            logger.info(f"Updated request {request_id} status to {status}")

    def create_approved_request(self, session: Session, approved_data: dict) -> ApprovedRequestDB:
        """
        Create approved request record.

        Args:
            session: Database session
            approved_data: Approved request data

        Returns:
            Created ApprovedRequestDB record
        """
        approved_request = ApprovedRequestDB(**approved_data)
        session.add(approved_request)
        session.flush()
        logger.info(f"Created approved request: {approved_request.request_id}")
        return approved_request

    def log_audit(
        self,
        session: Session,
        request_id: str,
        action: str,
        actor: str,
        details: dict = None
    ):
        """
        Create audit log entry.

        Args:
            session: Database session
            request_id: Request identifier
            action: Action performed
            actor: User or agent performing action
            details: Additional details
        """
        audit_log = AuditLogDB(
            id=str(uuid.uuid4()),
            request_id=request_id,
            action=action,
            actor=actor,
            details=details
        )
        session.add(audit_log)
        session.flush()
        logger.debug(f"Audit log: {action} by {actor} for {request_id}")


# Singleton instance
_db_service = None


def get_database_service() -> DatabaseService:
    """Get or create singleton database service"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
        _db_service.create_tables()
    return _db_service
