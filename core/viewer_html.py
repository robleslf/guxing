HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>🪐 GUXING - Apuntes Bilingües</title>
<style>
  :root {{
    --bg-page: #0f111c;
    --card-left: #171a2a;
    --card-right: #1a1e30;
    --border-comic: #2e3458;
    --text-ink: #f8fafc;
    --tommy-blue: #00b4d8;
    --chuckie-orange: #ff5400;
    --angelica-purple: #9d4edd;
    --reptar-green: #06d6a0;
    --block-hl: rgba(0, 180, 216, 0.16);
    --sentence-hl: rgba(255, 209, 102, 0.28);
    --sentence-text-hl: #ffe699;
    --sentence-border: #ff5400;
  }}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif; background: var(--bg-page); color: var(--text-ink); }}
  header {{ position: sticky; top: 0; z-index: 100; background: #141726; border-bottom: 3px solid var(--tommy-blue); padding: 14px 32px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 4px 18px rgba(0, 0, 0, 0.4); }}
  .brand {{ font-weight: 900; font-size: 1.4rem; color: var(--tommy-blue); display: flex; align-items: center; gap: 10px; letter-spacing: 1px; }}
  .badge-retro {{ background: var(--chuckie-orange); color: white; font-size: 0.75rem; padding: 3px 10px; border-radius: 12px; font-weight: 800; text-transform: uppercase; }}
  .btn {{ background: var(--tommy-blue); color: white; border: none; padding: 10px 20px; border-radius: 25px; cursor: pointer; font-size: 0.92rem; font-weight: 700; box-shadow: 0 4px 0 #0077b6; transition: all 0.15s ease; }}
  .btn:hover {{ background: #0096c7; transform: translateY(-1px); }}
  .btn-purple {{ background: var(--angelica-purple); box-shadow: 0 4px 0 #7b2cbf; }}
  .btn-purple:hover {{ background: #7b2cbf; }}
  .split-container {{ display: flex; width: 100%; min-height: calc(100vh - 68px); }}
  .column {{ width: 50%; padding: 32px 40px; overflow-y: auto; line-height: 1.95; }}
  .col-left {{ border-right: 3px dashed var(--border-comic); background: var(--card-left); }}
  .col-right {{ background: var(--card-right); font-size: 1.05rem; }}
  .col-header {{ font-size: 0.82rem; text-transform: uppercase; letter-spacing: 1.8px; color: #94a3b8; margin-bottom: 24px; font-weight: 800; }}
  .block {{ padding: 16px 20px; margin-bottom: 16px; border-radius: 12px; border-left: 5px solid transparent; transition: all 0.15s ease; }}
  .block.heading {{ font-size: 1.4rem; font-weight: 900; color: var(--reptar-green); margin-top: 28px; margin-bottom: 12px; border-bottom: 2px solid var(--border-comic); padding-bottom: 8px; border-left: none; }}
  .block.paragraph {{ background: #1e2238; border: 1px solid var(--border-comic); box-shadow: 0 4px 10px rgba(0,0,0,0.2); }}
  .block.code {{ font-family: monospace; background: #0b0c14; border: 2px solid var(--border-comic); color: #48cae4; white-space: pre-wrap; font-size: 0.95rem; border-radius: 10px; }}
  .block.active-block {{ background: var(--block-hl) !important; border-left: 5px solid var(--tommy-blue) !important; }}
  .sent {{ transition: all 0.12s ease; border-radius: 4px; padding: 2px 4px; cursor: pointer; }}
  .sent.active-sentence {{ background-color: var(--sentence-hl) !important; color: var(--sentence-text-hl) !important; box-shadow: 0 0 10px rgba(255, 84, 0, 0.5); border-bottom: 2px solid var(--sentence-border); font-weight: 600; }}
  #glossary-modal {{ display: none; position: fixed; inset: 0; background: rgba(10, 11, 18, 0.75); z-index: 200; justify-content: center; align-items: center; backdrop-filter: blur(4px); }}
  .modal-box {{ background: #1b1e33; width: 720px; max-height: 82vh; border-radius: 20px; padding: 30px; display: flex; flex-direction: column; border: 3px solid var(--angelica-purple); box-shadow: 0 16px 40px rgba(0,0,0,0.6); }}
  .term-row {{ display: flex; justify-content: space-between; padding: 12px 0; border-bottom: 1px dashed var(--border-comic); }}
  @media print {{ header, #glossary-modal {{ display: none !important; }} .split-container {{ display: block; }} .column {{ width: 100%; border: none; }} .col-left {{ display: none; }} }}
</style>
</head>
<body>
<header>
  <div class="brand"><span>🪐 GUXING</span><span class="badge-retro">Bilingual Reader</span></div>
  <div style="display: flex; gap: 14px;">
    <button class="btn btn-purple" onclick="toggleGlossary()">📚 Glosario de Examen</button>
    <button class="btn" onclick="window.print()">🖨️ Exportar a PDF</button>
  </div>
</header>
<div class="split-container">
  <div class="column col-left"><div class="col-header">Original (Español / Galego)</div>{left_content}</div>
  <div class="column col-right"><div class="col-header">Traducción con Anotaciones (中文)</div>{right_content}</div>
</div>
<div id="glossary-modal">
  <div class="modal-box">
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <h3 style="color:var(--tommy-blue); font-size:1.35rem; font-weight:800;">📚 Vocabulario Clave para Examen</h3>
      <button class="btn" onclick="toggleGlossary()">✕ Cerrar</button>
    </div>
    <div style="overflow-y: auto; margin-top: 20px;">{glossary_content}</div>
  </div>
</div>
<script>
  function syncBlock(bid, state) {{ document.querySelectorAll(`[data-bid="${{bid}}"]`).forEach(el => el.classList.toggle('active-block', state)); }}
  function syncSentence(sid, state) {{ document.querySelectorAll(`[data-sid="${{sid}}"]`).forEach(el => el.classList.toggle('active-sentence', state)); }}
  function scrollToMatching(sid) {{ document.querySelectorAll(`[data-sid="${{sid}}"]`).forEach(el => el.scrollIntoView({{ behavior: 'smooth', block: 'center' }})); }}
  function toggleGlossary() {{ const m = document.getElementById('glossary-modal'); m.style.display = m.style.display === 'flex' ? 'none' : 'flex'; }}
</script>
</body>
</html>
"""

def generate_html_viewer(translated_blocks: list, output_html_path: str):
    left_html, right_html, all_terms = [], [], []

    for b_idx, b in enumerate(translated_blocks):
        bid = b.get("id", f"b_{b_idx}")
        b_type = b.get("type", "paragraph")
        sentences = b.get("sentences", [])

        if not sentences:
            orig = b.get("original", "")
            trans = b.get("translated", "")
            sentences = [{"sid": f"{bid}_1", "orig": orig, "trans": trans}]

        left_sents_html, right_sents_html = [], []

        for s_idx, s in enumerate(sentences):
            sid = s.get("sid", f"{bid}_{s_idx}")
            orig_s = s.get("orig", "")
            trans_s = s.get("trans", "")

            left_sents_html.append(f'<span class="sent" data-sid="{sid}" onmouseenter="syncSentence(\'{sid}\', true)" onmouseleave="syncSentence(\'{sid}\', false)" onclick="scrollToMatching(\'{sid}\')">{orig_s} </span>')
            right_sents_html.append(f'<span class="sent" data-sid="{sid}" onmouseenter="syncSentence(\'{sid}\', true)" onmouseleave="syncSentence(\'{sid}\', false)" onclick="scrollToMatching(\'{sid}\')">{trans_s} </span>')

        left_html.append(f'<div class="block {b_type}" data-bid="{bid}" onmouseenter="syncBlock(\'{bid}\', true)" onmouseleave="syncBlock(\'{bid}\', false)">{"".join(left_sents_html)}</div>')
        right_html.append(f'<div class="block {b_type}" data-bid="{bid}" onmouseenter="syncBlock(\'{bid}\', true)" onmouseleave="syncBlock(\'{bid}\', false)">{"".join(right_sents_html)}</div>')

        if "key_terms" in b and isinstance(b["key_terms"], list):
            for t in b["key_terms"]:
                if t.get("original") and t.get("chinese"):
                    all_terms.append(t)

    unique_terms = {t["original"]: t["chinese"] for t in all_terms}
    glossary_html = [f'<div class="term-row"><span style="color:#00b4d8; font-weight:800;">{es}</span><span style="color:#06d6a0; font-weight:800;">{zh}</span></div>' for es, zh in sorted(unique_terms.items())]

    full_html = HTML_TEMPLATE.format(
        left_content="\n".join(left_html),
        right_content="\n".join(right_html),
        glossary_content="\n".join(glossary_html) if glossary_html else "<p>No se detectaron términos específicos.</p>"
    )
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(full_html)