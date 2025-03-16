from typing import Dict, Any, Optional
from pathlib import Path
import logging

from fastapi import UploadFile
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
        file = state.get("file")

        # Extract document text using Mistral OCR
        extracted_text = await self._process_with_mistral_ocr(file)

        # Process extracted content to structure it
        structured_content = await self._structure_extracted_content(extracted_text)

        logger.info(f"Successfully extracted and structured content from {structured_content}")

        # Return updated state
        return {
            "extracted_text": extracted_text,
            "structured_content": structured_content,
            "file_name": file.filename,
        }

    async def _process_with_mistral_ocr(self, file: UploadFile) -> str:
        """Process PDF document with Mistral OCR API."""
        logger.info(f"Processing document with Mistral OCR: {file.filename}")

        # Asegurarse de que estamos al inicio del archivo
        await file.seek(0)
        pdf_content = await file.read()

        try:
            # Subir el archivo a Mistral usando el mismo formato de la documentación
            uploaded_pdf = self.client.files.upload(
                file={
                    "file_name": file.filename,
                    "content": pdf_content,
                },
                purpose="ocr"
            )

            # Obtener la URL firmada para acceder al archivo
            signed_url = self.client.files.get_signed_url(file_id=uploaded_pdf.id, expiry=1)

            # Procesar el documento con OCR
            from mistralai import DocumentURLChunk

            ocr_response = self.client.ocr.process(
                document=DocumentURLChunk(document_url=signed_url.url),
                model="mistral-ocr-latest"
            )

            # Combinar texto de todas las páginas
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

        structured_content = {
            "raw_text": text,
            "metadata": {
                "total_length": len(text),
                "document_type": "SCTR"
            }
        }

        logger.info(
            f"Basic document structuring complete - identified as {structured_content['metadata']['document_type']}")

        return structured_content
