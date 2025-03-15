from typing import List

from langgraph.constants import START, END
from langgraph.graph import StateGraph
from langgraph.types import Send

from app.agent.document import DocumentAgent
from app.agent.judge import JudgeAgent

from app.agent.signature import SignatureAgent
from app.agent.single_logo import SingleLogoAgent
from app.agent.state.state import OverallState, PageContent
from app.agent.utils.pdf_utils import extract_pdf_text
from app.agent.utils.util import semantic_segment_pdf_with_llm, extract_name_enterprise, \
    semantic_segment_pdf_with_llm_v2, count_pdf_pages, semantic_segment_pdf_with_llm_v3

from app.workflow.builder.base import GraphBuilder
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DiagnosisValidationGraph(GraphBuilder):
    def __init__(self):
        super().__init__()
        self.document = DocumentAgent()
        self.logo = SingleLogoAgent()
        self.signature = SignatureAgent()
        self.judge = JudgeAgent()
        self.document_graph = None
        self.PAGE_PER_TIME = 5

    def init_graph(self) -> None:
        self.graph = StateGraph(OverallState)

    def add_nodes(self) -> None:
        self.graph.add_node("extract_pages_content",
                            self.extract_pages_content)
        self.graph.add_node("detect_signatures", self.signature.verify_signatures)
        self.graph.add_node("handle_invalid_document", self.handle_invalid_document)
        self.graph.add_node("validate_page", self.document_graph)
        self.graph.add_node("compile_verdict", self.judge.summarize)
        self.graph.add_node("logo_detection", self.logo.verify_logo)

    def add_edges(self) -> None:
        self.graph.add_edge(START, "logo_detection")
        self.graph.add_edge("logo_detection", "extract_pages_content")
        self.graph.add_conditional_edges("extract_pages_content",
                                         self.generate_pages_to_validate,
                                         ["validate_page", "handle_invalid_document"]
                                         )
        self.graph.add_edge("validate_page", "compile_verdict")
        self.graph.add_edge("compile_verdict", END)
        self.graph.add_edge("handle_invalid_document", END)

    async def extract_pages_content(self, state: OverallState) -> dict:
        """Extracts page content using semantic segmentation with LLM."""
        pdf_file = state["file"]
        #validate file structure
        # Primero extraer el texto para validar el formato
        full_text = await extract_pdf_text(pdf_file)

        # Validar si el documento parece ser un SCTR
        is_valid_sctr = await self.validate_sctr_document(full_text)
        if not is_valid_sctr:
            # Si no es un documento SCTR válido, retornar un estado especial con page_contents nulo
            return {
                "page_contents": None,
            }

        total_pages = await count_pdf_pages(pdf_file)
        if total_pages > 1:
            # Use semantic segmentation instead of page-based extraction
            segmented_sections = await semantic_segment_pdf_with_llm_v2(pdf_file,
                                                                        self.document.llm_manager)  # Use LLM for segmentation
        else:
            # Use page-based extraction
            segmented_sections = await semantic_segment_pdf_with_llm_v3(pdf_file,
                                                                        self.document.llm_manager)

        try:
            enterprise = await extract_name_enterprise(state["file"])
        except Exception as e:
            enterprise = ""

        person = state["worker"]
        document_type = state["worker_type"]
        user_date = state["user_date"]
        page_content_list: List[PageContent] = []
        for i, content in enumerate(segmented_sections):  # Iterate over segmented sections now
            page_num = i + 1
            page_content = PageContent(
                page_num=page_num,  # Rethink page_num - maybe section_num?
                page_content=content,
                valid_data=None,
                pages_verdicts=None,
                enterprise=enterprise,
                person=person,
                reference_date=user_date,
                document_type=document_type
            )
            page_content_list.append(page_content)

        print("Page content list: ", page_content_list)
        return {"page_contents": page_content_list}

    def generate_pages_to_validate(self, state: OverallState) -> list[Send]:
        """Creates Send objects for each PageContent in OverallState['page_contents'] for parallel validation."""
        # Verificar si el documento es válido
        if state.get("page_contents") is None or not state.get("page_contents"):
            logger.warning("Documento no válido o no es un SCTR: page_contents es None")
            return [Send("handle_invalid_document", {})]

        return [
            Send("validate_page",
                 {"page_content": page["page_content"],
                  "enterprise": page["enterprise"],
                  "valid_data": page["valid_data"],
                  "page_num": page["page_num"],
                  "person": page["person"],
                  "reference_date": page["reference_date"],
                  "document_type": page["document_type"]}
                 )
            for page in state["page_contents"]
        ]

    async def validate_sctr_document(self, text: str) -> bool:
        """
        Valida si el texto extraído parece ser de un documento SCTR.

        Args:
            text: Texto extraído del documento

        Returns:
            bool: True si parece ser un SCTR, False en caso contrario
        """
        # Palabras clave que deberían estar en un documento SCTR
        sctr_keywords = [
            "seguro complementario de trabajo de riesgo",
            "sctr",
            "constancia",
            "póliza",
            "riesgos laborales",
            "accidente de trabajo",
            "cobertura",
            "vigencia",
            "asegurado"
        ]

        # Convertir texto a minúsculas para búsqueda insensible a mayúsculas/minúsculas
        text_lower = text.lower()

        # Contar cuántas palabras clave aparecen en el texto
        keyword_matches = sum(1 for keyword in sctr_keywords if keyword in text_lower)

        # Si hay suficientes coincidencias, considerar que es un SCTR
        return keyword_matches >= 3

    def handle_invalid_document(self, state: OverallState) -> dict:
        """Maneja documentos inválidos y proporciona respuesta de error."""
        logger.warning("Documento inválido. No es un SCTR o no tiene formato esperado.")
        return {
            "final_verdict": {
                "verdict": False,
                "reason": "El documento proporcionado no es un SCTR válido",
                "details": {
                    "logo_validation_passed": False,
                    "validity_validation_passed": False,
                    "signature_validation_passed": False,
                    "person_validation_passed": False
                }
            }
        }