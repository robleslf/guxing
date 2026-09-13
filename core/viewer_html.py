import json

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>GUXING - Apuntes Bilingües</title>
<style>
  :root {{
    --bg-page: #0d1117;
    --card-left: #161b22;
    --card-right: #131922;
    --border-subtle: #30363d;
    --text-ink: #e6edf3;
    --tommy-blue: #58a6ff;
    --chuckie-orange: #ff7b72;
    --angelica-purple: #bc8cff;
    --reptar-green: #3fb950;
    --sentence-hl: rgba(255, 212, 59, 0.22);
    --sentence-border: #ffd43b;
  }}

  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "PingFang SC", "Microsoft YaHei", sans-serif;
    background: var(--bg-page);
    color: var(--text-ink);
    overflow: hidden;
    height: 100vh;
  }}

  header {{
    height: 58px;
    background: #161b22;
    border-bottom: 2px solid var(--border-subtle);
    padding: 0 24px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}

  .brand {{
    font-weight: 800;
    font-size: 1.25rem;
    color: var(--tommy-blue);
    display: flex;
    align-items: center;
    gap: 10px;
  }}

  .badge {{
    background: #238636;
    color: #ffffff;
    font-size: 0.72rem;
    padding: 3px 8px;
    border-radius: 10px;
    font-weight: 700;
  }}

  .actions {{
    display: flex;
    gap: 10px;
  }}

  .btn {{
    background: #21262d;
    color: var(--text-ink);
    border: 1px solid var(--border-subtle);
    padding: 6px 14px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.88rem;
    font-weight: 600;
    transition: all 0.2s ease;
    display: flex;
    align-items: center;
    gap: 6px;
  }}

  .btn:hover {{
    background: #30363d;
    border-color: #8b949e;
  }}

  .btn-primary {{
    background: #1f6feb;
    border-color: #388bfd;
    color: white;
  }}
  .btn-primary:hover {{ background: #388bfd; }}

  .btn-sync {{
    background: #238636;
    border-color: #2ea043;
    color: white;
  }}
  .btn-sync:hover {{ background: #2ea043; }}

  .split-container {{
    display: flex;
    height: calc(100vh - 58px);
    width: 100%;
  }}

  .column {{
    width: 50%;
    padding: 28px 36px;
    overflow-y: auto;
    scroll-behavior: smooth;
    line-height: 1.85;
  }}

  .col-left {{
    border-right: 1px solid var(--border-subtle);
    background: var(--card-left);
  }}

  .col-right {{
    background: var(--card-right);
    font-size: 1.02rem;
  }}

  .col-header {{
    font-size: 0.78rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #8b949e;
    margin-bottom: 20px;
    font-weight: 800;
    position: sticky;
    top: 0;
    background: inherit;
    padding: 6px 0;
    z-index: 10;
  }}

  .block {{
    margin-bottom: 18px;
    padding: 10px 14px;
    border-radius: 8px;
    transition: background-color 0.15s ease;
  }}

  .block.paragraph {{
    background: rgba(255, 255, 255, 0.02);
    border: 1px solid transparent;
  }}

  .block.heading {{
    font-size: 1.3rem;
    font-weight: 800;
    color: var(--reptar-green);
    margin-top: 24px;
    margin-bottom: 10px;
    border-bottom: 1px solid var(--border-subtle);
    padding-bottom: 6px;
  }}

  .block.code {{
    font-family: ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace;
    background: #0d1117;
    border: 1px solid var(--border-subtle);
    color: #79c0ff;
    padding: 12px;
    border-radius: 6px;
    white-space: pre-wrap;
    font-size: 0.9rem;
  }}

  .sent {{
    transition: background-color 0.15s ease, border-bottom 0.15s ease;
    border-radius: 3px;
    padding: 2px 2px;
    cursor: pointer;
  }}

  .sent:hover {{
    background: rgba(88, 166, 255, 0.15);
  }}

  .sent.active-sentence {{
    background-color: var(--sentence-hl) !important;
    border-bottom: 2px solid var(--sentence-border) !important;
    border-radius: 2px;
  }}

  #glossary-modal {{
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.7);
    z-index: 300;
    justify-content: center;
    align-items: center;
  }}

  .modal-box {{
    background: #161b22;
    width: 680px;
    max-height: 80vh;
    border-radius: 12px;
    padding: 24px;
    border: 1px solid var(--border-subtle);
    display: flex;
    flex-direction: column;
    box-shadow: 0 16px 36px rgba(0, 0, 0, 0.6);
  }}

  .term-row {{
    display: flex;
    justify-content: space-between;
    padding: 10px 0;
    border-bottom: 1px dashed var(--border-subtle);
  }}
</style>
</head>
<body>
<header>
  <div class="brand">
    <span>GUXING</span>
    <span class="badge">Bilingual Reader</span>
  </div>
  <div class="actions">
    <button class="btn btn-sync" onclick="syncCurrentView()">🎯 Sincronizar lectura</button>
    <button class="btn" onclick="toggleGlossary()">📖 Glosario de Examen</button>
    <button class="btn btn-primary" onclick="window.print()">🖨️ Exportar a PDF</button>
  </div>
</header>

<div class="split-container">
  <div class="column col-left" id="col-left" onmouseenter="activeColumn='col-left'">
    <div class="col-header">Original (Español / Galego)</div>
    {left_content}
  </div>
  <div class="column col-right" id="col-right" onmouseenter="activeColumn='col-right'">
    <div class="col-header">Traducción Técnica (中文)</div>
    {right_content}
  </div>
</div>

<div id="glossary-modal">
  <div class="modal-box">
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <h3 style="color:var(--tommy-blue); font-size:1.2rem;">📖 Vocabulario Clave para Examen</h3>
      <button class="btn" onclick="toggleGlossary()">✕</button>
    </div>
    <div style="overflow-y: auto; margin-top: 16px;">
      {glossary_content}
    </div>
  </div>
</div>

<script>
  let activeColumn = 'col-left';
  let lastInteractedSid = null;

  function syncSentenceHover(sid, state) {{
    document.querySelectorAll(`[data-sid="${{sid}}"]`).forEach(el => {{
      el.classList.toggle('active-sentence', state);
    }});
  }}

  function onSentenceClick(element, sid) {{
    lastInteractedSid = sid;
    const isLeft = element.closest('.col-left') !== null;
    const targetCol = isLeft ? document.getElementById('col-right') : document.getElementById('col-left');
    
    const targetElement = targetCol.querySelector(`[data-sid="${{sid}}"]`);
    if (targetElement) {{
      targetElement.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
    }}
  }}

  function syncCurrentView() {{
    const sourceCol = document.getElementById(activeColumn);
    const targetCol = activeColumn === 'col-left' ? document.getElementById('col-right') : document.getElementById('col-left');
    
    if (lastInteractedSid) {{
      const targetElement = targetCol.querySelector(`[data-sid="${{lastInteractedSid}}"]`);
      if (targetElement) {{
        targetElement.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
        return;
      }}
    }}

    const sents = sourceCol.querySelectorAll('.sent');
    const containerTop = sourceCol.getBoundingClientRect().top;
    let closestSid = null;

    for (const el of sents) {{
      const rect = el.getBoundingClientRect();
      if (rect.top >= containerTop && rect.top <= containerTop + 300) {{
        closestSid = el.getAttribute('data-sid');
        break;
      }}
    }}

    if (closestSid) {{
      const targetElement = targetCol.querySelector(`[data-sid="${{closestSid}}"]`);
      if (targetElement) {{
        targetElement.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
      }}
    }}
  }}

  function toggleGlossary() {{
    const m = document.getElementById('glossary-modal');
    m.style.display = m.style.display === 'flex' ? 'none' : 'flex';
  }}
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

            left_sents_html.append(
                f'<span class="sent" data-sid="{sid}" '
                f'onmouseenter="syncSentenceHover(\'{sid}\', true)" '
                f'onmouseleave="syncSentenceHover(\'{sid}\', false)" '
                f'onclick="onSentenceClick(this, \'{sid}\')">{orig_s} </span>'
            )
            right_sents_html.append(
                f'<span class="sent" data-sid="{sid}" '
                f'onmouseenter="syncSentenceHover(\'{sid}\', true)" '
                f'onmouseleave="syncSentenceHover(\'{sid}\', false)" '
                f'onclick="onSentenceClick(this, \'{sid}\')">{trans_s} </span>'
            )

        left_html.append(f'<div class="block {b_type}" data-bid="{bid}">{"".join(left_sents_html)}</div>')
        right_html.append(f'<div class="block {b_type}" data-bid="{bid}">{"".join(right_sents_html)}</div>')

        if "key_terms" in b and isinstance(b["key_terms"], list):
            for t in b["key_terms"]:
                if t.get("original") and t.get("chinese"):
                    all_terms.append(t)

    unique_terms = {t["original"]: t["chinese"] for t in all_terms}
    glossary_html = [
        f'<div class="term-row"><span style="color:#58a6ff; font-weight:700;">{es}</span>'
        f'<span style="color:#3fb950; font-weight:700;">{zh}</span></div>'
        for es, zh in sorted(unique_terms.items())
    ]

    full_html = HTML_TEMPLATE.format(
        left_content="\n".join(left_html),
        right_content="\n".join(right_html),
        glossary_content="\n".join(glossary_html) if glossary_html else "<p>No se detectaron términos específicos.</p>"
    )

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(full_html)