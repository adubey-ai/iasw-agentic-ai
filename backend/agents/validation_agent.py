"""
Validation Agent
Validates intake fields against RPS and performs initial checks
"""

import logging
from typing import Dict, List
from backend.models.schemas import ChangeRequest, ValidationResult, ChangeType

logger = logging.getLogger(__name__)


class ValidationAgent:
    """
    Validates change requests against RPS records.

    Responsibilities:
    - Check if customer exists in RPS
    - Verify current value matches RPS record
    - Validate format of new value
    - Check for business rule violations
    """

    def __init__(self, rps_service=None):
        """
        Initialize validation agent.

        Args:
            rps_service: Mock RPS service for record lookup
        """
        self.rps_service = rps_service
        logger.info("ValidationAgent initialized")

    def validate_request(self, request: ChangeRequest) -> ValidationResult:
        """
        Validate a change request.

        Args:
            request: Change request to validate

        Returns:
            ValidationResult with validation outcome
        """
        logger.info(f"Validating request for customer {request.customer_id}")

        errors = []
        warnings = []

        # Check if customer exists in RPS
        rps_record = self._lookup_customer(request.customer_id)
        rps_found = rps_record is not None

        if not rps_found:
            errors.append(f"Customer {request.customer_id} not found in RPS")
            return ValidationResult(
                valid=False,
                errors=errors,
                warnings=warnings,
                rps_record_found=False,
                rps_current_value=None
            )

        # Verify current value matches RPS
        rps_current_value = self._get_current_value(rps_record, request.change_type)

        if rps_current_value != request.old_value:
            warnings.append(
                f"Old value '{request.old_value}' does not match RPS value '{rps_current_value}'. "
                "This may indicate stale data."
            )

        # Validate format of new value
        format_errors = self._validate_format(request.change_type, request.new_value)
        errors.extend(format_errors)

        # Check business rules
        business_warnings = self._check_business_rules(request)
        warnings.extend(business_warnings)

        # Determine overall validity
        valid = len(errors) == 0

        result = ValidationResult(
            valid=valid,
            errors=errors,
            warnings=warnings,
            rps_record_found=rps_found,
            rps_current_value=rps_current_value
        )

        logger.info(f"Validation result: valid={valid}, errors={len(errors)}, warnings={len(warnings)}")
        return result

    def _lookup_customer(self, customer_id: str) -> Dict:
        """
        Look up customer in RPS (mock implementation).

        Args:
            customer_id: Customer identifier

        Returns:
            Customer record or None
        """
        # Mock RPS lookup - in production this would call actual RPS
        mock_customers = {
            "C001": {
                "customer_id": "C001",
                "name": "Priya Sharma",
                "address": "123 Main St, Mumbai",
                "dob": "1990-05-15",
                "email": "priya.sharma@email.com"
            },
            "0001": {
                "customer_id": "0001",
                "name": "Priya Sharma",
                "address": "123 Main St, Mumbai",
                "dob": "1990-05-15",
                "email": "priya.sharma@email.com"
            },
            "C002": {
                "customer_id": "C002",
                "name": "Rahul Kumar",
                "address": "456 Park Ave, Delhi",
                "dob": "1985-08-22",
                "email": "rahul.kumar@email.com"
            },
            "C003": {
                "customer_id": "C003",
                "name": "Tanvi Dubey",
                "address": "789 Lake View, Bangalore",
                "dob": "1995-03-12",
                "email": "tanvi.dubey@email.com"
            }
        }

        return mock_customers.get(customer_id)

    def _get_current_value(self, rps_record: Dict, change_type: ChangeType) -> str:
        """
        Extract current value for the field being changed.

        Args:
            rps_record: RPS customer record
            change_type: Type of change

        Returns:
            Current value
        """
        field_mapping = {
            ChangeType.LEGAL_NAME: "name",
            ChangeType.ADDRESS: "address",
            ChangeType.DATE_OF_BIRTH: "dob",
            ChangeType.CONTACT_EMAIL: "email"
        }

        field_name = field_mapping.get(change_type)
        return rps_record.get(field_name, "")

    def _validate_format(self, change_type: ChangeType, value: str) -> List[str]:
        """
        Validate format of new value.

        Args:
            change_type: Type of change
            value: New value

        Returns:
            List of format errors
        """
        errors = []

        if change_type == ChangeType.LEGAL_NAME:
            if len(value) < 2:
                errors.append("Name must be at least 2 characters")
            if not any(c.isalpha() for c in value):
                errors.append("Name must contain at least one letter")

        elif change_type == ChangeType.CONTACT_EMAIL:
            if "@" not in value or "." not in value:
                errors.append("Invalid email format")

        elif change_type == ChangeType.DATE_OF_BIRTH:
            # Basic date format check
            if not any(sep in value for sep in ["-", "/"]):
                errors.append("Date must contain separators (- or /)")

        return errors

    def _check_business_rules(self, request: ChangeRequest) -> List[str]:
        """
        Check business rules specific to change type.

        Args:
            request: Change request

        Returns:
            List of warnings
        """
        warnings = []

        # Example business rules
        if request.change_type == ChangeType.LEGAL_NAME:
            # Check if names are suspiciously different
            old_parts = set(request.old_value.lower().split())
            new_parts = set(request.new_value.lower().split())
            common = old_parts.intersection(new_parts)

            if not common:
                warnings.append(
                    "Old and new names have no common parts. "
                    "Ensure strong documentation is provided."
                )

        return warnings
