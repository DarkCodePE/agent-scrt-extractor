from typing import Dict, Any, Optional
from pathlib import Path
import logging
from mistralai import Mistral
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser
import os
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class DocumentExtractorAgent:
    """
    Agent for extracting and processing document content using Mistral OCR.
    Handles document extraction, text processing, and content structuring.
    """

    def __init__(self):
        """Initialize DocumentExtractorAgent with Mistral client"""
        self.mistral_api_key = os.getenv("MISTRAL_API_KEY")
        if not self.mistral_api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required")

        self.client = Mistral(api_key=self.mistral_api_key)
        logger.info("DocumentExtractorAgent initialized with Mistral API")

    async def extract_document_content(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main extraction function - processes PDF document using Mistral OCR and extracts content.

        Args:
            state: Current state dictionary containing file_path

        Returns:
            Updated state with extracted text and structured content
        """
        logger.info("Starting document extraction process")
        pdf_path = state.get("file_path")

        if not pdf_path or not Path(pdf_path).exists():
            logger.error(f"Invalid file path: {pdf_path}")
            return {
                "success": False,
                "error": f"File not found: {pdf_path}",
                "extracted_text": None,
                "structured_content": None
            }

        try:
            # Extract document text using Mistral OCR
            extracted_text = await self._process_with_mistral_ocr(pdf_path)

            # Process extracted content to structure it
            structured_content = await self._structure_extracted_content(extracted_text)

            logger.info(f"Successfully extracted and structured content from {pdf_path}")

            # Return updated state
            return {
                "success": True,
                "extracted_text": extracted_text,
                "structured_content": structured_content,
                "file_path": pdf_path
            }

        except Exception as e:
            logger.error(f"Error during document extraction: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "extracted_text": None,
                "structured_content": None
            }

    async def _process_with_mistral_ocr(self, pdf_path: str) -> str:
        """
        Process PDF document with Mistral OCR API.

        Args:
            pdf_path: Path to the PDF file

        Returns:
            Extracted text content
        """
        logger.info(f"Processing document with Mistral OCR: {pdf_path}")

        try:
            # Upload the file to Mistral
            uploaded_pdf = self.client.files.upload(
                file={
                    "file_name": Path(pdf_path).name,
                    "content": open(pdf_path, "rb"),
                },
                purpose="ocr"
            )

            # Get a signed URL to access the file
            signed_url = self.client.files.get_signed_url(file_id=uploaded_pdf.id)

            # Process the document with OCR
            ocr_response = self.client.ocr.process(
                model="mistral-ocr-latest",
                document={
                    "type": "document_url",
                    "document_url": signed_url.url,
                }
            )

            # Combine text from all pages
            text = "\n\n".join([page.markdown for page in ocr_response.pages])

            logger.info(f"Successfully extracted {len(text)} characters from document")
            return text

        except Exception as e:
            logger.error(f"Error in Mistral OCR processing: {str(e)}")
            raise

    async def _structure_extracted_content(self, text: str) -> Dict[str, Any]:
        """
        Process the raw extracted text to identify key sections and structure content.

        Args:
            text: Raw extracted text from OCR

        Returns:
            Structured content with identified sections
        """
        logger.info("Structuring extracted document content")

        # Simple structure example - this can be enhanced with better section detection
        structured_content = {
            "sections": [],
            "metadata": {
                "total_length": len(text),
                "section_count": 0
            }
        }

        # Simple section detection based on newlines and potential headers
        current_section = ""
        current_title = "Untitled Section"

        for line in text.split('\n'):
            # Simple heuristic for potential section headers (short lines that end with colon or are ALL CAPS)
            is_potential_header = (len(line.strip()) < 50 and line.strip().endswith(':')) or line.isupper()

            if is_potential_header and current_section:
                # Save the previous section
                structured_content["sections"].append({
                    "title": current_title,
                    "content": current_section.strip()
                })
                current_section = ""
                current_title = line.strip()
            else:
                current_section += line + "\n"

        # Add the last section
        if current_section:
            structured_content["sections"].append({
                "title": current_title,
                "content": current_section.strip()
            })

        structured_content["metadata"]["section_count"] = len(structured_content["sections"])

        logger.info(f"Identified {len(structured_content['sections'])} sections in document")
        return structured_content