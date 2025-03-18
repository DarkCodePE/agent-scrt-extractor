# app/agent/state/extraction_state.py

from typing import Dict, Any, List, Optional, TypedDict

from fastapi import UploadFile
from typing_extensions import NotRequired


class PersonValidationDetails(TypedDict):
    """Person details from the document"""
    full_name: str
    document_number: str
    coverage_start_date: str
    type_document: str

class DocumentStructured(TypedDict):
    start_date_validity: str
    end_date_validity: str
    validity: str
    policy_number: str
    company: str
    insurance_company: str
    person_by_policy: List[PersonValidationDetails]
    signatories: List[str]

class DocumentStructuredContent(TypedDict):
    content: List[DocumentStructured]


class DocumentValidationDetails(TypedDict):
    """Validation details extracted from the document"""
    start_date_validity: str
    end_date_validity: str
    validity: str
    policy_number: str
    company: str
    date_of_issuance: str
    person_by_policy: List[PersonValidationDetails]
    signatories: List[str]
    extracted_text: str
    file: UploadFile
    person_name: str
    structured_content: str
    file_name: str
    segmented_sections: List[DocumentStructuredContent]
