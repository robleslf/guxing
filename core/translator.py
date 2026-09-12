import json
import time
from openai import OpenAI

SYSTEM_PROMPT = """
Eres un profesor de Informática y experto en maquetación interactiva para estudiantes chinos en universidades de España.

Tu tarea es estructurar los apuntes en bloques y DIVIDIR CADA BLOQUE EN FRASES INDIVIDUALES alineadas (1 a 1) entre el original (español/gallego) y el chino.

REGLAS ESTRICTAS:
1. SEPARAR TÍTULOS: Si un título viene pegado al inicio de un bloque (ej: "Historia de los SGBD Como se ha visto..."), crea un bloque separado para el título (type: "heading") y otro para el contenido.
2. ALINEACIÓN FRASE A FRASE:
   - Divide cada párrafo en su lista de frases ('sentences').
   - Cada frase original debe emparejarse exactamente con su frase equivalente traducida.
   - En títulos o código, la lista 'sentences' tendrá un único elemento.
3. RETENCIÓN DE TÉRMINOS PARA EL EXAMEN:
   - Todo concepto técnico, definición o acrónimo en español/gallego debe traducirse al chino colocando inmediatamente al lado el término original entre paréntesis: [Chino] ([Original ES/GL]).
   - Ejemplo: 数据库管理系统 (sistemas de bases de datos)
4. CÓDIGO INTACTO: Código y comandos se mantienen 100% idénticos.

FORMATO JSON DE SALIDA OBLIGATORIO:
{
  "blocks": [
    {
      "id": "b_1",
      "type": "heading" | "paragraph" | "code",
      "sentences": [
        {"sid": "s_1_1", "orig": "Frase 1 original.", "trans": "Frase 1 traducida con términos (Original)."}
      ],
      "key_terms": [{"original": "Término ES/GL", "chinese": "Término Chino"}]
    }
  ]
}
"""

def translate_blocks_batch(client: OpenAI, model: str, blocks_batch: list, status_callback=None, max_retries: int = 4) -> list:
    prompt = f"Analiza, separa frases y traduce estos bloques:\n\n{json.dumps(blocks_batch, ensure_ascii=False)}"
    
    for attempt in range(max_retries):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                response_format={"type": "json_object"},
                temperature=0.1
            )
            result = json.loads(response.choices[0].message.content)
            return result.get("blocks", [])
            
        except Exception as e:
            err_str = str(e)
            if "429" in err_str or "RESOURCE_EXHAUSTED" in err_str:
                wait_time = 15 * (attempt + 1)
                if status_callback:
                    status_callback(f"Límite de velocidad alcanzado. Pausando {wait_time}s para continuar automáticamente...")
                time.sleep(wait_time)
            else:
                raise e

    raise RuntimeError("Se superó el límite de reintentos con el proveedor de IA.")