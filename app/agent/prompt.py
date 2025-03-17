SEGMENTATION_PROMPT = """
**Input Document Data:**
"document_data":  {extracted_text}

Realice una segmentación semántica en este {extracted_text} para dividirlo en secciones lógicas y semánticamente distintas que pueden abarcar **múltiples páginas originales**.
, luego analiza la información clave del siguiente documento, centrándote en las siguientes prioridades: vigencia, empresa, póliza, logo, firma y lista de oersonas aseguradas.

 Identifique las secciones basándose en:

-Títulos de documento y encabezados que indican el inicio de una nueva sección. Detecte variaciones como «CONSTANCIA», «CONSTANCIA Nº», o frases como «Seguro Complementario de Trabajo de Riesgo». Aunque no aparezca un número, trate el título como un encabezamiento de sección.
-Encabezamiento/Información de la empresa: Busque los datos de la empresa (por ejemplo, «Oficina Principal», «Central Administrativa», «RUC:», «VIGENCIA:», «ACTIVIDAD:», «Fecha de emisión:», «Fecha de firma:», «Número de póliza:», «Nombre de la empresa:») y las fechas que suelen aparecer en la parte superior de la página.
-Información del destinatario: Identifique los saludos o bloques de direcciones, como «Señores», «Presente.-», o variantes similares.
-Línea de referencia: Detecta secciones que comienzan con «Ref:» o marcadores similares.
-Renuncia/Notas: Identifique cualquier texto que comience con un asterisco (*) o que contenga frases clave como «No se brindara cobertura» como una sección de descargo de responsabilidad o nota distinta.
-Saludo: Busque saludos comunes como «Estimados Señores:».
-Contenido del cuerpo principal: Agrupe párrafos explicativos, detalles contractuales o información sobre políticas.
-Tablas de datos: Identifique las secciones de datos estructurados. Aunque el encabezamiento de la tabla sea diferente (por ejemplo, «Nro. Nombres Apellido Paterno Apellido Materno Nro. Documento"), detecte filas con ordenación numérica y datos personales para segmentar la tabla como sección independiente.
-Pie de página/Firmas: Capture la información de conclusión, como frases de despedida, nombres, funciones (por ejemplo, «GERENTE»), fechas y direcciones web.


# Analiza la información clave del siguiente documento basándose en:

1. **Comprender el Documento**: Lee completamente el documento para entender su contenido y estructura.
2. **Buscar la Vigencia**: Identifica todas las menciones de fechas o periodos temporales que indiquen la vigencia del documento.
3. **Fecha de emisión**: Busca la fecha de emisión del documento, si se encuentra, normalmente se encuentra en la parte superior del documento, pero puede estar en cualquier lugar.
3. **Compañia aseguradora**: Busca el nombre de la aseguradora que emite el documento, tienes que guardar el nombre de la empresa en el campo "insurance_company"
4. **Identificar la Empresa**: Localiza cualquier mención del nombre de una empresa o razon social que pudiera ser responsable del documento y que esta asociada a un poliza.
5. **Encontrar Información de la Póliza**: Busca números o identificadores que se mencionen junto a las palabras 'póliza' o 'Póliza de Pensiones'.
6. **Encontrar Persona Aseguradas**:
   - Busca en el documento la lista de personas aseguradas.

# Output Format

Produce una respuesta estructurada en formato JSON con las siguientes claves por cada seccion encontrada:
- "validity": [rango_fechas_o_null],
- "start_date_validity": [fecha_inicio_o_null],
- "end_date_validity": [fecha_fin_o_null],
- "insurance_company": [nombre_de_aseguradora_o_null],
- "company": [nombre_empresa_o_rason_social_o_null],
- "policy_number": [numeros_de_poliza_o_null],
- "person_by_policy": [person_by_policy_o_null],

# Notes

- Indica la ausencia de alguno de los elementos requeridos con el valor null si dicha información no está claramente especificada en el documento.
- La exactitud en la extracción de información y la claridad de los términos es prioritaria para asegurar la utilidad del resultado.
"""

