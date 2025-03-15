import logging
import re

from app.agent.extraction_state import DocumentValidationDetails
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
            max_tokens=4000  # Larger context for final compilation
        )
        self.llm_manager = LLMManager(llm_config)
        # Get the primary LLM for report generation
        self.primary_llm = self.llm_manager.get_llm(LLMType.GPT_4O_MINI)

    async def document_processor(self, state: DocumentValidationDetails) -> dict:
        person_identifier = state["document_type"]
        structured_llm = self.primary_llm.with_structured_output(DocumentValidationDetails)
        system_instructions = DOCUMENT_PROCESSOR_DNI.format(
            enterprise=state["enterprise"],
            document_data=state["page_content"],
            person_identifier=state["person"]
        )
        result = structured_llm.invoke([
            SystemMessage(content=system_instructions),
            HumanMessage(
                content="Extrae los datos clave de un documento, particularmente la vigencia (fechas o periodos), empresa, póliza")
        ])
        # print(f"Document Processor Result: {result}")
        state["valid_data"] = result
        date_issuance_format = convertir_fecha_spanish(state["valid_data"]["date_of_issuance"])
        state["valid_data"]["date_of_issuance"] = date_issuance_format
        return state