# app/agent/state/extraction_state.py

from typing import Dict, Any, List, Optional, TypedDict
from typing_extensions import NotRequired


class DocumentSection(TypedDict):
    """A section of extracted document content"""
    title: str
    content: str


class DocumentMetadata(TypedDict):
    """Metadata about the extracted document"""
    total_length: int
    section_count: int
    additional_info: NotRequired[Dict[str, Any]]


class StructuredContent(TypedDict):
    """Structured representation of document content"""
    sections: List[DocumentSection]
    metadata: DocumentMetadata


class ExtractionState(TypedDict):
    """State for document extraction workflow"""
    file_path: str
    success: bool
    error: NotRequired[str]
    extracted_text: NotRequired[str]
    structured_content: NotRequired[StructuredContent]