SEGMENTATION_PROMPT_V2 = """
   Analyze the following compiled text {extracted_text} representing an entire PDF document, which was extracted page by page using an LLM. Now, perform semantic segmentation on this **compiled text** to divide it into logical, semantically distinct sections that may span **across multiple original pages**.

   **Compiled Text from the Entire PDF Document (Extracted page by page):**
   [Start Compiled Text]
   {extracted_text}
   [End Compiled Text]

   Identify sections based on:
   
   Usually the section starts with an issue date at the top of the sheet, you should take this detail into account to know if it is a new section. 
   Document titles and headings that indicate the start of a new section. 
   Detect for variations such as “CONSTANCIA”, “CONSTANCIA Nº”, or phrases such as “Seguro Complementario de Trabajo de Riesgo”. Even if a number does not appear, it is an indication of a new section.
   Header/Company Information: Look for company details (e.g., "Oficina Principal", "Central Administrativa", "RUC:", "VIGENCIA:", "ACTIVIDAD:", "Issue Date:", "Signature Date:", "Policy Number:", "Company Name:"") and dates that are typically at the top of the page.
   Recipient Information: Identify salutations or address blocks, such as "Señores", "Presente.-", or similar variants.
   Reference Line: Detect sections that begin with "Ref:" or similar markers.
   Disclaimer/Notes: Identify any text that begins with an asterisk (*) or contains key phrases like "No se brindara cobertura" as a distinct disclaimer or note section.
   Salutation/Greeting: Look for common greetings like "Estimados Señores:".
   Main Body Content: Group explanatory paragraphs, contractual details, or policy information.
   Tables of Data: Identify structured data sections. Even if the table header differs (for instance, "Nro. Nombres Apellido Paterno Apellido Materno Nro. Documento"), detect rows with numerical ordering and personal data to segment the table as an independent section.
   Footer/Signatures: Capture concluding information such as sign-off phrases, names, roles (e.g., "GERENTE"), dates, and web addresses.

   Ensure that:
   **Multi-Page Sections Allowed:** Sections in the output list *can* contain text extracted from multiple pages if they represent a single semantic unit (like a multi-page table or a body text section spanning pages).
   **Single Table Section:**  A table that spans multiple pages should be represented as **one single string** in the output list, containing all the text content of the entire table.
   **Grouping Short/Related Sections:** As before, group very short, dependent phrases within larger sections.
   **Minimal Segmentation:** If the document is very simple and no clear semantic sections are identifiable beyond the entire document, return a **list containing the entire extracted text content of the *entire document* as a single string element.*
   The segmentation is flexible enough to account for slight variations in wording and layout across different documents.
   If some parts are very short and logically belong to a larger section (e.g., "Presente.-" next to "Señores"), they should be combined.
   If no clear distinct sections are identifiable beyond the entire text, return a list with the entire text content as a single section.
   If the issue date is detected in other pages, include it in the text output as part of the header or a separate section.
   
   #output_format
   # Analyze separate logical sections based on:
   
    1. **Understanding the Document**: Read the document completely to understand its content and structure.
    2. **Find the Validity**: Identify all mentions of dates or time periods that indicate the validity of the document.
    3. **Date of Issue**: Look for the date of issue of the document, if found, usually found at the top of the document, but can be anywhere.
    3. **Insurance company**: Look for the name of the insurance company issuing the document, you have to store the company name in the field “insurance_company”.
    4. **Company Identification**: Locate any mention of a company name or company name that could be responsible for the document and that is associated with a policy.
    5. **Find Policy Information**: Search for numbers or identifiers that are mentioned next to the words 'policy' or 'Pension Policy'.
    6. **Find Insured Person**:
       - Search the document for the list of insured persons.
       
   the result should be a list of logical sections separated by policy number, with the following keys :
    - "validity": [rango_fechas_o_null],
    - "start_date_validity": [fecha_inicio_o_null],
    - "end_date_validity": [fecha_fin_o_null],
    - "insurance_company": [nombre_de_aseguradora_o_null],
    - "company": [nombre_empresa_o_rason_social_o_null],
    - "policy_number": [numeros_de_poliza_o_null],
    - "person_by_policy": [person_by_policy_o_null],
   """

