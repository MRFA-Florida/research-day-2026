#!/usr/bin/env python3
"""Build printable judge evaluation sheets from data/event.json.

    python3 tools/build_judging_sheets.py [output_dir]

Writes two PDFs (default: ./judging-sheets/):
  judging-oral.pdf     one landscape page per oral session, with presenter photos
  judging-posters.pdf  one portrait page per poster session
Re-run after any change to presenters, titles or poster lists.
"""
import glob
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_abstract_book import ROOT, BLUE, NAVY, esc, fmt, data_uri, font_faces  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from pypdf import PdfReader  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "judging-sheets"
ev = json.loads((ROOT / "data" / "event.json").read_text())
talks = {t["id"]: t for t in ev["talks"]}
LOGO = data_uri(ROOT / "assets/img/mayo-clinic-logo-white.svg")
SUNSET = "#f6b48a"
ROMAN = {1: "I", 2: "II"}

ORAL = [("Scientific merit", "Originality, importance of the question"),
        ("Methods and rigor", "Design, analysis, validity of conclusions"),
        ("Clarity of presentation", "Organization, slides, timing"),
        ("Impact and discussion", "Significance; answers to questions")]
POSTER = [("Scientific merit", "Originality, importance of the question"),
          ("Methods and rigor", "Design, analysis, validity of conclusions"),
          ("Poster design", "Layout, figures, readability"),
          ("Presenter", "Explanation and answers to questions")]


def short(n):
    return re.sub(r",.*$", "", re.sub(r"\(.*?\)\s*", "", n)).strip()


def initials(n):
    w = [x for x in short(n).split() if not re.fullmatch(r"[A-Z]\.", x)]
    return ((w[0][0] if w else "") + (w[-1][0] if len(w) > 1 else "")).upper()


def avatar(person):
    ph = person.get("photo")
    if ph and (ROOT / ph).exists():
        return f'<span class="av"><img src="{data_uri(ROOT / ph)}" alt=""></span>'
    return f'<span class="av ini">{esc(initials(person["presenter"]))}</span>'


