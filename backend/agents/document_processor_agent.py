"""
Document Processor Agent
Handles OCR extraction, data extraction, and document archival
"""

import logging
import os
import re
import time
import uuid
from pathlib import Path
from typing import Dict
from backend.models.schemas import DocumentProcessingResult
from backend.utils.ocr_processor import get_ocr_processor
from backend.utils.llm_handler import get_llama_handler

logger = logging.getLogger(__name__)

# When IASW_FAST_MODE is enabled, skip multi-minute LLM calls on CPU and
# fall back to regex extraction over the OCR text. Default ON for the demo.
FAST_MODE = os.getenv("IASW_FAST_MODE", "1") != "0"


class DocumentProcessorAgent:
    """
    Processes uploaded documents for change requests.

    Responsibilities:
    - Perform OCR extraction
    - Extract structured data using LLM
    - Detect potential forgery
    - Generate FileNet reference (mock)
    """

    def __init__(self):
        """Initialize document processor agent"""
        self.ocr_processor = get_ocr_processor()
        self.llm_handler = None  # Lazy load
        logger.info("DocumentProcessorAgent initialized")

    def _get_llm(self):
        """Lazy load LLM handler"""
        if self.llm_handler is None:
            self.llm_handler = get_llama_handler()
        return self.llm_handler

    def process_document(
        self,
        file_path: str,
        change_type: str,
        document_type: str
    ) -> DocumentProcessingResult:
        """
        Process a document end-to-end.

        Args:
            file_path: Path to uploaded document
            change_type: Type of change request
            document_type: Type of document

        Returns:
            DocumentProcessingResult with extracted data and analysis
        """
        logger.info(f"Processing document: {file_path}")
        start_time = time.time()

        try:
            # Step 1: Perform OCR
            logger.info("Step 1: Performing OCR extraction...")
            ocr_text, ocr_confidence = self.ocr_processor.process_document(file_path)
            logger.info(f"OCR completed: {len(ocr_text)} chars, confidence={ocr_confidence:.1f}%")

            if FAST_MODE:
                logger.info("Step 2: Extracting structured data (fast mode, regex over OCR)...")
                extracted_data = self._regex_extract(ocr_text, change_type)
                logger.info(f"Extracted data: {list(extracted_data.keys())}")
                forgery_detected, forgery_score = self._heuristic_forgery(ocr_text, ocr_confidence)
                logger.info(f"Forgery check (heuristic): detected={forgery_detected}, score={forgery_score}")
            else:
                logger.info("Step 2: Extracting structured data with Qwen2.5-VL...")
                llm = self._get_llm()
                extracted_data = llm.extract_document_data(ocr_text, change_type, document_type, image_path=file_path)
                logger.info(f"Extracted data: {list(extracted_data.keys())}")

                logger.info("Step 3: Running forgery detection...")
                forgery_result = llm.detect_forgery(ocr_text, ocr_confidence, image_path=file_path)
                forgery_detected = forgery_result.get("forgery_detected", False)
                forgery_score = forgery_result.get("forgery_score", 0.0)
                logger.info(f"Forgery check: detected={forgery_detected}, score={forgery_score}")

            # Step 4: Generate FileNet reference (mock)
            filenet_ref = self._generate_filenet_reference(file_path)
            logger.info(f"FileNet reference: {filenet_ref}")

            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Create result
            document_id = str(uuid.uuid4())
            result = DocumentProcessingResult(
                document_id=document_id,
                extracted_data=extracted_data,
                ocr_confidence=ocr_confidence,
                forgery_detected=forgery_detected,
                forgery_score=forgery_score,
                processing_time_ms=processing_time_ms,
                filenet_reference=filenet_ref
            )

            logger.info(f"Document processing completed in {processing_time_ms}ms")
            return result

        except Exception as e:
            logger.error(f"Error processing document: {str(e)}", exc_info=True)
            raise

    def _regex_extract(self, ocr_text: str, change_type: str) -> Dict:
        """Pull structured fields out of OCR text without calling the LLM.

        Handles the common label patterns in the demo documents. Returns the same
        keys the LLM extractor would produce so downstream scoring is unchanged.
        """
        def grab(patterns):
            for pat in patterns:
                m = re.search(pat, ocr_text, flags=re.IGNORECASE)
                if m:
                    return m.group(1).strip().strip(":,.")
            return ""

        data = {
            "old_name": "",
            "new_name": "",
            "document_date": "",
            "document_number": "",
            "issuing_authority": "",
            "other_details": "",
        }

        if change_type == "legal_name":
            data["old_name"] = grab([
                r"bride[^\n:]*[:\-]\s*([A-Z][A-Za-z .'-]+)",
                r"maiden\s*name[^\n:]*[:\-]\s*([A-Z][A-Za-z .'-]+)",
                r"(?:name\s*of\s*)?wife[^\n:]*[:\-]\s*([A-Z][A-Za-z .'-]+)",
                r"former\s*name[^\n:]*[:\-]\s*([A-Z][A-Za-z .'-]+)",
            ])
            data["new_name"] = grab([
                r"married\s*name[^\n:]*[:\-]\s*([A-Z][A-Za-z .'-]+)",
                r"new\s*name[^\n:]*[:\-]\s*([A-Z][A-Za-z .'-]+)",
                r"name\s*after\s*marriage[^\n:]*[:\-]\s*([A-Z][A-Za-z .'-]+)",
            ])
        elif change_type == "address":
            data["other_details"] = grab([
                r"address[^\n:]*[:\-]\s*(.+)",
                r"residence[^\n:]*[:\-]\s*(.+)",
            ])

        data["document_number"] = grab([
            r"(?:certificate|registration|reference|doc)\s*(?:no\.?|number)[^\n:]*[:\-]\s*([A-Z0-9\-\/]+)",
            r"\bNo\.?\s*[:\-]?\s*([A-Z0-9\-\/]{4,})",
        ])
        data["document_date"] = grab([
            r"(?:date\s*of\s*issue|issued\s*on|dated)[^\n:]*[:\-]?\s*(\d{1,2}[\-\/][A-Za-z0-9]{2,}[\-\/]\d{2,4})",
            r"\b(\d{1,2}\s+[A-Za-z]+\s+\d{4})\b",
        ])
        data["issuing_authority"] = grab([
            r"issued\s*by[^\n:]*[:\-]\s*(.+)",
            r"registrar[^\n:]*[:\-]\s*(.+)",
            r"(Municipal\s+Corporation[^\n]*)",
            r"(Government\s+of[^\n]+)",
        ])
        return data

    def _heuristic_forgery(self, ocr_text: str, ocr_confidence: float):
        """Cheap rule-based forgery signal when the LLM path is disabled."""
        if ocr_confidence < 35 and len(ocr_text) < 50:
            return True, 80.0
        suspicious = 0
        if re.search(r"(copy|specimen|sample)\s+only", ocr_text, re.IGNORECASE):
            suspicious += 1
        if re.search(r"photoshop|edited|draft", ocr_text, re.IGNORECASE):
            suspicious += 1
        score = min(suspicious * 35.0 + max(0.0, 60.0 - ocr_confidence) * 0.5, 95.0)
        return score >= 70.0, float(round(score, 2))

    def _generate_filenet_reference(self, file_path: str) -> str:
        """
        Generate FileNet reference for document archival.
        In production, this would call actual FileNet API.

        Args:
            file_path: Path to document

        Returns:
            FileNet reference ID
        """
        # Mock FileNet archival
        # In production, would upload to FileNet and return real reference
        path = Path(file_path)
        timestamp = int(time.time())
        ref_id = f"FN-{timestamp}-{uuid.uuid4().hex[:8]}"

        logger.info(f"Mock FileNet archival: {path.name} -> {ref_id}")

        return ref_id

    def archive_document(self, file_path: str, metadata: Dict) -> str:
        """
        Archive document to FileNet with metadata.

        Args:
            file_path: Path to document
            metadata: Document metadata

        Returns:
            FileNet reference ID
        """
        # In production, this would:
        # 1. Upload document to FileNet
        # 2. Attach metadata
        # 3. Return reference ID

        logger.info(f"Archiving document with metadata: {metadata}")
        return self._generate_filenet_reference(file_path)