SEGMENTATION_PROMPT_V3 = """
   Analyze the following compiled text {extracted_text} representing an entire PDF document, which was extracted page by page using an LLM. Now, perform semantic segmentation on this **compiled text** to divide it into logical, semantically distinct sections that may span **across multiple original pages**.

   **Compiled Text from the Entire PDF Document (Extracted page by page):**
   [Start Compiled Text]
   {extracted_text}
   [End Compiled Text]

   Identify sections based on rules:

    ## 1. Rules for Document Start/New Section
    - If a page begins with a date in a standard format (`DD/MM/YYYY`, `DD-MM-YYYY`, etc.) followed by a title such as **"CONSTANCIA"**, **"CERTIFICADO"**, or similar, this marks the start of a new document or main section.
    - If a reference number, certificate number, or code (e.g., **"SCTR7039077"**, **"MP/2022/6440824"**, **"POS-EPS - ATS - C - 2620087"**) appears alongside a title, this indicates the beginning of a new document.
    - Any text appearing after a document header and before the next header should be considered part of that section.
    
    ## 2. Header and Company Information
    - Group all header information into a single section, including:
      - **Name of the insurance company** (`Rimac`, `Mapfre`, `Sanitas`, `La Positiva`, etc.)
      - **Document issuance date**
      - **Certificate/policy number**
      - **Name of the insured entity (company)**
      - **Company's tax identification number (RUC)**
      - **Validity period** (start and end dates)
      - **Economic activity**
      - **Address or risk location**
    
    ## 3. Identification of Policies and Coverage
    - Consider as a separate section any information detailing:
      - **SCTR Pension Policy Number**
      - **SCTR Health Policy Number**
      - **Contract number**
      - **Coverage description**
      - **Any explanatory paragraph about the scope of the insurance**
    
    ## 4. List of Insured Individuals
    - **Tables of insured individuals** should be identified as a complete section, even if they span multiple pages.
    - Identify **table headers** (`"No."`, `"First Name"`, `"Last Name"`, `"Document Number"`, etc.).
    - A table should be kept as a single unit, regardless of the number of pages it occupies.
    - If there are multiple **tables separated by titles or subtitles** (such as `"SEDE: PRINCIPAL"`), each table should be considered a **separate section**.
    
    ## 5. Notes, Exemptions, and Limitations
    - Blocks of text starting with **asterisks (`*`), "Note:", "NOTA:"** or similar should be treated as **note sections**.
    - Text containing phrases such as **"Coverage will not be provided"** should be identified as **exemptions or limitations**.
    - Paragraphs explaining **specific conditions** should be grouped in this section.
    
    ## 6. Signatures and Validation
    - Identify as the **final section** the part containing:
      - Phrases such as **"We issue this certificate at the request of our client..."**
      - **Digital signatures** or names of signatories
      - **Positions or titles** of the signatories
      - **Place and date** of signing
      - **QR codes** or references for document validation
    
    ## 7. Continuity Between Pages
    - If a page begins **without a clear header or date**, and appears to be a continuation of the previous page (e.g., **continuation of a table**), it should be considered part of the **previous section**.
    - Identify **headers or footers** that repeat across multiple pages and **exclude them** from the main semantic segmentation.
    
    ## 8. Rules for Multiple Documents
    - If the file contains **multiple distinct documents** (identifiable by separate titles such as `"CONSTANCIA"` followed by different dates), each document should **be segmented separately**.
    - When a pattern indicating a new document is detected (**new date + new title + new company information**), **start a new main segment**.
    
    ## 9. Rule Prioritization
    1. **First**, identify the boundaries of complete documents.
    2. **Then**, identify the main sections within each document.
    3. **Finally**, apply detailed segmentation to tables and text blocks.
    
    ## 10. Rule for Simple Documents
    - If, after applying all the previous rules, **only one section** is identified, return the entire text as a **single segment**.
    ## 11. Rule for multiple receipts in the same document
    - If the document contains different record numbers (e.g., "CONSTANCIA Nº 4440435" y "CONSTANCIA Nº 4440429"), each must be treated as a separate document, even when:
      * They refer to the same company
      * They share the same period of validity
      * They include the same list of workers
      * The data tables are identical
    - The records must be differentiated by:
      * Different certificate number * Different type of coverage (PENSION)
      Different type of coverage (PENSION vs. HEALTH) * Different policy or contract number
      * Different policy or contract number
    - Each record should be segmented as a separate document with its own set of fields in the final output.
    - A signature or a “No other particulars” section followed by a new header with date and record number clearly indicates the end of one record and the beginning of another.
    
   Ensure that:
   **Multi-Page Sections Allowed:** Sections in the output list *can* contain text extracted from multiple pages if they represent a single semantic unit (like a multi-page table or a body text section spanning pages).  
   **Single Table Section:**  A table that spans multiple pages should be represented as **one single string** in the output list, containing all the text content of the entire table.
   **Grouping Short/Related Sections:** As before, group very short, dependent phrases within larger sections.
   **Minimal Segmentation:** If the document is very simple and no clear semantic sections are identifiable beyond the entire document, return a **list containing the entire extracted text content of the *entire document* as a single string element.*
   The segmentation is flexible enough to account for slight variations in wording and layout across different documents.
   If some parts are very short and logically belong to a larger section (e.g., "Presente.-" next to "Señores"), they should be combined.
   If no clear distinct sections are identifiable beyond the entire text, return a list with the entire text content as a single section.
   If the issue date is detected in other pages, include it in the text output as part of the header or a separate section.
   
   #output_format
   # Analyze separate logical sections based on:
   
    1. **Understanding the Document**: Read the document completely to understand its content and structure.
    2. **Find the Validity**: Identify all mentions of dates or time periods that indicate the validity of the document.
    3. **Date of Issue**: Look for the date of issue of the document, if found, usually found at the top of the document, but can be anywhere.
    3. **Insurance company**: Look for the name of the insurance company issuing the document, you have to store the company name in the field “insurance_company”.
    4. **Identification of the Company**: Locate any mention of a company name or company name that could be responsible for the document and that is associated with a policy.
    5. **Find Policy Information**: Search for numbers or identifiers that are mentioned next to the words 'policy' or 'Pension Policy'.
    6. **Find Insured Person**:
       - Search the document for the list of insured persons.
       
   the result should be a list of logical sections separated by policy number, with the following keys :
    - "validity": [rango_fechas_o_null],
    - "start_date_validity": [fecha_inicio_o_null],
    - "end_date_validity": [fecha_fin_o_null],      
    - "insurance_company": [nombre_de_aseguradora_o_null],
    - "company": [nombre_empresa_o_rason_social_o_null],
    - "policy_number": [numeros_de_poliza_o_null],
    - "person_by_policy": [person_by_policy_o_null],
    - "signatories": [lista_de_nombres_y_cargos_de_firmantes]            
   """