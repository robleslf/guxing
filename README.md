[ Documento Original ] (PDF / DOCX / ODT)
         │
         ▼
[ 1. Ingesta y Normalización ] ──► Extracción a formato estructurado (Markdown / JSON con IDs)
         │
         ▼
[ 2. Motor de Traducción Inteligente ] ──► LLM con Glosario + Reglas de Examen + Retención de Código
         │
         ▼
[ 3. Matriz de Alineación ] ──► JSON emparejado: { id: 1, es_gl: "...", zh: "..." }
         │
    ┌────┴────────────────────────┐
    ▼                             ▼
[ 4. Visor Interactivo HTML ]   [ 5. Exportador a PDF ]
(Doble pantalla + hover sync)   (PDF Bilingüe o Chino Anotado)


___


guxing/
├── launcher.py               # Autoinstalador / Lanzador
├── app.py                    # Punto de entrada
├── config.py                 # Gestor seguro de perfiles y rutas del sistema
├── core/
│   ├── __init__.py
│   ├── parser.py             # Extracción de PDF (pymupdf), DOCX, ODT, TXT
│   ├── translator.py         # Motor IA (Gemini, DeepSeek, OpenAI) y batches
│   └── viewer_html.py        # Generador de la plantilla HTML bilingüe interactiva
├── ui/
│   ├── __init__.py
│   ├── theme.py              # Paleta y constantes visuales
│   ├── api_dialog.py         # Ventana modal gestora de APIs (con renombrado)
│   └── main_window.py        # Ventana principal (pantalla completa, Drop Zone, imagen)
└── img/
    ├── guxing-ico.png
    └── guxing-letras.png