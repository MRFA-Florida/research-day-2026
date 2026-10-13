# MRFA Research Day, Florida 2026

Event website for the **Mayo Clinic Research Fellow’s Association (MRFA) Research Day**
Thursday, October 29, 2026 · Kinne Auditorium, Mayo Clinic in Florida

**Live site:** https://mrfa-florida.github.io/research-day-2026/
**All MRFA Florida events:** https://mrfa-florida.github.io

The site is plain HTML, CSS and JavaScript hosted free on GitHub Pages. There is no build step: edit a file on github.com, commit, and the site updates in about a minute.

---

## What the site includes

| Section | What attendees see |
|---|---|
| **Program** | Full agenda with a live **Now / Next** bar on the event day (Florida time). Each talk opens to show presenter, PI, co-authors and actions. Full oral talks are highlighted in blue. |
| **Speakers** | Cards with photo, degrees, role and department. Filter by session or format. |
| **Panel** | Organizing committee, moderator and judges, with photos and short bios. |
| **Posters** | Searchable list grouped by category, each linked to its abstract. |
| **Awards** | Award categories; winners appear here once announced. Explains the Audience Choice Award. |
| **My agenda** | Talks and posters an attendee saved with ☆ Save (kept on their device). |
| **Info** | FAQ, Q&A form, and a QR code for the site. |
| **Abstract pages** | `abstract.html?talk=s1-04` or `abstract.html?poster=p09`: journal-style abstract with authors, affiliations, abstract code, and **Cite this abstract** (AMA). |

Per-talk actions: **Ask a question** (Microsoft Forms), **Rate this talk** (unlocks when the talk starts, closes at 1:30 PM), Save, Abstract, Cite, **Add to calendar** (.ics with a 10-minute reminder) and QR code. The header has **Add to calendar** for the whole day (reminders 1 day and 1 hour before). The site follows the device's light/dark setting, with a button to switch.

---

## Editing content (no coding needed)

Almost everything comes from two files:

| File | Contains |
|---|---|
| `data/event.json` | Event details, agenda, talks, posters, people, awards, FAQ, form links |
| `data/abstracts.json` | Abstract text, author lists and affiliations, keyed by talk/poster ID |

**To edit:** open the file on github.com → pencil icon → change the text → **Commit changes**.

Rules that keep the JSON valid:
- Keep every value inside `"double quotes"`.
- Items in a list are separated by commas; the **last item has no comma** after it.
- Times use 24-hour format: `"13:15"` for 1:15 PM. Dates use `"YYYY-MM-DD"`.
- If the page says "The program couldn't load", the file has a typo (usually a comma). Undo the last change from the commit history.

### `data/event.json` sections

| Key | What it controls |
|---|---|
| `event` | Name, date, `timeLabel` shown in the header, location, intro, tagline, `defaultQuestionUrl` (Q&A form), `ratingUrl` (rating form), `ratingCloses`, Audience Choice text (`award`), calendar times (`calStart`, `calEnd`) |
| `agenda` | Program blocks. `type` is `session`, `plenary`, `break` or `posters`. Sessions list their talk IDs in `talks` and name the `moderator` |
| `talks` | One entry per oral presentation: `id`, `code` (O-01…), `session`, `order`, `start`, `minutes`, `format` (`Full oral` / `Rapid-fire`), `presenter`, `degrees`, `role`, `department`, `pi`, `coauthors`, `title`, `photo`, `abstract` (true/false), `citation` |
| `posters` | One entry per poster: `id` (p01…), `number`/`code` (P-01…), presenter details, `category`, `title`, `citation` |
| `committee`, `moderators`, `judges` | People cards: `name`, `degrees`, `title`, `role`, `photo`, `sessions` (tag), `bio`. An empty `judges` list shows `judgesNote` instead |
| `awards` | Award categories and winners (see below) |
| `info` | Question-and-answer pairs in the Info section |

**IDs:** talks are `s1-01`…`s1-11` (Session I) and `s2-01`…`s2-11` (Session II); posters are `p01`…`p21`. IDs link the agenda, abstracts, saved items and awards together, so don't change them without updating every place they appear.

