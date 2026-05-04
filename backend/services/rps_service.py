"""
RPS (Core Banking System) Service - Mock Implementation
"""

import logging
from typing import Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class RPSService:
    """
    Mock RPS (Core Banking System) service.
    In production, this would integrate with the actual core banking system.
    """

    # Map change-request field names to customer-record field names
    FIELD_MAP = {
        "legal_name": "name",
        "address": "address",
        "date_of_birth": "dob",
        "contact_email": "email",
    }

    def __init__(self):
        """Initialize RPS service with in-memory customer store."""
        self._customers = {
            "C001": {
                "customer_id": "C001",
                "name": "Priya Sharma",
                "address": "123 Main St, Mumbai, 400001",
                "dob": "1990-05-15",
                "email": "priya.sharma@email.com",
                "phone": "+91-9876543210",
                "account_number": "ACC-001-12345",
                "account_type": "Savings",
                "balance": 125000.50,
            },
            "C002": {
                "customer_id": "C002",
                "name": "Rahul Kumar",
                "address": "456 Park Ave, Delhi, 110001",
                "dob": "1985-08-22",
                "email": "rahul.kumar@email.com",
                "phone": "+91-9876543211",
                "account_number": "ACC-002-67890",
                "account_type": "Current",
                "balance": 45678.75,
            },
            "C003": {
                "customer_id": "C003",
                "name": "Tanvi Dubey",
                "address": "789 Lake View, Bangalore, 560001",
                "dob": "1995-03-12",
                "email": "tanvi.dubey@email.com",
                "phone": "+91-9876543212",
                "account_number": "ACC-003-11223",
                "account_type": "Savings",
                "balance": 250000.00,
            },
        }
        logger.info("RPSService initialized (Mock)")

    def update_customer_record(
        self,
        customer_id: str,
        field_name: str,
        old_value: str,
        new_value: str,
        approved_by: str,
        request_id: str
    ) -> Dict:
        """
        Update customer record in RPS.

        CRITICAL: This is the final write-call to the core banking system.
        This method should ONLY be called after explicit human approval.

        Args:
            customer_id: Customer identifier
            field_name: Field to update
            old_value: Current value (for verification)
            new_value: New value to set
            approved_by: Checker who approved the change
            request_id: Original request ID for audit

        Returns:
            Dict with update result
        """
        logger.info("=" * 80)
        logger.info("RPS UPDATE INITIATED")
        logger.info("=" * 80)
        logger.info(f"Customer ID: {customer_id}")
        logger.info(f"Field: {field_name}")
        logger.info(f"Old Value: {old_value}")
        logger.info(f"New Value: {new_value}")
        logger.info(f"Approved By: {approved_by}")
        logger.info(f"Request ID: {request_id}")
        logger.info("=" * 80)

        # Mock implementation - simulate RPS update
        # In production, this would make actual API call to core banking system

        try:
            import time
            time.sleep(0.5)

            customer = self._customers.get(customer_id)
            if not customer:
                raise KeyError(f"Customer {customer_id} not found in RPS")

            target_field = self.FIELD_MAP.get(field_name, field_name)
            if target_field not in customer:
                raise KeyError(f"Unknown RPS field '{target_field}' for customer {customer_id}")

            current_value = customer[target_field]
            customer[target_field] = new_value
            logger.info(f"RPS: {customer_id}.{target_field} {current_value!r} -> {new_value!r}")

            response = {
                "success": True,
                "customer_id": customer_id,
                "field_updated": target_field,
                "old_value": old_value,
                "new_value": new_value,
                "updated_at": datetime.utcnow().isoformat(),
                "updated_by": approved_by,
                "request_id": request_id,
                "rps_transaction_id": f"RPS-TXN-{int(time.time())}"
            }

            logger.info(f"✅ RPS UPDATE SUCCESSFUL: {response['rps_transaction_id']}")
            logger.info("=" * 80)

            return response

        except Exception as e:
            logger.error(f"❌ RPS UPDATE FAILED: {str(e)}")
            logger.info("=" * 80)
            return {
                "success": False,
                "error": str(e),
                "customer_id": customer_id,
                "request_id": request_id
            }

    def get_customer_record(self, customer_id: str) -> Optional[Dict]:
        """
        Retrieve customer record from RPS.

        Args:
            customer_id: Customer identifier

        Returns:
            Customer record or None
        """
        customer = self._customers.get(customer_id)
        if customer:
            logger.info(f"Retrieved RPS record for customer {customer_id}")
        else:
            logger.warning(f"Customer {customer_id} not found in RPS")

        return customer

    def get_customer_details(self, customer_id: str) -> Optional[Dict]:
        """
        Get detailed customer information (alias for get_customer_record).

        Args:
            customer_id: Customer identifier

        Returns:
            Customer details or None
        """
        return self.get_customer_record(customer_id)

    def verify_field_value(self, customer_id: str, field_name: str, expected_value: str) -> bool:
        """
        Verify that a field in RPS matches expected value.

        Args:
            customer_id: Customer identifier
            field_name: Field name
            expected_value: Expected value

        Returns:
            True if matches, False otherwise
        """
        customer = self.get_customer_record(customer_id)
        if not customer:
            return False

        actual_value = customer.get(field_name, "")
        matches = actual_value == expected_value

        logger.info(
            f"RPS field verification: {field_name} "
            f"expected='{expected_value}' actual='{actual_value}' matches={matches}"
        )

        return matches


# Singleton instance
_rps_service = None


def get_rps_service() -> RPSService:
    """Get or create singleton RPS service"""
    global _rps_service
    if _rps_service is None:
        _rps_service = RPSService()
    return _rps_service
