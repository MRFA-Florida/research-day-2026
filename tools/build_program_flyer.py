#!/usr/bin/env python3
"""Build the one-page printable program flyer (assets/program-flyer.pdf) from data/event.json.

Usage (from the repository root):
    pip install playwright pypdf && playwright install chromium
    python3 tools/build_program_flyer.py

Re-run after any change to the agenda, talks, presenters or poster counts, then commit the PDF.
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

OUT = ROOT / "assets" / "program-flyer.pdf"
SITE = "https://mrfa-florida.github.io/research-day-2026/"
ev = json.loads((ROOT / "data" / "event.json").read_text())
E = ev["event"]
talks = {t["id"]: t for t in ev["talks"]}
SUNSET = "#f6b48a"


def short(name):
    return re.sub(r",.*$", "", re.sub(r"\(.*?\)\s*", "", name)).strip()


def block(a):
    when = f'{fmt(a["start"])}<span class="to">–{fmt(a["end"])}</span>'
    kind = a.get("type", "")
    if kind == "session":
        rows = []
        for tid in a.get("talks", []):
            t = talks[tid]
            full = "rapid" not in t.get("format", "").lower()
            who = f'{short(t["presenter"])}{", " + esc(t["degrees"]) if t.get("degrees") else ""}'
            rows.append(f'<li class="{"full" if full else "rapid"}"><span class="t">{fmt(t["start"]).replace(" AM", "").replace(" PM", "")}</span>'
                        f'<span class="tag">{"Oral" if full else "Rapid"}</span><span class="who">{esc(who)}</span>'
                        f'<span class="ttl">{esc(t["title"])}</span></li>')
        mod = f'<span class="mod">Moderator: {esc(a["moderator"])}</span>' if a.get("moderator") else ""
        return f'''<section class="blk session"><div class="bh"><span class="when">{when}</span><h2>{esc(a["title"])}</h2>{mod}</div>
          <ol class="talks">{"".join(rows)}</ol></section>'''
    sub = ""
    if kind == "posters":
        n = 1 if a["start"] < "12:00" else 2
        ps = [p for p in ev["posters"] if p.get("posterSession", 1) == n]
        sub = f'{len(ps)} posters, {esc(ps[0]["code"])} to {esc(ps[-1]["code"])}' + (f' · {esc(a["setup"])}' if a.get("setup") else "")
    elif a.get("speakers"):
        sub = " and ".join(esc(f'{x["name"]}, {x["role"]}') for x in a["speakers"])
    elif a.get("who"):
        sub = esc(a["who"])
    return f'<section class="blk {esc(kind)}"><div class="bh"><span class="when">{when}</span><h2>{esc(a["title"])}</h2>{f"<span class=sub>{sub}</span>" if sub else ""}</div></section>'


def html():
    logo = data_uri(ROOT / "assets/img/mayo-clinic-logo-white.svg")
    qrjs = (ROOT / "assets/qrcode-generator.js").read_text()
    blocks = "".join(block(a) for a in ev["agenda"])
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{font_faces()}
@page {{ size: Letter; margin: 0; }}
* {{ box-sizing: border-box; }}
html, body {{ margin: 0; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
body {{ width: 8.5in; height: 11in; font: 8.2pt/1.28 'Inter', 'Atkinson Hyperlegible', sans-serif; color: #17202b; display: flex; flex-direction: column; overflow: hidden; }}
h1, h2, .when, .tag, .t {{ font-family: 'Familjen Grotesk', sans-serif; }}
header {{ background: {NAVY}; color: #fff; padding: .3in .5in .22in; display: grid; grid-template-columns: auto 1fr auto; gap: .28in; align-items: center; }}
header img {{ width: .78in; }}
header .k {{ margin: 0 0 3pt; font-size: 8.5pt; color: #cfe0f5; }}
header h1 {{ margin: 0; font-size: 25pt; line-height: 1; letter-spacing: -.01em; }}
header h1 span {{ color: {SUNSET}; font-weight: 500; }}
header .f {{ margin: 6pt 0 0; font-size: 10pt; color: #e3edf9; }}
header .f b {{ color: #fff; }}
.qr {{ background: #fff; padding: 5pt; border-radius: 6pt; width: 1.02in; text-align: center; color: {NAVY}; font: 700 6.6pt 'Familjen Grotesk', sans-serif; }}
.qr svg {{ width: 100%; height: auto; display: block; margin-bottom: 2pt; }}
main {{ flex: 1; padding: .16in .5in 0; display: flex; flex-direction: column; gap: 4pt; }}
.blk {{ border-radius: 6pt; overflow: hidden; break-inside: avoid; }}
.bh {{ display: grid; grid-template-columns: 1.05in 1fr; column-gap: 8pt; align-items: baseline; padding: 4pt 9pt; background: #e6effa; }}
.bh h2 {{ margin: 0; font-size: 10.2pt; color: {NAVY}; }}
.bh .sub, .bh .mod {{ grid-column: 2; font-size: 7.8pt; color: #4a5868; }}
.when {{ font-weight: 600; font-size: 8.6pt; color: {BLUE}; white-space: nowrap; font-variant-numeric: tabular-nums; }}
.when .to {{ color: #6b7785; font-weight: 500; }}
.posters .bh {{ background: #fde9dc; }}
.session .bh {{ background: {NAVY}; }}
.session .bh h2 {{ color: #fff; }}
.session .when {{ color: {SUNSET}; }} .session .when .to {{ color: #b8c7da; }}
.session .bh .mod {{ color: #cfe0f5; }}
.talks {{ list-style: none; margin: 0; padding: 2pt 9pt 3pt; border: 1px solid #d5dee8; border-top: 0; border-radius: 0 0 6pt 6pt; }}
.talks li {{ display: grid; grid-template-columns: .36in .44in 1.62in 1fr; gap: 5pt; align-items: baseline; padding: 1.4pt 0; border-bottom: .5pt solid #e6ebf1; white-space: nowrap; }}
.talks li:last-child {{ border-bottom: 0; }}
.talks .t {{ font-weight: 600; color: {BLUE}; font-variant-numeric: tabular-nums; }}
.tag {{ font-size: 6.4pt; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: #8a4b12; }}
.full .tag {{ color: {BLUE}; }}
.full .who, .full .ttl {{ font-weight: 700; }}
.who {{ overflow: hidden; text-overflow: ellipsis; }}
.ttl {{ overflow: hidden; text-overflow: ellipsis; color: #33404f; }}
footer {{ padding: 5pt .5in .26in; display: flex; justify-content: space-between; gap: 12pt; font-size: 7.6pt; color: #4a5868; border-top: 2pt solid {BLUE}; margin: 6pt .5in 0; padding-left: 0; padding-right: 0; }}
footer b {{ color: {NAVY}; }}
</style></head><body>
<header>
  <img src="{logo}" alt="">
  <div>
    <p class="k">{esc(E.get('host') or '')}</p>
    <h1>MRFA Research Day <span>Florida 2026</span></h1>
    <p class="f"><b>{esc(E.get('dateLabel'))}</b> · {esc(E.get('timeLabel'))} · {esc(E.get('location') or 'Kinne Auditorium')}, Mayo Clinic Florida</p>
  </div>
  <div class="qr"><div id="qr"></div>Program, abstracts,<br>Q&amp;A and ratings</div>
</header>
<main>{blocks}</main>
<footer>
  <span><b>Program, abstracts and live Q&amp;A:</b> mrfa-florida.github.io/research-day-2026</span>
  <span>Oral talks 10 min · Rapid-fire 5 min · Program subject to change</span>
</footer>
<script>{qrjs}</script>
<script>var q = qrcode(0, "M"); q.addData("{SITE}"); q.make(); document.getElementById("qr").innerHTML = q.createSvgTag({{ cellSize: 3, margin: 0, scalable: true }});</script>
</body></html>"""


def main():
    cands = glob.glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell")
    with sync_playwright() as p:
        b = p.chromium.launch(executable_path=cands[0]) if cands else p.chromium.launch()
        pg = b.new_page()
        pg.set_content(html(), wait_until="load")
        pg.evaluate("document.fonts.ready")
        pg.wait_for_timeout(300)
        overflow = pg.evaluate("document.body.scrollHeight - document.body.clientHeight")
        pdf = pg.pdf(format="Letter", print_background=True, prefer_css_page_size=True)
        b.close()
    OUT.write_bytes(pdf)
    pages = len(PdfReader(str(OUT)).pages)
    print(f"Wrote {OUT.relative_to(ROOT)}: {pages} page(s), overflow {overflow}px")
    if pages != 1 or overflow > 0:
        sys.exit("The flyer no longer fits on one page; shorten titles or tighten spacing.")


if __name__ == "__main__":
    main()
