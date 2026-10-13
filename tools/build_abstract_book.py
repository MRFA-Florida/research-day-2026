#!/usr/bin/env python3
"""Build the MRFA Research Day Abstract Book PDF from data/event.json and data/abstracts.json.

Usage (from the repository root):
    pip install playwright pypdf && playwright install chromium
    python3 tools/build_abstract_book.py

Writes assets/abstract-book.pdf. Run it again whenever an abstract, title, author or
the running order changes, then commit the new PDF.
"""
import glob
import html
import io
import json
import os
import re
import sys
import base64
import mimetypes
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "abstract-book.pdf"
FONTS = ROOT / "tools" / "fonts"
BLUE, NAVY = "#0157b8", "#0a2d5c"

ev = json.loads((ROOT / "data" / "event.json").read_text())
ab = json.loads((ROOT / "data" / "abstracts.json").read_text())
E = ev["event"]
def data_uri(path):
    path = Path(path)
    mt = {".woff2": "font/woff2", ".svg": "image/svg+xml"}.get(path.suffix, mimetypes.guess_type(path.name)[0] or "application/octet-stream")
    return f"data:{mt};base64,{base64.b64encode(path.read_bytes()).decode()}"


esc = lambda s: html.escape(str(s or ""), quote=True)
roman = lambda n: {1: "I", 2: "II"}.get(n, str(n))
clean = lambda n: re.sub(r",.*$", "", re.sub(r"\(.*?\)", "", str(n))).strip()


def fmt(hhmm):
    if not hhmm:
        return ""
    h, m = map(int, hhmm.split(":"))
    return f"{h % 12 or 12}:{m:02d} {'PM' if h >= 12 else 'AM'}"


CRED = re.compile(r"^(MD|PhD|DO|MBBS|MBChB|MPH|MS|MSc|RN|PharmD|DNP|BS|BA|LP|ABPP-CN)\.?$", re.I)


def split_names(s):
    out = []
    for p in re.split(r",\s*", s or ""):
        if not p:
            continue
        if CRED.match(p) and out:
            out[-1] += ", " + p
        else:
            out.append(p)
    return out


def sups(a, k, multi):
    return f"<sup>{esc((a.get('authorAffil') or [''] * 99)[k] if k < len(a.get('authorAffil') or []) else '')}</sup>" if multi and a.get("authorAffil") else ""


def affil_html(a, multi):
    if not a.get("affiliations"):
        return ""
    items = "".join(f"<li>{f'<sup>{k + 1}</sup> ' if multi else ''}{esc(x)}</li>" for k, x in enumerate(a["affiliations"]))
    return f'<ul class="affil">{items}</ul>'


def body_html(a):
    out = []
    for s in a.get("sections", []):
        paras = s.get("p", [])
        for i, p in enumerate(paras):
            head = f'<span class="rh">{esc(s["h"])}.</span> ' if s.get("h") and i == 0 else ""
            out.append(f"<p>{head}{esc(p)}</p>")
    if a.get("keywords"):
        out.append(f'<p class="kw"><span class="rh">Keywords:</span> {esc(a["keywords"])}</p>')
    return "".join(out)


def talk_page(t):
    a = ab.get(t["id"]) or {}
    co = t["coauthors"].split(";") if ";" in (t.get("coauthors") or "") else split_names(t.get("coauthors"))
    co = [c.strip() for c in co]
    names = [f"{t['presenter']}, {t['degrees']}" if t.get("degrees") else t["presenter"]] + [c for c in co if clean(c) != clean(t["presenter"])]
    multi = len(a.get("affiliations") or []) > 1
    authors = ", ".join((f'<span class="pres">{esc(n)}</span>' if k == 0 else esc(n)) + sups(a, k, multi) for k, n in enumerate(names))
    kind = "rapid" if re.search("rapid", t.get("format", ""), re.I) else "full"
    meta = [f"Session {roman(t['session'])}, talk {t['order']}", f"{fmt(t.get('start'))}" + (f", {t['minutes']} min" if t.get("minutes") else "")]
    if a.get("category"):
        meta.append(a["category"])
    who = ", ".join(x for x in [t.get("role"), t.get("department")] if x)
    body = body_html(a) if a.get("sections") else '<p class="missing">Abstract not available at the time of publication.</p>'
    pi = t.get("pi") if t.get("pi") and t["pi"] not in (t.get("department") or "") else None
    return page(t["code"], t.get("format", ""), kind, meta, t["title"], authors, affil_html(a, multi), pi, who, body, t.get("citation") if a.get("sections") else None)