CSS = """
* { box-sizing: border-box; }
html, body { margin: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { font: 8.4pt/1.28 'Inter', 'Atkinson Hyperlegible', sans-serif; color: #17202b; }
.page { page-break-after: always; display: flex; flex-direction: column; overflow: hidden; }
.page:last-child { page-break-after: auto; }
h1, h2, th, .k, .code { font-family: 'Familjen Grotesk', 'Inter', sans-serif; }
header { background: NAVY; color: #fff; padding: 12pt 18pt; display: grid; grid-template-columns: auto 1fr auto; gap: 14pt; align-items: center; border-radius: 0 0 8pt 8pt; }
header img { width: 44pt; }
header .k { margin: 0 0 2pt; font-size: 8pt; color: #cfe0f5; font-weight: 600; letter-spacing: .04em; text-transform: uppercase; }
header h1 { margin: 0; font-size: 17pt; line-height: 1.1; }
header h1 span { color: SUNSET; font-weight: 500; }
header .s { margin: 3pt 0 0; font-size: 9pt; color: #e3edf9; }
.judge { display: grid; grid-template-columns: auto 2.3in; gap: 6pt 6pt; align-items: end; font-size: 8.5pt; color: #e3edf9; }
.judge .ln { border-bottom: 1px solid rgba(255,255,255,.75); height: 14pt; }
.rubric { display: grid; gap: 6pt; margin: 9pt 0 7pt; }
.rubric div { background: #eef4fb; border-left: 3pt solid BLUE; border-radius: 4pt; padding: 4pt 7pt; font-size: 7.6pt; color: #33404f; }
.rubric b { display: block; color: NAVY; font: 700 8.6pt 'Familjen Grotesk', sans-serif; }
.rubric b i { font-style: normal; color: BLUE; margin-right: 3pt; }
.note { display: flex; justify-content: space-between; gap: 12pt; font-size: 7.6pt; color: #4a5868; margin: 0 0 5pt; }
.note b { color: NAVY; }
table { width: 100%; border-collapse: separate; border-spacing: 0; table-layout: fixed; }
th { font-size: 7.4pt; font-weight: 700; color: #fff; background: BLUE; padding: 4pt 4pt; text-align: center; line-height: 1.15; }
th:first-child { border-radius: 5pt 0 0 0; } th:last-child { border-radius: 0 5pt 0 0; }
th.l { text-align: left; }
td { border-bottom: .6pt solid #cfd9e5; padding: 0 4pt; vertical-align: middle; }
tr.full td.who { box-shadow: inset 3pt 0 0 BLUE; }
tr:nth-child(even) td { background: #f7f9fc; }
td.num { text-align: center; font: 700 8.6pt 'Familjen Grotesk', sans-serif; color: BLUE; white-space: nowrap; }
td.num small { display: block; font: 500 6.8pt 'Inter', sans-serif; color: #6b7785; }
td.ph { text-align: center; padding: 2pt; }
.av { display: inline-grid; place-items: center; border-radius: 50%; overflow: hidden; background: #e6effa; color: BLUE; font: 700 7pt 'Familjen Grotesk', sans-serif; vertical-align: middle; }
.av img { width: 100%; height: 100%; object-fit: cover; display: block; }
td.who { overflow: hidden; }
.nm { font-weight: 700; font-size: 8.4pt; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.nm .tag { font: 700 6.2pt 'Familjen Grotesk', sans-serif; text-transform: uppercase; letter-spacing: .05em; color: #8a4b12; margin-left: 4pt; }
tr.full .nm .tag { color: BLUE; }
.ttl { color: #4a5868; font-size: 7.4pt; line-height: 1.2; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; }
td.box { padding: 3pt; }
td.box div { border: 1pt solid #9fb0c8; border-radius: 3pt; height: var(--bh); background: #fff; }
td.box.tot div { border: 1.4pt solid NAVY; background: #fff; }
td.coi { text-align: center; }
td.coi span { display: inline-block; width: 9pt; height: 9pt; border: 1pt solid #9fb0c8; border-radius: 2pt; background: #fff; }
td.cm div { border-bottom: .6pt dotted #9fb0c8; height: calc(var(--bh) * .6); }
footer { margin-top: auto; padding-top: 6pt; display: flex; justify-content: space-between; font-size: 7.2pt; color: #6b7785; border-top: 1.5pt solid BLUE; }
footer b { color: NAVY; }
""".replace("NAVY", NAVY).replace("BLUE", BLUE).replace("SUNSET", SUNSET)


def sheet(kind, title_line, sub, rows, crit, row_h, av_px, page_h, extra_note, box_h):
    rub = "".join(f'<div><b><i>{i}</i>{esc(n)}</b>{esc(d)}</div>' for i, (n, d) in enumerate(crit, 1))
    heads = "".join(f'<th>{i}<br><span style="font-weight:500">{esc(n.split()[0] if len(n) > 14 else n)}</span></th>' for i, (n, _) in enumerate(crit, 1))
    trs = []
    for r in rows:
        trs.append(f'''<tr class="{r["cls"]}" style="height:{row_h}">
          <td class="num">{r["num"]}<small>{r["sub"]}</small></td>
          <td class="ph">{r["av"].replace('class="av', f'style="width:{av_px};height:{av_px}" class="av')}</td>
          <td class="who"><div class="nm">{r["name"]}<span class="tag">{r["tag"]}</span></div><div class="ttl">{r["title"]}</div></td>
          {''.join('<td class="box"><div></div></td>' for _ in crit)}
          <td class="box tot"><div></div></td><td class="coi"><span></span></td><td class="cm"><div></div></td></tr>''')
    return f'''<section class="page" style="height:{page_h};--bh:{box_h}">
  <header><img src="{LOGO}" alt="">
    <div><p class="k">Judge evaluation · {esc(kind)}</p><h1>MRFA Research Day <span>Florida 2026</span></h1><p class="s">{title_line}</p></div>
    <div class="judge"><span>Judge</span><span class="ln"></span><span>Signature</span><span class="ln"></span></div></header>
  <div class="rubric" style="grid-template-columns:repeat({len(crit)},1fr)">{rub}</div>
  <p class="note"><span><b>Score each criterion from 1 to 10</b> (1–3 needs improvement · 4–6 good · 7–8 very good · 9–10 outstanding). Total out of {10 * len(crit)}.</span>
    <span><b>COI:</b> tick and leave blank if you are an author, mentor or PI on that work.</span></p>
  <table><colgroup>{sub}</colgroup>
    <thead><tr><th>#</th><th></th><th class="l">Presenter and title</th>{heads}<th>Total<br><span style="font-weight:500">/{10 * len(crit)}</span></th><th>COI</th><th class="l">Comments</th></tr></thead>
    <tbody>{"".join(trs)}</tbody></table>
  <footer><span>{extra_note}</span><span>Mayo Clinic Research Fellows’ Association (MRFA) · Thursday, October 29, 2026 · Kinne Auditorium</span></footer>
</section>'''


