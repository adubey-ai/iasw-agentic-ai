"""
Confidence Scorer Agent
Generates confidence scores for extracted data vs requested changes
"""

import logging
import os
from typing import List
from backend.models.schemas import (
    FieldConfidence,
    ConfidenceScoreCard,
    ChangeRequest,
    DocumentProcessingResult
)
from backend.utils.llm_handler import get_llama_handler

logger = logging.getLogger(__name__)

FAST_MODE = os.getenv("IASW_FAST_MODE", "1") != "0"


class ConfidenceScorerAgent:
    """
    Scores confidence of document data matching change request.
    """

    def __init__(self):
        self.llm_handler = None
        logger.info("ConfidenceScorerAgent initialized")

    def _get_llm(self):
        if self.llm_handler is None:
            self.llm_handler = get_llama_handler()
        return self.llm_handler

    def generate_score_card(
        self,
        request: ChangeRequest,
        doc_result: DocumentProcessingResult,
        request_id: str
    ) -> ConfidenceScoreCard:
        logger.info(f"Generating confidence score card for request {request_id}")

        field_scores = self._score_fields(request, doc_result)
        overall_confidence = self._calculate_overall_confidence(field_scores, doc_result)
        recommendation = self._determine_recommendation(overall_confidence, doc_result.forgery_detected, field_scores)

        ai_summary = self._generate_summary(
            request, doc_result, field_scores, overall_confidence, recommendation
        )

        score_card = ConfidenceScoreCard(
            request_id=request_id,
            overall_confidence=overall_confidence,
            field_scores=field_scores,
            forgery_check_passed=not doc_result.forgery_detected,
            forgery_confidence=100.0 - doc_result.forgery_score,
            recommendation=recommendation,
            ai_summary=ai_summary
        )

        logger.info(f"Score card generated: confidence={overall_confidence:.1f}%, recommendation={recommendation}")
        return score_card

    def _score_fields(
        self,
        request: ChangeRequest,
        doc_result: DocumentProcessingResult
    ) -> List[FieldConfidence]:
        field_scores = []
        extracted = doc_result.extracted_data

        if request.change_type.value == "legal_name":
            old_name_extracted = extracted.get("old_name", "")
            old_name_score = self._fuzzy_name_match(request.old_value, old_name_extracted)

            # Boost score if OCR/VL found the name anywhere in the extracted data
            if old_name_score < 50:
                old_name_score = self._search_name_in_all_fields(request.old_value, extracted)

            field_scores.append(FieldConfidence(
                field_name="old_name",
                extracted_value=old_name_extracted or "(not extracted)",
                expected_value=request.old_value,
                confidence_score=old_name_score,
                status=self._score_to_status(old_name_score),
                notes=f"Extracted: '{old_name_extracted}'"
            ))

            new_name_extracted = extracted.get("new_name", "")
            new_name_score = self._fuzzy_name_match(request.new_value, new_name_extracted)

            if new_name_score < 50:
                new_name_score = self._search_name_in_all_fields(request.new_value, extracted)

            field_scores.append(FieldConfidence(
                field_name="new_name",
                extracted_value=new_name_extracted or "(not extracted)",
                expected_value=request.new_value,
                confidence_score=new_name_score,
                status=self._score_to_status(new_name_score),
                notes=f"Extracted: '{new_name_extracted}'"
            ))

            doc_number = extracted.get("document_number", "")
            has_doc_number = len(str(doc_number).strip()) > 0
            field_scores.append(FieldConfidence(
                field_name="document_number",
                extracted_value=doc_number or "(none)",
                expected_value="Any valid number",
                confidence_score=90.0 if has_doc_number else 50.0,
                status="pass" if has_doc_number else "flag",
                notes=f"Document number {'found' if has_doc_number else 'not found'}"
            ))

            issuing_authority = extracted.get("issuing_authority", "")
            has_authority = len(str(issuing_authority).strip()) > 0
            field_scores.append(FieldConfidence(
                field_name="issuing_authority",
                extracted_value=issuing_authority or "(none)",
                expected_value="Valid authority",
                confidence_score=85.0 if has_authority else 40.0,
                status="pass" if has_authority else "flag",
                notes=f"Authority: '{issuing_authority}'"
            ))

        # OCR quality score - be more lenient for VL models
        ocr_score = min(doc_result.ocr_confidence * 1.5, 100.0) if doc_result.ocr_confidence > 0 else 60.0
        field_scores.append(FieldConfidence(
            field_name="ocr_quality",
            extracted_value=f"{doc_result.ocr_confidence:.1f}%",
            expected_value=">50%",
            confidence_score=ocr_score,
            status=self._score_to_status(ocr_score),
            notes=f"OCR confidence: {doc_result.ocr_confidence:.1f}% (VL model augmented)"
        ))

        return field_scores

    def _fuzzy_name_match(self, expected: str, actual: str) -> float:
        """Fuzzy name matching that handles partial matches and common variations."""
        if not actual or not actual.strip():
            return 0.0

        expected_norm = expected.lower().strip()
        actual_norm = actual.lower().strip()

        if expected_norm == actual_norm:
            return 99.0

        if expected_norm in actual_norm or actual_norm in expected_norm:
            return 90.0

        expected_tokens = set(expected_norm.split())
        actual_tokens = set(actual_norm.split())

        if not expected_tokens or not actual_tokens:
            return 0.0

        intersection = expected_tokens.intersection(actual_tokens)

        if len(intersection) == len(expected_tokens):
            return 95.0

        if intersection:
            coverage = len(intersection) / len(expected_tokens)
            return min(coverage * 100.0, 92.0)

        # Substring match on individual tokens
        for et in expected_tokens:
            for at in actual_tokens:
                if et in at or at in et:
                    return 70.0

        return 0.0

    def _search_name_in_all_fields(self, name: str, extracted: dict) -> float:
        """Search for a name across all extracted fields."""
        name_lower = name.lower().strip()
        name_tokens = set(name_lower.split())

        best_score = 0.0
        for key, value in extracted.items():
            if not value or not isinstance(value, str):
                continue
            value_lower = value.lower()

            if name_lower in value_lower:
                best_score = max(best_score, 85.0)
            else:
                value_tokens = set(value_lower.split())
                overlap = name_tokens.intersection(value_tokens)
                if overlap:
                    score = (len(overlap) / len(name_tokens)) * 80.0
                    best_score = max(best_score, score)

        return best_score

    def _score_to_status(self, score: float) -> str:
        if score >= 70.0:
            return "pass"
        elif score >= 40.0:
            return "flag"
        else:
            return "fail"

    def _calculate_overall_confidence(
        self,
        field_scores: List[FieldConfidence],
        doc_result: DocumentProcessingResult
    ) -> float:
        if not field_scores:
            return 0.0

        total_weight = 0.0
        weighted_sum = 0.0

        for field in field_scores:
            weight = 2.5 if field.field_name in ["old_name", "new_name"] else 1.0
            weighted_sum += field.confidence_score * weight
            total_weight += weight

        avg_confidence = weighted_sum / total_weight if total_weight > 0 else 0.0

        if doc_result.forgery_detected:
            avg_confidence *= 0.5

        return round(avg_confidence, 2)

    def _determine_recommendation(
        self,
        overall_confidence: float,
        forgery_detected: bool,
        field_scores: List[FieldConfidence]
    ) -> str:
        if forgery_detected:
            return "reject"

        fail_count = sum(1 for f in field_scores if f.status == "fail")
        name_fields = [f for f in field_scores if f.field_name in ["old_name", "new_name"]]
        name_fail_count = sum(1 for f in name_fields if f.status == "fail")

        # Only reject if both name fields fail
        if name_fail_count == 2:
            return "reject"

        if overall_confidence >= 80.0:
            return "approve"

        if overall_confidence >= 50.0:
            return "manual_review"

        if fail_count >= 2:
            return "reject"

        return "manual_review"

    def _generate_summary(
        self,
        request: ChangeRequest,
        doc_result: DocumentProcessingResult,
        field_scores: List[FieldConfidence],
        overall_confidence: float,
        recommendation: str
    ) -> str:
        if FAST_MODE:
            return self._template_summary(request, overall_confidence, recommendation, doc_result.forgery_detected)
        try:
            llm = self._get_llm()
            summary_data = {
                "change_type": request.change_type.value,
                "old_value": request.old_value,
                "new_value": request.new_value,
                "overall_confidence": overall_confidence,
                "recommendation": recommendation,
                "forgery_detected": doc_result.forgery_detected,
                "field_results": [
                    {"field": f.field_name, "status": f.status, "confidence": f.confidence_score}
                    for f in field_scores
                ]
            }
            return llm.generate_summary(summary_data, {})

        except Exception as e:
            logger.warning(f"Failed to generate LLM summary: {e}")
            return self._template_summary(request, overall_confidence, recommendation, doc_result.forgery_detected)

    def _template_summary(self, request, confidence, recommendation, forgery_detected) -> str:
        doc_status = "FORGED document detected" if forgery_detected else "Document verified"
        return (
            f"{doc_status}. "
            f"Name change from '{request.old_value}' to '{request.new_value}' "
            f"has {confidence:.1f}% confidence. "
            f"Recommendation: {recommendation.upper()}."
        )