def poster_page(p):
    a = ab.get(p["id"]) or {}
    multi = len(a.get("affiliations") or []) > 1
    pres = p["presenter"]

    def is_pres(n):
        return clean(n) == clean(pres) or (n.split(" ")[-1] == pres.split(" ")[-1] and n[:1] == pres[:1])

    authors = ", ".join((f'<span class="pres">{esc(n)}</span>' if is_pres(n) else esc(n)) + sups(a, k, multi) for k, n in enumerate(a.get("authors") or [pres]))
    meta = [f"Poster session {'II' if p.get('posterSession') == 2 else 'I'}"] + ([p["category"]] if p.get("category") else [])
    who = ", ".join(x for x in [p.get("role"), p.get("department")] if x)
    body = body_html(a) if a.get("sections") else '<p class="missing">Abstract not available at the time of publication.</p>'
    behalf = bool(a.get("authors")) and not any(is_pres(n) for n in a["authors"])
    return page(p.get("code") or p["number"], "Poster", "poster", meta, p["title"], authors, affil_html(a, multi), p.get("pi"), who, body, p.get("citation") if a.get("sections") else None, pres=f"{pres}, {p['degrees']}" if p.get("degrees") else pres, behalf=behalf)


def page(code, fmt_label, kind, meta, title, authors, affil, pi, who, body, cite, pres=None, behalf=False):
    note = (f"Presented by {esc(pres)} on behalf of the authors." if behalf else "Presenting author underlined.") + (f" Principal investigator: {esc(pi)}." if pi else "")
    who_line = f'<p class="who"><strong>Presenter:</strong> {esc(pres)}, {esc(who)}</p>' if pres and who else (f'<p class="who"><strong>Presenter:</strong> {esc(who)}</p>' if who else "")
    return f"""
<section class="abs" id="a-{esc(code)}">
  <p class="meta"><span class="code">{esc(code)}</span><span class="fmt {kind}">{esc(fmt_label)}</span>{''.join(f'<span>{esc(m)}</span>' for m in meta if m)}</p>
  <h2 class="title">{re.sub(r"(\S+-\d\S*)", r'<span style="white-space:nowrap">\1</span>', esc(title))}</h2>
  <p class="authors">{authors}</p>
  {affil}
  <p class="note">{note}</p>
  {who_line}
  <div class="body">{body}</div>
  {f'<p class="cite"><span class="rh">Cite as:</span> {esc(cite)}</p>' if cite else ''}
</section>"""


def font_faces():
    rules = []
    for f in sorted(FONTS.glob("*.woff2")):
        m = re.match(r"(.+)-latin-(\d+)-(normal|italic)", f.stem)
        fam = {"source-serif-4": "Source Serif 4", "familjen-grotesk": "Familjen Grotesk", "atkinson-hyperlegible": "Atkinson Hyperlegible"}[m.group(1)]
        rules.append(f"@font-face{{font-family:'{fam}';src:url('{data_uri(f)}') format('woff2');font-weight:{m.group(2)};font-style:{m.group(3)}}}")
    return "\n".join(rules)