def oral_html():
    pages = []
    cols = '<col style="width:.55in"><col style="width:.5in"><col style="width:4.55in">' + '<col style="width:.52in">' * 4 + '<col style="width:.56in"><col style="width:.34in"><col>'
    for a in [x for x in ev["agenda"] if x.get("type") == "session"]:
        n = 1 if a["start"] < "12:00" else 2
        rows = []
        for tid in a["talks"]:
            t = talks[tid]
            full = "rapid" not in t["format"].lower()
            rows.append(dict(cls="full" if full else "rapid", num=esc(t["code"]), sub=fmt(t["start"]), av=avatar(t),
                             name=esc(short(t["presenter"]) + (", " + t["degrees"] if t.get("degrees") else "")), tag="Oral 10 min" if full else "Rapid-fire 5 min",
                             title=esc(t["title"])))
        pages.append(sheet("Oral and rapid-fire presentations", f"Session {ROMAN[n]} · {fmt(a['start'])} – {fmt(a['end'])} · Moderator: {esc(a.get('moderator', ''))}",
                           cols, rows, ORAL, ".44in", ".38in", "7.6in",
                           f"<b>Return this sheet</b> to the registration desk at the end of Session {ROMAN[n]}.", ".3in"))
    return pages, "@page { size: Letter landscape; margin: .4in; }"


def poster_sheet(a, ps):
    n = 1 if a["start"] < "12:00" else 2
    rub = "".join(f'<div><b><i>{i}</i>{esc(nm)}</b>{esc(d)}</div>' for i, (nm, d) in enumerate(POSTER, 1))
    heads = "".join(f'<th>{i}<br><span style="font-weight:500">{esc(nm.split()[0])}</span></th>' for i, (nm, _) in enumerate(POSTER, 1))
    trs = "".join(f'''<tr><td class="num">{esc(p["code"])}</td><td class="ph">{avatar(p)}</td>
      <td class="pr"><div class="nm">{esc(short(p["presenter"]) + (", " + p["degrees"] if p.get("degrees") else ""))}</div></td>
      <td class="pt">{esc(p["title"])}</td>{"".join('<td class="box"><div></div></td>' for _ in POSTER)}<td class="box tot"><div></div></td><td class="cm"></td></tr>''' for p in ps)
    return f'''<section class="page">
  <header><img src="{LOGO}" alt="">
    <div><p class="k">Judge evaluation · Posters</p><h1>MRFA Research Day <span>Florida 2026</span></h1><p class="s">Poster session {ROMAN[n]} · {fmt(a['start'])} – {fmt(a['end'])} · {len(ps)} posters</p></div>
    <div class="judge"><span>Judge</span><span class="ln"></span><span>Signature</span><span class="ln"></span></div></header>
  <div class="rubric" style="grid-template-columns:repeat(4,1fr)">{rub}</div>
  <p class="note"><span><b>Score each criterion from 1 to 10</b> (1–3 needs improvement · 4–6 good · 7–8 very good · 9–10 outstanding). Total out of 40. Score only the posters you visit; leave blank any poster you are an author, mentor or PI on.</span></p>
  <table class="pt-table"><colgroup><col style="width:.4in"><col style="width:.24in"><col style="width:1.3in"><col><col style="width:.36in"><col style="width:.36in"><col style="width:.36in"><col style="width:.36in"><col style="width:.4in"><col style="width:.5in"></colgroup>
    <thead><tr><th>#</th><th></th><th class="l">Presenter</th><th class="l">Title</th>{heads}<th>Total<br><span style="font-weight:500">/40</span></th><th class="l">Notes</th></tr></thead>
    <tbody>{trs}</tbody></table>
  <footer><span><b>Return this sheet</b> to the registration desk by {fmt(a['end'])}.</span><span>MRFA Research Day · Thursday, October 29, 2026</span></footer>
</section>'''


