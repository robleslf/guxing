import os
import re

try:
    import pymupdf
    HAS_PYMUPDF = True
except ImportError:
    HAS_PYMUPDF = False
    from pypdf import PdfReader

import docx
from odf import opendocument
from odf import text as odf_text
from odf import teletype


def _merge_broken_paragraphs(raw_list: list) -> list:
    """Fusiona fragmentos partidos de un mismo párrafo antes de enviarlos a traducir."""
    merged = []
    for text in raw_list:
        text = text.strip()
        if not text:
            continue
        
        # Si el bloque anterior no terminó en cierre de puntuación (. : ? !), se une con el actual
        if merged and not re.search(r'[.:!?\n]\s*$', merged[-1]) and not text.startswith(('•', '-', '*', '1.', '2.', '3.', '4.', '5.')):
            merged[-1] = f"{merged[-1]} {text}"
        else:
            merged.append(text)
    return merged


def extract_text_from_file(file_path: str) -> list:
    ext = os.path.splitext(file_path)[1].lower()
    raw_blocks = []

    if ext == ".pdf":
        if HAS_PYMUPDF:
            doc = pymupdf.open(file_path)
            for page in doc:
                blocks = page.get_text("blocks")
                for b in blocks:
                    text = b[4].strip()
                    if text and not text.isdigit() and len(text) > 3:
                        cleaned = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
                        raw_blocks.append(cleaned.strip())
        else:
            reader = PdfReader(file_path)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    for line in text.split("\n\n"):
                        cleaned = line.strip()
                        if cleaned:
                            raw_blocks.append(cleaned)

    elif ext == ".docx":
        doc = docx.Document(file_path)
        for p in doc.paragraphs:
            cleaned = p.text.strip()
            if cleaned:
                raw_blocks.append(cleaned)

    elif ext == ".odt":
        doc = opendocument.load(file_path)
        for p in doc.getElementsByType(odf_text.P):
            cleaned = teletype.extractText(p).strip()
            if cleaned:
                raw_blocks.append(cleaned)

    elif ext in [".txt", ".md"]:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for block in f.read().split("\n\n"):
                cleaned = block.strip()
                if cleaned:
                    raw_blocks.append(cleaned)
    else:
        raise ValueError(f"Formato no soportado: {ext}")

    normalized_blocks = _merge_broken_paragraphs(raw_blocks)

    processed_blocks = []
    for idx, text in enumerate(normalized_blocks, start=1):
        processed_blocks.append({"id": f"b_{idx}", "text": text})
    return processed_blocks