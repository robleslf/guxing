import json
import time
from openai import OpenAI

SYSTEM_PROMPT = """
Eres un profesor de Informática y experto en maquetación interactiva para estudiantes chinos en universidades de España.
Tu tarea es estructurar los apuntes en bloques y DIVIDIR CADA BLOQUE EN FRASES INDIVIDUALES alineadas (1 a 1) entre el original y la traducción.

REGLAS ESTRICTAS:
1. SEPARAR TÍTULOS: Si un título viene pegado al inicio de un bloque (ej: "Historia de los SGBD Como se ha visto..."), crea un bloque de tipo "heading" solo para el título y otro de tipo "paragraph" para el resto.
2. ALINEACIÓN FRASE A FRASE:
   - Divide cada párrafo en su lista de frases ('sentences').
   - Cada frase original debe emparejarse exactamente con su frase equivalente traducida.
   - En títulos o código, la lista 'sentences' tendrá un único elemento.
3. RETENCIÓN DE TÉRMINOS PARA EL EXAMEN:
   - Todo concepto técnico, definición o acrónimo en español/gallego debe traducirse al chino colocando inmediatamente al lado el término original entre paréntesis.
   - Ejemplo: 数据库系统 (sistemas de bases de datos)
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

# Fragmentos de mensajes de error que indican que una clave está agotada,
# es inválida o no tiene permiso -- no merece la pena reintentar con ella,
# lo suyo es pasar directamente a la siguiente cuenta configurada.
_KEY_EXHAUSTED_MARKERS = (
    "429",
    "resource_exhausted",
    "insufficient_quota",
    "quota",
    "rate limit",
    "rate_limit",
    "401",
    "invalid_api_key",
    "incorrect api key",
    "authentication",
    "permission_denied",
    "403",
)


def _looks_like_key_exhausted(error_str: str) -> bool:
    lowered = error_str.lower()
    return any(marker in lowered for marker in _KEY_EXHAUSTED_MARKERS)


def test_api_key(client, model, timeout=None):
    """
    Comprobación mínima y barata de que una cuenta/API key funciona de
    verdad para traducir: manda un mensaje muy corto y pide como máximo
    1 token de respuesta, usando el mismo endpoint (chat.completions) que
    se usará durante la traducción real, para que el resultado sea fiable.

    Si la cuenta está agotada o es inválida, el proveedor la rechaza antes
    de generar nada, así que el coste real en tokens es prácticamente cero
    en el peor caso, y mínimo (unos pocos tokens) si la cuenta sí funciona.

    Devuelve (ok: bool, mensaje: str).
    """
    try:
        client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "hola"}],
            max_tokens=1,
        )
        return True, "OK"
    except Exception as e:
        return False, str(e)


def translate_blocks_batch(client_pool, blocks_batch, status_callback=None,
                            max_retries_per_key=2, dead_keys=None):
    """
    Traduce un lote de bloques probando, en orden, cada perfil/cuenta del
    pool. Si una cuenta falla (cuota agotada, clave inválida, error de red
    persistente...) se descarta para el resto del proceso y se continúa
    automáticamente con la siguiente, hasta que una funcione o se agoten
    todas.

    client_pool: lista de dicts {"name": str, "client": OpenAI, "model": str}
                 (normalmente una entrada por cada perfil con API key
                 configurado en Guxing, empezando por el perfil activo).
    dead_keys:   set() compartido entre lotes para no volver a probar una
                 cuenta que ya se sabe agotada/rota en este mismo proceso.
    """
    if dead_keys is None:
        dead_keys = set()

    prompt = f"Analiza, separa frases y traduce estos bloques:\n\n{json.dumps(blocks_batch, ensure_ascii=False)}"

    last_error = None

    for profile in client_pool:
        name = profile["name"]
        if name in dead_keys:
            continue

        client = profile["client"]
        model = profile["model"]

        for attempt in range(max_retries_per_key):
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
                last_error = e

                if _looks_like_key_exhausted(err_str):
                    # No merece la pena reintentar con esta cuenta: se marca
                    # como agotada y se pasa a la siguiente inmediatamente.
                    dead_keys.add(name)
                    if status_callback:
                        status_callback(f"⚠ Cuenta '{name}' sin cuota o sin acceso. Probando con la siguiente cuenta...")
                    break

                # Error probablemente transitorio (red, servidor caído, etc.):
                # un par de reintentos cortos antes de dar por perdida esta cuenta.
                if attempt < max_retries_per_key - 1:
                    wait_time = 5 * (attempt + 1)
                    if status_callback:
                        status_callback(f"Fallo temporal en '{name}': {err_str[:100]}. Reintentando en {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    dead_keys.add(name)
                    if status_callback:
                        status_callback(f"⚠ '{name}' no responde tras varios intentos. Probando con la siguiente cuenta...")

    # Si llegamos aquí, ninguna cuenta del pool ha podido traducir este lote
    raise RuntimeError(
        "Se agotaron todas las cuentas/API keys configuradas sin poder traducir este bloque. "
        f"Último error: {last_error}"
    )


def test_api_key(client, model: str, timeout: float = 15.0) -> tuple:
    """
    Comprueba si una cuenta/API key concreta funciona, con el mínimo gasto
    posible: una única petición de chat con un mensaje casi vacío y
    max_tokens=1. Usa el mismo camino (chat.completions) que la traducción
    real, así que si esto funciona, la traducción también podrá arrancar
    con esta cuenta.

    Devuelve (ok: bool, mensaje: str).
    """
    try:
        kwargs = dict(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
        try:
            client.chat.completions.create(timeout=timeout, **kwargs)
        except TypeError:
            # Alguna versión del cliente no acepta 'timeout' en este método
            client.chat.completions.create(**kwargs)
        return True, "OK"
    except Exception as e:
        err_str = str(e)
        if _looks_like_key_exhausted(err_str):
            return False, f"Sin cuota o credenciales inválidas ({err_str[:100]})"
        return False, f"Error de conexión ({err_str[:100]})"


def check_client_pool(client_pool, status_callback=None) -> dict:
    """
    Comprueba, una por una, todas las cuentas de client_pool. Llama a
    status_callback (si se proporciona) con mensajes de progreso legibles,
    útiles para mostrar en la interfaz mientras se ejecuta.

    Devuelve un dict {nombre_cuenta: (ok: bool, mensaje: str)}.
    """
    results = {}
    for profile in client_pool:
        name = profile["name"]
        if status_callback:
            status_callback(f"Comprobando cuenta '{name}'...")
        ok, msg = test_api_key(profile["client"], profile["model"])
        results[name] = (ok, msg)
        if status_callback:
            icon = "✔" if ok else "✘"
            status_callback(f"{icon} '{name}': {msg}")
    return results