CSS = f"""
{font_faces()}
@page {{ size: Letter; margin: 0.7in 0.8in 0.8in; }}
* {{ box-sizing: border-box; }}
html {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ margin: 0; font: 10pt/1.45 'Source Serif 4', 'DejaVu Serif', serif; color: #17202b; }}
h1, h2, h3, .meta, .sans {{ font-family: 'Familjen Grotesk', 'Inter', 'DejaVu Sans', sans-serif; }}
.marker {{ position: absolute; top: 0; right: 0; font-size: 5pt; color: #fff; }}
.abs {{ break-before: page; position: relative; width: 6.9in; }}
.abs.tight {{ font-size: 9.3pt; line-height: 1.38; }} .abs.tight .body p {{ margin-bottom: 5pt; }} .abs.tight .cite {{ margin-top: 7pt; }}
.abs.tight2 {{ font-size: 8.8pt; line-height: 1.34; }} .abs.tight2 .body p {{ margin-bottom: 4pt; }} .abs.tight2 .cite {{ margin-top: 6pt; }}
.meta {{ display: flex; flex-wrap: wrap; gap: 4pt 10pt; align-items: center; margin: 0 0 10pt; font-size: 8.6pt; color: #4a5868; font-weight: 500; }}
.meta .code {{ font-weight: 700; color: #fff; background: {NAVY}; padding: 2pt 7pt; border-radius: 3pt; letter-spacing: .02em; }}
.meta .fmt {{ font-weight: 700; text-transform: uppercase; letter-spacing: .06em; font-size: 7.6pt; color: {BLUE}; }}
.meta .fmt.rapid {{ color: #8a4b12; }} .meta .fmt.poster {{ color: #2d6a3e; }}
.meta span + span:not(.fmt)::before {{ content: ""; }}
.title {{ font-family: 'Source Serif 4', serif; font-weight: 700; font-size: 15.5pt; line-height: 1.25; margin: 0 0 9pt; color: #0d1b2c; text-wrap: balance; }}
.authors {{ margin: 0 0 4pt; font-size: 9.8pt; }}
.authors sup, .affil sup {{ font-size: 6.5pt; }}
.pres {{ text-decoration: underline; text-underline-offset: 1.5pt; font-weight: 600; }}
.affil {{ list-style: none; margin: 0 0 6pt; padding: 0; font-size: 8.4pt; color: #4a5868; font-style: italic; line-height: 1.4; }}
.note, .who {{ margin: 0 0 2pt; font-size: 8.4pt; color: #4a5868; font-family: 'Atkinson Hyperlegible', sans-serif; }}
.who {{ margin-bottom: 0; }}
.body {{ margin-top: 11pt; padding-top: 10pt; border-top: 1.2pt solid {BLUE}; text-align: justify; hyphens: auto; }}
.body p {{ margin: 0 0 6.5pt; }}
.rh {{ font-family: 'Familjen Grotesk', sans-serif; font-weight: 700; color: {NAVY}; font-size: 9.6pt; }}
.kw {{ font-size: 9.2pt; margin-top: 8pt !important; }}
.missing {{ font-style: italic; color: #4a5868; }}
.cite {{ margin: 10pt 0 0; padding: 7pt 9pt; background: #eef4fb; border-left: 2.5pt solid {BLUE}; font-size: 8.4pt; line-height: 1.45; text-align: left; break-inside: avoid; }}
/* front matter */
.front h1 {{ font-size: 22pt; margin: 0 0 4pt; color: {NAVY}; }}
.front h2 {{ font-family: 'Familjen Grotesk', sans-serif; font-size: 12pt; margin: 18pt 0 6pt; color: {BLUE}; text-transform: uppercase; letter-spacing: .06em; }}
.lede {{ font-size: 11pt; color: #33404f; margin: 0 0 6pt; }}
.glance {{ width: 100%; border-collapse: collapse; font-size: 9.6pt; }}
.glance td {{ padding: 5pt 6pt; border-bottom: .6pt solid #d5dee8; vertical-align: top; }}
.glance td:first-child {{ width: 1.35in; font-family: 'Familjen Grotesk', sans-serif; font-weight: 600; color: {NAVY}; white-space: nowrap; }}
.glance small {{ color: #4a5868; }}
.people {{ display: grid; grid-template-columns: 1fr 1fr; gap: 10pt 18pt; font-size: 9.4pt; }}
.people img {{ width: 0.62in; height: 0.62in; border-radius: 5pt; object-fit: cover; float: left; margin-right: 8pt; }}
.people p {{ margin: 0; }} .people b {{ font-family: 'Familjen Grotesk', sans-serif; font-size: 10.4pt; }}
.people .r {{ color: #4a5868; font-size: 8.6pt; }}
.toc {{ break-before: page; }}
.toc h3 {{ font-size: 10.5pt; margin: 14pt 0 4pt; color: {BLUE}; text-transform: uppercase; letter-spacing: .06em; }}
.toc ol {{ list-style: none; margin: 0; padding: 0; }}
.toc li {{ display: grid; grid-template-columns: .48in 1fr .38in; gap: 6pt; padding: 3.2pt 0; border-bottom: .5pt dotted #c4cfdb; font-size: 8.9pt; line-height: 1.32; break-inside: avoid; }}
.toc .c {{ font-family: 'Familjen Grotesk', sans-serif; font-weight: 700; color: {NAVY}; }}
.toc .p {{ text-align: right; font-family: 'Familjen Grotesk', sans-serif; font-variant-numeric: tabular-nums; }}
.toc .t {{ color: #17202b; }} .toc .n {{ color: #4a5868; }}
.toc a {{ color: inherit; text-decoration: none; }}
.divider {{ break-before: page; height: 8.6in; display: flex; flex-direction: column; justify-content: center; }}
.divider p {{ font-family: 'Familjen Grotesk', sans-serif; text-transform: uppercase; letter-spacing: .12em; color: {BLUE}; font-weight: 700; margin: 0 0 6pt; font-size: 10pt; }}
.divider h2 {{ font-size: 34pt; margin: 0; color: {NAVY}; line-height: 1.05; }}
.divider .s {{ font-family: 'Atkinson Hyperlegible', sans-serif; color: #4a5868; font-size: 11pt; margin-top: 10pt; text-transform: none; letter-spacing: 0; font-weight: 400; }}
"""


