#!/usr/bin/env python3
"""Printable poster-board number cards, four per US Letter page with cut marks.

    python3 tools/build_poster_numbers.py [output_dir]

Writes poster-numbers.pdf (default folder: ./judging-sheets/, which is git-ignored).
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
LOGO = data_uri(ROOT / "assets/img/mayo-clinic-logo-white.svg")
SUNSET = "#f6b48a"
ROMAN = {1: "I", 2: "II"}
times = {}
for a in ev["agenda"]:
    if a.get("type") == "posters":
        times[1 if a["start"] < "12:00" else 2] = f'{fmt(a["start"])} – {fmt(a["end"])}'


def short(n):
    return re.sub(r",.*$", "", re.sub(r"\(.*?\)\s*", "", n)).strip()


def card(p):
    s = p.get("posterSession", 1)
    num = p["code"].replace("P-", "")
    return f'''<div class="card s{s}">
  <div class="top"><img src="{LOGO}" alt=""><span>MRFA Research Day<br><b>Florida 2026</b></span></div>
  <div class="mid"><span class="lbl">Poster</span><span class="num">{esc(num)}</span></div>
  <div class="bot"><span class="pill">Poster session {ROMAN[s]} · {esc(times.get(s, ""))}</span>
    <span class="who">{esc(short(p["presenter"]))}</span></div>
</div>'''


CSS = f"""
@page {{ size: Letter; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; font-family: 'Familjen Grotesk', 'Inter', sans-serif; }}
.sheet {{ width: 8.5in; height: 11in; position: relative; display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 1fr 1fr; page-break-after: always; }}
.sheet:last-child {{ page-break-after: auto; }}
.cell {{ display: grid; place-items: center; }}
.card {{ width: 3.85in; height: 5.1in; border-radius: 14pt; overflow: hidden; display: flex; flex-direction: column; background: #fff; border: 1.2pt solid #d5dee8; }}
.top {{ background: {NAVY}; color: #fff; display: flex; align-items: center; gap: 9pt; padding: 11pt 14pt; }}
.top img {{ width: 34pt; }}
.top span {{ font-size: 10pt; line-height: 1.15; color: #dbe8f7; font-weight: 600; }}
.top b {{ color: {SUNSET}; font-weight: 600; }}
.mid {{ flex: 1; display: flex; flex-direction: column; align-items: center; justify-content: center; }}
.lbl {{ font-size: 15pt; font-weight: 700; letter-spacing: .22em; text-transform: uppercase; color: {BLUE}; margin-bottom: -6pt; }}
.num {{ font-size: 150pt; font-weight: 700; line-height: 1; color: {NAVY}; letter-spacing: -.03em; font-variant-numeric: tabular-nums; }}
.bot {{ padding: 0 14pt 15pt; display: flex; flex-direction: column; align-items: center; gap: 7pt; }}
.pill {{ font-size: 9.5pt; font-weight: 700; padding: 4pt 11pt; border-radius: 999px; background: #e6effa; color: {BLUE}; }}
.s2 .pill {{ background: #fde9dc; color: #8a4b12; }}
.s2 .top {{ box-shadow: inset 0 -4pt 0 {SUNSET}; }}
.s1 .top {{ box-shadow: inset 0 -4pt 0 {BLUE}; }}
.who {{ font-family: 'Inter', sans-serif; font-size: 10.5pt; color: #4a5868; }}
/* cut guides */
.sheet::before, .sheet::after {{ content: ""; position: absolute; background: none; }}
.sheet::before {{ left: 50%; top: 0; bottom: 0; border-left: .6pt dashed #b8c4d2; }}
.sheet::after {{ top: 50%; left: 0; right: 0; border-top: .6pt dashed #b8c4d2; }}
"""


def main():
    posters = ev["posters"]
    pages = []
    for i in range(0, len(posters), 4):
        cells = "".join(f'<div class="cell">{card(p)}</div>' for p in posters[i:i + 4])
        pages.append(f'<section class="sheet">{cells}</section>')
    doc = f'<!doctype html><html><head><meta charset="utf-8"><style>{font_faces()}{CSS}</style></head><body>{"".join(pages)}</body></html>'
    cands = glob.glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=cands[0]) if cands else p.chromium.launch()
        pg = b.new_page()
        pg.set_content(doc, wait_until="load")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        pdf = pg.pdf(prefer_css_page_size=True, print_background=True)
        b.close()
    OUT.mkdir(parents=True, exist_ok=True)
    f = OUT / "poster-numbers.pdf"
    f.write_bytes(pdf)
    print(f"Wrote {f}: {len(PdfReader(str(f)).pages)} pages for {len(posters)} posters")


if __name__ == "__main__":
    main()