def poster_html():
    pages = [poster_sheet(a, [p for p in ev["posters"] if p.get("posterSession", 1) == (1 if a["start"] < "12:00" else 2)])
             for a in ev["agenda"] if a.get("type") == "posters"]
    return pages, "@page { size: Letter; margin: .35in; }"


POSTER_CSS = """
.page { height: 10.25in; }
header { padding: 8pt 13pt; } header img { width: 36pt; } header h1 { font-size: 13.5pt; } header .s { font-size: 8.4pt; } header .k { font-size: 7pt; }
.judge { font-size: 8pt; grid-template-columns: auto 2in; }
.rubric { margin: 5pt 0 4pt; gap: 4pt; } .rubric div { font-size: 6.6pt; padding: 2pt 5pt; line-height: 1.12; } .rubric b { font-size: 7.6pt; }
.note { font-size: 6.8pt; margin: 0 0 3pt; }
th { font-size: 6.6pt; padding: 2.5pt 2pt; }
.pt-table td { padding: 1.6pt 3pt; vertical-align: middle; }
.pt-table td.num { font-size: 7.4pt; }
.pt-table td.ph { padding: 1pt; } .pt-table .av { width: .2in; height: .2in; font-size: 5.6pt; }
.pt-table .nm { font-size: 7pt; line-height: 1.1; white-space: normal; }
.pt-table .ar { font-size: 5.9pt; line-height: 1.1; color: #6b7785; }
.pt-table td.pt { font-size: 6.6pt; line-height: 1.12; color: #33404f; }
.pt-table td.box { padding: 1.5pt 2pt; } .pt-table td.box div { height: .19in; }
.pt-table td.cm { border-left: .6pt dotted #9fb0c8; }
footer { padding-top: 4pt; font-size: 6.8pt; }
"""


def build(name, maker, poster=False):
    pages, page_css = maker()
    css = CSS + ("" if poster else ".ttl{line-height:1.13}.rubric{margin:7pt 0 5pt}header{padding:10pt 16pt}")
    if poster:
        css += POSTER_CSS
    doc = f'<!doctype html><html><head><meta charset="utf-8"><style>{font_faces()}{page_css}{css}</style></head><body>{"".join(pages)}</body></html>'
    cands = glob.glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=cands[0]) if cands else p.chromium.launch()
        pg = b.new_page()
        pg.set_content(doc, wait_until="load")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        over = pg.evaluate("[...document.querySelectorAll('.page')].map(p => p.scrollHeight - p.clientHeight)")
        pdf = pg.pdf(prefer_css_page_size=True, print_background=True)
        b.close()
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / name
    f.write_bytes(pdf)
    print(f"Wrote {f}: {len(PdfReader(str(f)).pages)} pages, overflow {over}")


if __name__ == "__main__":
    build("judging-oral.pdf", oral_html)
    build("judging-posters.pdf", poster_html, poster=True)
