&lt;p align="center"&gt;
&lt;img src="img/guxing-letras.png" alt="Guxing Logo" width="320" /&gt;
&lt;/p&gt;

&lt;p align="center"&gt;
&lt;strong&gt;Plataforma Inteligente de Traducción, Alineación y Lectura Bilingüe de Documentos&lt;/strong&gt;
&lt;/p&gt;

&lt;p align="center"&gt;
&lt;img src="https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&amp;logo=python" alt="Python Version" /&gt;
&lt;img src="https://img.shields.io/badge/PyMuPDF-PDF_Parsing-orange?style=flat-square" alt="PyMuPDF" /&gt;
&lt;img src="https://img.shields.io/badge/AI_Engine-Gemini%20%7C%20DeepSeek%20%7C%20OpenAI-green?style=flat-square" alt="AI Engines" /&gt;
&lt;img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20macOS-lightgrey?style=flat-square" alt="Platform" /&gt;
&lt;/p&gt;

---

## 📌 Descripción general

**Guxing** es una herramienta integral diseñada para procesar, estructurar y traducir documentos complejos (PDF, DOCX, ODT, TXT) manteniendo el contexto técnico, la sintaxis de código y reglas terminológicas específicas.

Genera interfaces interactivas con sincronización de lectura (*hover sync*) y permite la exportación a formatos bilingües listos para estudio o examen.

---

## 🔄 Flujo de Trabajo (Pipeline)

```mermaid
flowchart TD
A["📄 Documento Original\n(PDF / DOCX / ODT / TXT)"] --&gt; B["⚙️ 1. Ingesta y Normalización\n(Extracción a Markdown / JSON con IDs)"]
B --&gt; C["🧠 2. Motor de Traducción Inteligente\n(LLM + Glosario + Reglas + Retención de Código)"]
C --&gt; D["🔗 3. Matriz de Alineación\n(JSON emparejado: {id, es_gl, zh})"]
D --&gt; E["🌐 4. Visor Interactivo HTML\n(Doble pantalla + Hover Sync)"]
D --&gt; F["📑 5. Exportador a PDF\n(PDF Bilingüe / Chino Anotado)"]
```

---

## ✨ Características Principales

- **Ingesta multiformato:** Soporte para PDF (vía `PyMuPDF`), Word (`.docx`), OpenDocument (`.odt`) y texto plano.
- **Motor de IA flexible:** Compatible con múltiples proveedores LLM (**Gemini**, **DeepSeek**, **OpenAI**) con soporte para procesamiento por lotes (*batches*).
- **Traducción contextual técnica:** Retención de bloques de código, respeto estricto de glosarios y reglas para exámenes.
- **Alineación precisa:** Mapeo estructurado por IDs de párrafo/oración entre el texto original y la traducción.
- **Visor interactivo:** Interfaz web bilingüe con efecto *hover sincronizado* entre idiomas.
- **Exportación flexible:** Generación de PDFs bilingües o con anotaciones.

---

## 📁 Estructura del Proyecto

```text
guxing/
├── launcher.py # Autoinstalador y lanzador del sistema
├── app.py # Punto de entrada principal
├── config.py # Gestor seguro de perfiles y rutas del sistema
│
├── core/ # Lógica interna y procesamiento
│ ├── __init__.py
│ ├── parser.py # Extracción de PDF (pymupdf), DOCX, ODT y TXT
│ ├── translator.py # Motor IA (Gemini, DeepSeek, OpenAI) y batches
│ └── viewer_html.py # Generador de la plantilla HTML bilingüe interactiva
│
├── ui/ # Interfaz gráfica de usuario
│ ├── __init__.py
│ ├── theme.py # Paleta y constantes visuales
│ ├── api_dialog.py # Ventana modal gestora de APIs (con soporte de renombrado)
│ └── main_window.py # Ventana principal (pantalla completa, Drop Zone, visor)
│
└── img/ # Recursos visuales y assets
├── guxing-ico.png # Icono de la aplicación
└── guxing-letras.png # Logotipo oficial
```

---

## 🚀 Instalación y Uso Rápido

### 1. Clonar el repositorio
```bash
git clone https://github.com/tu-usuario/guxing.git
cd guxing
```

### 2. Ejecutar mediante el lanzador
El lanzador se encargará de verificar y preparar el entorno:
```bash
python launcher.py
```

*O ejecutar directamente la aplicación:*
```bash
python app.py
```

---

## 🔑 Configuración de APIs

Guxing integra un gestor modal (`api_dialog.py`) donde puedes configurar y renombrar tus credenciales para:
- **Google Gemini API**
- **DeepSeek API**
- **OpenAI API**
