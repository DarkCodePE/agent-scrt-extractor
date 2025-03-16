# app/workflow/document_extraction_graph.py

from typing import Dict, Any
from langgraph.graph import StateGraph
from langgraph.constants import START, END
import logging

from app.agent.document_extractor import DocumentExtractorAgent
from app.agent.extraction_state import DocumentValidationDetails
from app.agent.structured_content import StructuredContentExtractor
from app.workflow.builder.base import GraphBuilder

# Configure logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DocumentExtractionGraph(GraphBuilder):
    """Builder for creating document extraction workflow graph"""

    def __init__(self):
        """Initialize workflow builder with necessary agents"""
        super().__init__()
        self.extractor = DocumentExtractorAgent()
        self.segmenter = StructuredContentExtractor()

    def init_graph(self) -> None:
        self.graph = StateGraph(DocumentValidationDetails)

    def add_nodes(self) -> None:
        """Add all required nodes to the graph"""
        # Add the document extraction node
        self.graph.add_node("extract_document", self.extractor.extract_document_content)
        self.graph.add_node("structure_content", self.segmenter.document_processor)

    def add_edges(self) -> None:
        """Define all edges in the graph"""
        # Start -> extract_document
        self.graph.add_edge(START, "extract_document")
        self.graph.add_edge("extract_document", "structure_content")
        # Error handler always ends the workflow
        self.graph.add_edge("structure_content", END)