**Talk times:** each talk's `start` drives the Now/Next bar, the rating unlock and calendar files. Full orals are 10 minutes and rapid-fire talks 5 minutes.

### Speaker photos
Upload to `assets/img/speakers/` named after the presenter in lowercase with hyphens, e.g. `diego-sanchez-calderin.jpg`, and set the talk's `photo` to that path. Square crops around 400×400 px load fastest; any size works, but large camera files slow the page on phones. A missing photo shows the person's initials.

### Q&A and rating forms
Both are Microsoft Forms with a "Which talk?" dropdown whose options must match the site exactly, e.g. `I-4 Diego Sanchez-Calderin` (session in Roman numerals, running order, presenter name without degrees). The site shows "In the forms, choose …" next to each button. **If you change the running order or a presenter, update both forms' dropdowns.**

### Announcing award winners
In `data/event.json` → `awards`, replace `null` with the winning ID:

```json
{ "id": "best-oral", "title": "Best Full Oral Presentation", "winner": { "id": "s1-04" } }
```

Use a talk ID (`s1-04`) or poster ID (`p09`). Optional: `"note": "Runner-up: …"` inside `winner`. The winner's photo, name, title and abstract link appear automatically.

### Citations
Each talk and poster has a pre-built AMA `citation`. If you change a title, author list or abstract code, update the citation too (or ask Claude to regenerate them).

### Abstract Book (PDF)
The **Download Abstract Book** button in the header serves `assets/abstract-book.pdf`: cover, welcome and program at a glance, contents with page numbers, then every abstract in program order (O-01…O-22, then P-01…P-21), one per page with its AMA citation. It is built from the two data files, so after changing an abstract, title, author or the running order, rebuild it:

```
pip install playwright pypdf && playwright install chromium
python3 tools/build_abstract_book.py
```

Then commit the new PDF (or ask Claude to rebuild it).

---

## Testing before the day

Add `?preview=HH:MM` to any page address to see it as if it were that time on the event day:

- `…/research-day-2026/?preview=09:40` — Now/Next bar on Session I, rating open for talk I-4
- `…/research-day-2026/?preview=13:40` — ratings closed

---

## Files

```
index.html            Main page (structure only; content comes from data/)
abstract.html         Abstract page for talks and posters
data/event.json       Event content
data/abstracts.json   Abstract text and authors
assets/app.js         Program, speakers, posters, panel, awards, My agenda, Now/Next
assets/abstract.js    Abstract pages
assets/extras.js      Save, Cite and Add-to-calendar
assets/rating.js      Timed "Rate this talk" buttons
assets/theme.js       Light / dark / auto
assets/styles.css     Site styles (abstract.css for abstract pages)
assets/qrcode-generator.js  QR codes (MIT, Kazuhiko Arase)
assets/abstract-book.pdf    Abstract Book (built by tools/build_abstract_book.py)
tools/                Abstract Book builder and its fonts (OFL)
assets/img/           Logo, campus photos, link-preview image, speaker photos
```

---

## Reusing the site for next year

1. Mark this repository as a template (**Settings → General → Template repository**).
2. On the repository page click **Use this template → Create a new repository** in `MRFA-Florida`, named e.g. `research-day-2027`.
3. In the new repository, update `data/event.json` and `data/abstracts.json`, replace speaker photos, and update the address in the `og:` tags at the top of `index.html` and `abstract.html` (used for link previews).
4. Turn on **Settings → Pages** (branch `main`, folder `/ (root)`).
5. Add the event to `events.json` in the `MRFA-Florida.github.io` repository so it appears on the MRFA Florida landing page. Past events move to "Past events" automatically.

## Ownership

Maintained by the MRFA Florida organizing committee in the `MRFA-Florida` GitHub organization. Keep at least two current MRFA officers as organization **Owners** so access isn't lost when trainees rotate out.

Mayo Clinic name and logo are used for this Mayo Clinic Research Fellow’s Association event; confirm brand use with MRFA leadership or Mayo Clinic communications.