def cover_html():
    logo = data_uri(ROOT / "assets/img/mayo-clinic-logo-white.svg")
    bg = data_uri(ROOT / "assets/img/campus-facade.jpg")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{font_faces()}
@page {{ size: Letter; margin: 0; }} html,body {{ margin:0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
.c {{ width: 8.5in; height: 11in; position: relative; color: #fff; background: {NAVY} url('{bg}') 62% center / cover; font-family: 'Familjen Grotesk', sans-serif; overflow: hidden; }}
.s {{ position: absolute; inset: 0; background: linear-gradient(180deg, rgba(10,45,92,.55) 0%, rgba(10,45,92,.1) 30%), linear-gradient(0deg, rgba(7,26,54,.97) 18%, rgba(1,87,184,.6) 62%, rgba(1,87,184,.1) 100%); }}
.i {{ position: absolute; left: .9in; right: .9in; bottom: 1in; }}
img {{ position: absolute; top: .8in; left: .9in; width: 1in; }}
.k {{ font-size: 13pt; color: #dbe8f7; margin: 0 0 10pt; }}
h1 {{ font-size: 50pt; line-height: 1; margin: 0; letter-spacing: -.02em; }}
h1 span {{ display:block; color: #f3b48a; font-weight: 500; }}
.ab {{ font-size: 26pt; font-weight: 600; margin: 26pt 0 0; padding-top: 16pt; border-top: 2pt solid rgba(255,255,255,.55); }}
.f {{ font-family: 'Atkinson Hyperlegible', sans-serif; font-size: 12.5pt; margin: 12pt 0 0; line-height: 1.5; color: #e3edf9; }}
</style></head><body><div class="c"><div class="s"></div><img src="{logo}" alt="">
<div class="i"><p class="k">{esc(E.get('host') or 'Mayo Clinic Research Fellow’s Association (MRFA)')}</p>
<h1>MRFA Research Day <span>Florida 2026</span></h1>
<p class="ab">Abstract Book</p>
<p class="f">{esc(E.get('dateLabel'))}<br>{esc(E.get('location') or 'Kinne Auditorium')}, Mayo Clinic in Florida, Jacksonville</p></div></div></body></html>"""


def body_document(pages_for=None):
    talks = sorted(ev["talks"], key=lambda t: t["code"])
    posters = sorted(ev["posters"], key=lambda p: p.get("code") or p["number"])
    pg = lambda code: str(pages_for.get(code, "")) if pages_for else "000"

    rows = []
    for a in ev["agenda"]:
        extra = ""
        if a["type"] == "session":
            n = 1 if a["start"] < "12:00" else 2
            extra = f"<br><small>Abstracts {talks_in(talks, n)}. Moderator: {esc(a.get('moderator'))}</small>"
        elif a["type"] == "posters":
            n = 1 if a["start"] < "12:00" else 2
            ps = [p for p in posters if p.get("posterSession", 1) == n]
            extra = f"<br><small>Posters {esc(ps[0]['code'])} to {esc(ps[-1]['code'])}</small>" if ps else ""
        elif a.get("who"):
            extra = f"<br><small>{esc(a['who'])}</small>"
        rows.append(f"<tr><td>{fmt(a['start'])} to {fmt(a['end'])}</td><td>{esc(a['title'])}{extra}</td></tr>")

    people = []
    for p in ev.get("committee", []):
        img = data_uri(ROOT / p["photo"]) if p.get("photo") and (ROOT / p["photo"]).exists() else ""
        people.append(f'<div>{f"<img src={chr(34)}{img}{chr(34)} alt={chr(34)}{chr(34)}>" if img else ""}<p><b>{esc(p["name"])}, {esc(p.get("degrees"))}</b></p><p class="r">{esc(p.get("title"))}</p></div>')

    tcode = {t["id"]: t["code"] for t in talks}

    def toc_list(items, codekey):
        out = []
        for x in items:
            code = x.get(codekey) or x["number"]
            note, page_of = "", code
            if x.get("talk"):
                note, page_of = f" · see oral abstract {tcode.get(x['talk'], '')}", tcode.get(x["talk"], "")
            elif "talk" not in x and "session" not in x and not ab.get(x["id"], {}).get("sections"):
                note, page_of = " · abstract not available", None
            name = esc(x["presenter"]) + (", " + esc(x["degrees"]) if x.get("degrees") else "")
            out.append(f'<li><span class="c">{esc(code)}</span><span><span class="t">{esc(x["title"])}</span><br><span class="n">{name}{note}</span></span><span class="p">{pg(page_of) if page_of else ""}</span></li>')
        return "<ol>" + "".join(out) + "</ol>"

    own = [p for p in posters if not p.get("talk") and ab.get(p["id"], {}).get("sections")]
    ps1 = [p for p in posters if p.get("posterSession", 1) == 1]
    ps2 = [p for p in posters if p.get("posterSession") == 2]
    s1 = [t for t in talks if t["session"] == 1]
    s2 = [t for t in talks if t["session"] == 2]
    front = f"""
<section class="front">
  <h1>Welcome</h1>
  <p class="lede">{esc(E.get('fullName') or 'MRFA Research Day, Florida 2026')}. {esc(E.get('dateLabel'))}, {esc(E.get('location') or 'Kinne Auditorium')}, Mayo Clinic in Florida.</p>
  <p class="lede">This book collects the {len(talks)} oral and rapid-fire presentations and {len(posters)} posters presented at Research Day, in program order. Posters that accompany an oral presentation point to that abstract. Abstracts appear as submitted by the authors. The live program, speaker details and Q&amp;A are at <span class="sans">mrfa-florida.github.io/research-day-2026</span>.{(' Contact: <span class="sans">' + esc(E['contactEmail']) + '</span>.') if E.get('contactEmail') else ''}</p>
  <h2>Program at a glance</h2>
  <table class="glance">{''.join(rows)}</table>
  <h2>Organizing committee</h2>
  <div class="people">{''.join(people)}</div>
</section>
<section class="toc">
  <h1 style="font-family:'Familjen Grotesk',sans-serif;font-size:22pt;margin:0;color:{NAVY}">Contents</h1>
  <h3>Oral presentations, Session I</h3>{toc_list(s1, 'code')}
  <h3>Oral presentations, Session II</h3>{toc_list(s2, 'code')}
  <h3>Poster session I</h3>{toc_list(ps1, 'code')}
  <h3>Poster session II</h3>{toc_list(ps2, 'code')}
</section>"""

    def divider(kicker, title, sub):
        return f'<section class="divider"><p>{esc(kicker)}</p><h2>{esc(title)}</h2><p class="s">{sub}</p></section>'

    s_time = {a["start"] < "12:00" and 1 or 2: a for a in ev["agenda"] if a["type"] == "session"}
    parts = [front]
    parts.append(divider("Oral presentations", "Session I", f"{fmt(s_time[1]['start'])} to {fmt(s_time[1]['end'])}, Kinne Auditorium. Moderator: {esc(s_time[1].get('moderator'))}"))
    parts += [talk_page(t) for t in s1]
    parts.append(divider("Oral presentations", "Session II", f"{fmt(s_time[2]['start'])} to {fmt(s_time[2]['end'])}, Kinne Auditorium. Moderator: {esc(s_time[2].get('moderator'))}"))
    parts += [talk_page(t) for t in s2]
    pss = [a for a in ev["agenda"] if a["type"] == "posters"]
    for n, a in enumerate(pss, 1):
        mine = [p for p in own if p.get("posterSession", 1) == n]
        if mine:
            parts.append(divider("Posters", f"Poster session {'I' * n}", f"{fmt(a['start'])} to {fmt(a['end'])}. Abstracts for posters that accompany an oral presentation appear with the oral sessions."))
            parts += [poster_page(p) for p in mine]
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><style>{CSS}</style></head><body>{"".join(parts)}</body></html>'


def talks_in(talks, n):
    xs = [t["code"] for t in talks if t["session"] == n]
    return f"{xs[0]} to {xs[-1]}" if xs else ""


FOOTER = f"""<div style="width:100%;font:7.5pt 'Helvetica',sans-serif;color:#6b7785;padding:0 0.8in;display:flex;justify-content:space-between">
<span>MRFA Research Day, Florida 2026 &middot; Abstract Book</span><span><span class="pageNumber"></span></span></div>"""


def render(browser, doc, footer=True):
    pg = browser.new_page()
    pg.set_content(doc, wait_until="load")
    pg.evaluate("document.fonts.ready")
    pg.wait_for_timeout(300)
    # Shrink abstracts that just miss fitting on one page (9.6in of usable height).
    pg.evaluate("""() => { const max = 9.45 * 96;
      document.querySelectorAll('.abs').forEach((el) => {
        if (el.offsetHeight <= max) return;
        el.classList.add('tight'); if (el.offsetHeight <= max) return;
        el.classList.replace('tight', 'tight2'); if (el.offsetHeight > max) el.classList.remove('tight2');
      }); }""")
    pdf = pg.pdf(format="Letter", print_background=True, prefer_css_page_size=True,
                 display_header_footer=footer, header_template="<span></span>", footer_template=FOOTER if footer else "<span></span>")
    pg.close()
    return pdf


def main():
    exe = None
    cands = glob.glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell")
    if cands:
        exe = cands[0]
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        cover = render(b, cover_html(), footer=False)
        first = render(b, body_document())
        # find the page each abstract starts on (cover is page 1, body numbering continues from 2)
        pages = {}
        for i, page in enumerate(PdfReader(io.BytesIO(first)).pages):
            m = re.match(r"\s*([OP]-\d+)\s*(FULL ORAL|RAPID-FIRE|POSTER)", page.extract_text() or "", re.I)
            if m:
                pages.setdefault(m.group(1), i + 1)
        body = render(b, body_document(pages))
        b.close()
    w = PdfWriter()
    for src in (cover, body):
        for pg in PdfReader(io.BytesIO(src)).pages:
            w.add_page(pg)
    w.add_metadata({"/Title": "MRFA Research Day, Florida 2026: Abstract Book", "/Author": "Mayo Clinic Research Fellow’s Association (MRFA), Florida"})
    with open(OUT, "wb") as f:
        w.write(f)
    print(f"Wrote {OUT.relative_to(ROOT)}: {len(w.pages)} pages, {len(pages)} abstracts located")


if __name__ == "__main__":
    main()
