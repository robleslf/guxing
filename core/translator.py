import json
import time
from openai import OpenAI

SYSTEM_PROMPT = """
你是计算机科学专业教授，同时也是中西双语教学专家。
你的任务是将西班牙大学的计算机专业课件/讲义（西班牙语/加利西亚语）整理、对齐并翻译为高水准的中文学术笔记，供中国留学生备考。

【核心翻译与排版准则】：
1. 语言自然性与学术性（专业标准）：
   - 采用中国计算机专业核心教材（如清华大学、电子工业出版社出版标准）的标准中文术语。
   - 语句必须通顺、逻辑清晰易懂，严禁生硬机翻。如果原文句式复杂，可在保持原意的前提下重新组织中文语序。

2. 备考关键术语保留：
   - 仅对【核心概念、考试技术术语、关键缩写、数据库/系统专有名词】在中文后保留原语标注，格式：中文术语 (Término en Español/Galego)。
   - 常用词汇、日常动词、助词切勿过度加括号，以免影响阅读流畅度。
   - 示例：CAP定理 (Teorema CAP)、一致性 (Consistencia)、物理磁盘文件 (ficheiros en disco físico)。

3. 结构与对齐规范：
   - 保持段落连贯，不要将一段完整的话生硬拆成琐碎的孤立单句。
   - 'sentences' 数组中的每一项必须是一句完整的语义句，且 'orig' 与 'trans' 必须严格 1 对 1 对应。
   - 代码块、SQL、命令行及系统路径必须 100% 保持原样输出，不翻译。

【严格的 JSON 输出结构】：
{
  "blocks": [
    {
      "id": "b_1",
      "type": "heading" | "paragraph" | "code",
      "sentences": [
        {
          "sid": "s_1_1",
          "orig": "Texto original en español o galego.",
          "trans": "翻译为自然流畅的中文学术内容，重点概念标注 (Término Original)。"
        }
      ],
      "key_terms": [
        {"original": "Término en examen", "chinese": "中文标准术语"}
      ]
    }
  ]
}
"""

_KEY_EXHAUSTED_MARKERS = (
    "429", "resource_exhausted", "insufficient_quota", "quota",
    "rate limit", "rate_limit", "401", "invalid_api_key",
    "incorrect api key", "authentication", "permission_denied", "403",
)

def _looks_like_key_exhausted(error_str: str) -> bool:
    lowered = error_str.lower()
    return any(marker in lowered for marker in _KEY_EXHAUSTED_MARKERS)

def test_api_key(client, model: str, timeout: float = 15.0) -> tuple:
    try:
        kwargs = dict(
            model=model,
            messages=[{"role": "user", "content": "ping"}],
            max_tokens=1,
        )
        try:
            client.chat.completions.create(timeout=timeout, **kwargs)
        except TypeError:
            client.chat.completions.create(**kwargs)
        return True, "OK"
    except Exception as e:
        err_str = str(e)
        if _looks_like_key_exhausted(err_str):
            return False, f"Sin cuota o credenciales inválidas ({err_str[:100]})"
        return False, f"Error de conexión ({err_str[:100]})"

def check_client_pool(client_pool, status_callback=None) -> dict:
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

def translate_blocks_batch(client_pool, blocks_batch, status_callback=None,
                           max_retries_per_key=2, dead_keys=None):
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
                    temperature=0.2
                )
                result = json.loads(response.choices[0].message.content)
                return result.get("blocks", [])
            except Exception as e:
                err_str = str(e)
                last_error = e

                if _looks_like_key_exhausted(err_str):
                    dead_keys.add(name)
                    if status_callback:
                        status_callback(f"■ Cuenta '{name}' sin cuota o sin acceso. Probando siguiente...")
                    break

                if attempt < max_retries_per_key - 1:
                    wait_time = 4 * (attempt + 1)
                    if status_callback:
                        status_callback(f"Fallo temporal en '{name}': {err_str[:80]}. Reintentando...")
                    time.sleep(wait_time)
                else:
                    dead_keys.add(name)
                    if status_callback:
                        status_callback(f"■ '{name}' no responde. Probando siguiente...")

    raise RuntimeError(f"Se agotaron todas las cuentas/APIs configuradas. Último error: {last_error}")