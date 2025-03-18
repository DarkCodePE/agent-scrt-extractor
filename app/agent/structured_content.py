import logging
import re

from langchain_core.messages import SystemMessage, HumanMessage

from app.agent.extraction_state import DocumentValidationDetails, DocumentStructuredContent
from app.agent.prompt import SEGMENTATION_PROMPT, SEGMENTATION_PROMPT_V2, SEGMENTATION_PROMPT_V3
from app.config.config import get_settings
from app.providers.llm_manager import LLMConfig, LLMManager, LLMType

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class StructuredContentExtractor:
    """
    Agente para el procesamiento de documentos PDF.
    Se encarga de identificar la empresa aseguradora, extraer el contenido del documento y procesar los datos clave.
    """

    def __init__(self, settings=None):
        """
        Initialize StructuredContentExtractor with settings.
        Args:
            settings: Optional application settings. If None, will load default settings.
        """
        self.settings = settings or get_settings()
        # Initialize LLM manager with compilation-specific configuration
        llm_config = LLMConfig(
            temperature=0.0,  # Use deterministic output for compilation
            streaming=False,
        )
        self.llm_manager = LLMManager(llm_config)
        # Get the primary LLM for report generation
        self.primary_llm = self.llm_manager.get_llm(LLMType.GPT_4O_MINI)

    async def document_processor(self, state: DocumentValidationDetails) -> dict:
        extracted_text = state["extracted_text"]
        structured_llm = self.primary_llm.with_structured_output(DocumentStructuredContent)
        system_instructions = SEGMENTATION_PROMPT_V3.format(
            extracted_text=extracted_text,
        )
        result = structured_llm.invoke([
            SystemMessage(content=system_instructions),
            HumanMessage(
                content="Extrae los datos clave de un documento, particularmente la vigencia (fechas o periodos), empresa, póliza y retorna un lista segementada de secciones logicas")
        ])
        print(f"Segmented sections: {result}")
        return {"segmented_sections": result}
