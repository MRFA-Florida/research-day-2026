// Shared helpers: saved agenda, "Cite this abstract" and calendar (.ics) downloads.
(() => {
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const KEY = "mrfa-saved";
  let memory = [];

  // ---------- My agenda ----------
  const saved = {
    all() { try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch (e) { return memory.slice(); } },
    has(id) { return saved.all().includes(id); },
    toggle(id) {
      const list = saved.all(); const i = list.indexOf(id);
      if (i >= 0) list.splice(i, 1); else list.push(id);
      memory = list.slice();
      try { localStorage.setItem(KEY, JSON.stringify(list)); } catch (e) {}
      document.dispatchEvent(new CustomEvent("mrfa:saved", { detail: { id, on: i < 0 } }));
      return i < 0;
    },
  };
  const saveBtn = (id) => {
    const on = saved.has(id);
    return `<button type="button" class="mini-btn save-btn" data-save="${esc(id)}" aria-pressed="${on}">
      <span class="star" aria-hidden="true">${on ? "★" : "☆"}</span><span class="lbl">${on ? "Saved" : "Save"}</span></button>`;
  };
  const refreshSaveButtons = () => document.querySelectorAll("[data-save]").forEach((b) => {
    const on = saved.has(b.dataset.save);
    b.setAttribute("aria-pressed", on);
    b.querySelector(".star").textContent = on ? "★" : "☆";
    b.querySelector(".lbl").textContent = on ? "Saved" : "Save";
  });

  // ---------- Calendar ----------
  const pad = (n) => String(n).padStart(2, "0");
  const stamp = (d) => `${d.getUTCFullYear()}${pad(d.getUTCMonth() + 1)}${pad(d.getUTCDate())}T${pad(d.getUTCHours())}${pad(d.getUTCMinutes())}00Z`;
  const at = (ev, hhmm, plusMin = 0) => new Date(new Date(`${ev.date}T${hhmm}:00${ev.utcOffset || "-04:00"}`).getTime() + plusMin * 60000);
  const icsText = (s) => String(s || "").replace(/\\/g, "\\\\").replace(/\n/g, "\\n").replace(/[,;]/g, (m) => "\\" + m);
  function buildICS(items) {
    const lines = ["BEGIN:VCALENDAR", "VERSION:2.0", "PRODID:-//MRFA Research Day//EN", "CALSCALE:GREGORIAN", "METHOD:PUBLISH"];
    items.forEach((it) => {
      lines.push("BEGIN:VEVENT", `UID:${it.uid}@mrfa-research-day`, `DTSTAMP:${stamp(new Date())}`,
        `DTSTART:${stamp(it.start)}`, `DTEND:${stamp(it.end)}`, `SUMMARY:${icsText(it.title)}`,
        `LOCATION:${icsText(it.location)}`, `DESCRIPTION:${icsText(it.description)}`);
      if (it.url) lines.push(`URL:${it.url}`);
      (it.alarms || []).forEach((m) => lines.push("BEGIN:VALARM", "ACTION:DISPLAY", `DESCRIPTION:${icsText(it.title)}`, `TRIGGER:-PT${m}M`, "END:VALARM"));
      lines.push("END:VEVENT");
    });
    lines.push("END:VCALENDAR");
    return lines.join("\r\n");
  }
  function download(name, text) {
    const blob = new Blob([text], { type: "text/calendar;charset=utf-8" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = name;
    document.body.appendChild(a); a.click();
    setTimeout(() => { URL.revokeObjectURL(a.href); a.remove(); }, 1000);
  }
  const siteUrl = () => location.href.split("#")[0].split("?")[0].replace(/abstract\.html$/, "");
  const place = (ev) => [ev.location, ev.room, ev.campus].filter(Boolean).join(", ");
  const calendar = {
    event(ev) {
      download("MRFA-Research-Day-2026.ics", buildICS([{
        uid: "mrfa-2026-day", title: ev.fullName || ev.name, start: at(ev, ev.calStart || "09:30"), end: at(ev, ev.calEnd || "14:30"),
        location: place(ev), description: `Program, abstracts and Q&A: ${siteUrl()}`, url: siteUrl(), alarms: [1440, 60],
      }]));
    },
    talks(ev, talks, name) {
      download(name || "MRFA-talks.ics", buildICS(talks.filter((t) => t.start).map((t) => ({
        uid: `mrfa-2026-${t.id}`, title: `${t.code ? t.code + " " : ""}${t.presenter}: ${t.title}`,
        start: at(ev, t.start), end: at(ev, t.start, t.minutes || 10), location: place(ev),
        description: `${t.format || "Talk"}, ${t.presenter}. Abstract: ${siteUrl()}abstract.html?talk=${t.id}`,
        url: `${siteUrl()}abstract.html?talk=${t.id}`, alarms: [10],
      }))));
    },
  };
  const calBtn = (id) => `<button type="button" class="mini-btn" data-cal="${esc(id)}"><span aria-hidden="true">🗓</span> Add to calendar</button>`;

  // ---------- Cite ----------
  const citeBtn = (id) => `<button type="button" class="mini-btn" data-cite="${esc(id)}"><span aria-hidden="true">❝</span> Cite</button>`;
  function openCite(item) {
    let d = document.getElementById("cite-dialog");
    if (!d) {
      d = document.createElement("dialog"); d.id = "cite-dialog";
      d.innerHTML = `<div class="cite-inner"><h3>Cite this abstract</h3><p class="cite-text" id="cite-text"></p>
        <p class="cite-style">AMA style</p><div class="actions"><button class="btn" type="button" id="cite-copy">Copy citation</button>
        <button class="btn ghost" type="button" id="cite-close">Close</button></div></div>`;
      document.body.appendChild(d);
      d.querySelector("#cite-close").onclick = () => d.close();
    }
    d.querySelector("#cite-text").textContent = item.citation;
    const copy = d.querySelector("#cite-copy");
    copy.textContent = "Copy citation";
    copy.onclick = () => copyText(item.citation, copy);
    d.showModal();
  }
  function copyText(text, btn) {
    const done = () => { btn.textContent = "Copied"; setTimeout(() => (btn.textContent = "Copy citation"), 2000); };
    if (navigator.clipboard && window.isSecureContext) navigator.clipboard.writeText(text).then(done, () => fallback());
    else fallback();
    function fallback() {
      const ta = document.createElement("textarea"); ta.value = text; ta.style.position = "fixed"; ta.style.opacity = "0";
      document.body.appendChild(ta); ta.select();
      try { document.execCommand("copy"); done(); } catch (e) { btn.textContent = "Select and copy the text above"; }
      ta.remove();
    }
  }
  const citeBlock = (item) => item.citation ? `<section class="cite-block" aria-labelledby="cite-h">
      <h2 id="cite-h">Cite this abstract</h2><p class="cite-text">${esc(item.citation)}</p>
      <button type="button" class="btn ghost" data-copy-cite>Copy citation</button></section>` : "";

  window.MRFA = { saved, saveBtn, refreshSaveButtons, calendar, calBtn, citeBtn, openCite, citeBlock, copyText };
  document.addEventListener("mrfa:saved", refreshSaveButtons);
})();
