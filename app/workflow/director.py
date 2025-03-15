from langgraph.graph import StateGraph

from app.workflow.document_extraction_graph import DocumentExtractionGraph


class GraphDirector:
    """Director que maneja la construcción de grafos"""

    @staticmethod
    def document_extraction() -> StateGraph:
        builder = DocumentExtractionGraph()
        return builder.build()