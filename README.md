# MRFA Research Day website

Live site: https://verasteguialfredo.github.io/mrfa-research-day/

Photos: Mayo Clinic in Florida campus (assets/img). Logo: assets/img/mayo-clinic-logo*.svg.

## Editing the event (no coding needed)

Everything on the site comes from one file: **`data/event.json`**.

1. Open `data/event.json` on github.com and click the pencil icon.
2. Change the text between the quotes (times, names, titles, room, links).
3. Click **Commit changes**. The site updates in about a minute.

Rules that keep the file valid:
- Keep every value inside `"double quotes"`.
- Items in a list are separated by commas, but the **last item has no comma** after it.
- Times use 24-hour format: `"13:15"` for 1:15 PM.
- If the page shows "The program couldn't load", the file has a typo. Usually it's a missing or extra comma. Undo your last change from the commit history.

### What each section does
| Section | What to edit |
|---|---|
| `event` | Name, date (`YYYY-MM-DD`), location, intro text, contact email, `notice` (set to `""` to hide the draft banner) |
| `agenda` | The program blocks. `type` is `session`, `plenary`, `break` or `posters`. Sessions list their talk IDs in `talks` |
| `talks` | One entry per oral presentation. `id` links it to the agenda. `questionUrl` is the Microsoft Forms link for that talk |
| `posters` | Poster number, presenter, category, title |
| `judges` | A list of names, e.g. `["Dr. A", "Dr. B"]`. Leave `[]` to hide |
| `info` | Question-and-answer pairs shown in the Info section |

### Questions for each talk
Paste a Microsoft Forms link into a talk's `questionUrl`. To use one form for every talk, put it in `event.defaultQuestionUrl` instead. Talks without a link show "Questions open on the day".

### Previewing the live "Now" view
On the event date, the site highlights the current block and shows a Now/Next bar using Florida time. To preview it any day, add `?preview=10:30` to the address.

## Announcing award winners
In `data/event.json`, find `"awards"` and replace `null` with the winning talk or poster ID, for example
`"winner": { "id": "s1-04" }` (talk) or `"winner": { "id": "p09" }` (poster). Talk IDs: `s1-01`…`s2-11`; poster IDs: `p01`…`p21`.

## Citations
Each talk and poster has a pre-built AMA `citation` in `data/event.json`. If you change a title or author, update that line too (or ask Claude to regenerate them).
