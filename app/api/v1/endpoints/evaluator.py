import tempfile
from datetime import datetime
from typing import List, Tuple
import re

import cv2
from fastapi import FastAPI, UploadFile, File, HTTPException, APIRouter, Depends, Form
from sqlalchemy import desc
from sqlalchemy.orm import Session
import fitz
import numpy as np

from app.agent.extraction_state import DocumentValidationDetails
from app.config.database import get_db
import os
import logging
from langchain_community.document_loaders import PyPDFLoader


from app.workflow.document_graph import document_graph

logger = logging.getLogger(__name__)

# Verificar que la variable esté configurada
router = APIRouter(prefix="/document", tags=["document"])

@router.post("/v2/validate", response_model=dict)
async def validate_document(
        file: UploadFile = File(...),
        person_name: str = Form(...),
        user_date: str = Form(None),
        db: Session = Depends(get_db),
):
    """
    Validates a PDF document using the complete validation workflow.

    Args:
        file: PDF file to validate
        db: Database session

    Returns:
        Dict containing complete validation results
        :param file:
        :param person_name:
    """
    try:
        # Verify file type
        if not file.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail="Only PDF files are accepted"
            )

        # Validate and normalize person_name
        input_value = person_name.strip()
        if not input_value:
            raise HTTPException(
                status_code=400,
                detail="Person name or DNI is required"
            )

        # Determine if the input is a DNI (8 digits) or a name
        is_dni = bool(re.match(r'^\d{8}$', input_value))

        # Different formatting based on type
        if is_dni:
            # Store the DNI directly
            input_type = "dni"
            normalized_value = input_value
            logger.info(f"Identified input as DNI: {normalized_value}")
        else:
            # Format as name - convert to uppercase and normalize spaces
            input_type = "name"
            normalized_value = " ".join(input_value.upper().split())
            logger.info(f"Identified input as name: {normalized_value}")

        # Execute workflow
        logger.info(f"Starting document validation: {file.filename}")
        state = DocumentValidationDetails(file=file, person_name=person_name)
        component = document_graph.compile()
        result = await component.ainvoke(state)
        # Format response
        response = {
            "extracted_text": result["extracted_text"],
            "component": result["structured_content"],
            "person_name": result["person_name"],
            "segmented_sections": result["segmented_sections"]
        }
        return response

    except Exception as e:
        logger.error(f"Error in document validation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}"
        )
