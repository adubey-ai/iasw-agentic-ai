"""
OCR and Document Processing Utilities
"""

import pytesseract
from PIL import Image
from pdf2image import convert_from_path
import io
import logging
from typing import Tuple, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class OCRProcessor:
    """Handle OCR extraction from documents"""

    def __init__(self):
        """Initialize OCR processor"""
        # Check if tesseract is available
        try:
            pytesseract.get_tesseract_version()
            logger.info("Tesseract OCR initialized successfully")
        except Exception as e:
            logger.warning(f"Tesseract not available: {e}")
            logger.warning("OCR functionality may be limited")

    def process_image(self, image_path: str) -> Tuple[str, float]:
        """
        Extract text from image using OCR.

        Args:
            image_path: Path to image file

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            # Load image
            image = Image.open(image_path)

            # Perform OCR with detailed data for confidence
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)

            # Extract text
            text = pytesseract.image_to_string(image)

            # Calculate average confidence
            confidences = [
                int(conf) for conf in ocr_data["conf"] if conf != "-1"
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            logger.info(f"OCR completed: {len(text)} chars, {avg_confidence:.1f}% confidence")

            return text.strip(), avg_confidence

        except Exception as e:
            logger.error(f"Error processing image: {str(e)}")
            raise

    def process_pdf(self, pdf_path: str, page_num: int = 0) -> Tuple[str, float]:
        """
        Extract text from PDF using OCR.

        Args:
            pdf_path: Path to PDF file
            page_num: Page number to process (0-indexed)

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        try:
            # Convert PDF page to image
            images = convert_from_path(pdf_path, first_page=page_num + 1, last_page=page_num + 1)

            if not images:
                raise ValueError(f"Could not extract page {page_num} from PDF")

            # Process first (only) image
            image = images[0]

            # Perform OCR
            ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
            text = pytesseract.image_to_string(image)

            # Calculate confidence
            confidences = [
                int(conf) for conf in ocr_data["conf"] if conf != "-1"
            ]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

            logger.info(f"PDF OCR completed: {len(text)} chars, {avg_confidence:.1f}% confidence")

            return text.strip(), avg_confidence

        except Exception as e:
            logger.error(f"Error processing PDF: {str(e)}")
            raise

    def process_document(self, file_path: str) -> Tuple[str, float]:
        """
        Process document (auto-detect type and extract text).

        Args:
            file_path: Path to document

        Returns:
            Tuple of (extracted_text, confidence_score)
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        logger.info(f"Processing document: {path.name} ({extension})")

        if extension in [".pdf"]:
            return self.process_pdf(file_path)
        elif extension in [".jpg", ".jpeg", ".png", ".tiff", ".bmp"]:
            return self.process_image(file_path)
        else:
            raise ValueError(f"Unsupported file type: {extension}")

    def extract_document_metadata(self, file_path: str) -> dict:
        """
        Extract metadata from document file.

        Args:
            file_path: Path to document

        Returns:
            Dictionary of metadata
        """
        path = Path(file_path)

        metadata = {
            "filename": path.name,
            "extension": path.suffix.lower(),
            "size_bytes": path.stat().st_size,
            "size_mb": round(path.stat().st_size / (1024 * 1024), 2),
        }

        # Try to get image dimensions if applicable
        try:
            if metadata["extension"] in [".jpg", ".jpeg", ".png", ".bmp"]:
                with Image.open(file_path) as img:
                    metadata["width"] = img.width
                    metadata["height"] = img.height
                    metadata["format"] = img.format
        except Exception:
            pass

        return metadata


def get_ocr_processor() -> OCRProcessor:
    """Get OCR processor instance"""
    return OCRProcessor()
