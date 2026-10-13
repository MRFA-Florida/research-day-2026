(() => {
  const $ = (id) => document.getElementById(id);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = (hhmm) => {
    if (!hhmm) return "";
    let [h, m] = hhmm.split(":").map(Number);
    const ap = h >= 12 ? "PM" : "AM";
    return `${h % 12 || 12}:${String(m).padStart(2, "0")} ${ap}`;
  };
  const roman = (n) => (n === 1 ? "I" : n === 2 ? "II" : String(n));
  const clean = (n) => String(n).replace(/\(.*?\)/g, "").replace(/,.*$/, "").trim();
  const initials = (n) => clean(n).split(/\s+/).filter(Boolean).slice(0, 2).map((w) => w[0]).join("").toUpperCase();
  const id = new URLSearchParams(location.search).get("talk");
  const bust = `?v=${Date.now()}`;

  Promise.all([
    fetch(`data/event.json${bust}`, { cache: "no-store" }).then((r) => r.json()),
    fetch(`data/abstracts.json${bust}`, { cache: "no-store" }).then((r) => r.json()),
  ]).then(([data, abstracts]) => render(data, abstracts)).catch(() => {
    $("abs").innerHTML = `<p class="empty">This abstract couldn’t load. <a href="./#program">Go back to the program</a>.</p>`;
  });

  function render(data, abstracts) {
    const pid = new URLSearchParams(location.search).get("poster");
    if (pid) return renderPoster(data, abstracts, pid);
    const talks = data.talks || [];
    const i = talks.findIndex((t) => t.id === id);
    if (i < 0) { $("abs").innerHTML = `<p class="empty">That talk isn’t in the program. <a href="./#program">See all talks</a>.</p>`; return; }
    const t = talks[i], a = abstracts[id];
    const asPoster = (data.posters || []).find((p) => p.talk === t.id);
    document.title = `${t.title} | MRFA Research Day, Florida 2026`;

    // Authors: presenter (underlined) followed by co-authors, without repeating the presenter.
    const coNames = t.coauthors && t.coauthors.includes(";") ? t.coauthors.split(/;\s*/) : splitNames(t.coauthors);
    const names = [t.degrees ? `${t.presenter}, ${t.degrees}` : t.presenter, ...coNames.filter((n) => clean(n) !== clean(t.presenter))];
    const multi = a && a.affiliations && a.affiliations.length > 1;
    const authorsHTML = names.map((n, k) => {
      const sup = multi && a.authorAffil ? `<sup>${a.authorAffil[k] || ""}</sup>` : "";
      return k === 0 ? `<span class="presenting">${esc(n)}</span>${sup}` : `${esc(n)}${sup}`;
    }).join(", ");
    const affil = a && a.affiliations ? `<ul class="abs-affil">${a.affiliations.map((x, k) => `<li>${multi ? `<sup>${k + 1}</sup> ` : ""}${esc(x)}</li>`).join("")}</ul>` : "";

    const body = a ? a.sections.map((s) => `${s.h ? `<h2>${esc(s.h)}</h2>` : ""}${s.p.map((p) => `<p>${esc(p)}</p>`).join("")}`).join("")
      : `<p class="abs-missing">The abstract for this talk will be posted soon.</p>`;

    const q = t.questionUrl || data.event.defaultQuestionUrl || "";
    const pick = `${roman(t.session)}-${t.order} ${String(t.presenter).replace(/,.*$/, "").trim()}`;
    const prev = talks[i - 1], next = talks[i + 1];
    const navLink = (x, cls, label) => x ? `<a class="${cls}" href="abstract.html?talk=${esc(x.id)}"><small>${label}: Session ${roman(x.session)}, talk ${x.order}</small><span>${esc(clean(x.presenter))}</span></a>` : "";
    const photo = t.photo ? `<img src="${esc(t.photo)}" alt="" onerror="this.remove()">` : "";

    $("abs").innerHTML = `
      <p class="abs-meta">
        <span class="fmt ${/rapid/i.test(t.format) ? "rapid" : "full"}">${esc(t.format)}</span>${t.code ? `<span class="abs-code">Abstract ${esc(t.code)}</span>` : ""}
        <span>Session ${roman(t.session)}, talk ${esc(t.order)}</span>
        ${t.start ? `<span class="sep" aria-hidden="true"></span><span>${fmt(t.start)}${t.minutes ? `, ${t.minutes} min` : ""}</span>` : ""}
        ${a && a.category ? `<span class="sep" aria-hidden="true"></span><span>${esc(a.category)}</span>` : ""}
      </p>
      <h1 class="abs-title">${esc(t.title)}</h1>
      <p class="abs-authors">${authorsHTML}</p>
      ${affil}
      <p class="abs-note">Presenting author underlined.${t.pi ? ` Principal investigator: ${esc(t.pi)}.` : ""}${asPoster ? ` Also presented as poster ${esc(asPoster.code)} in poster session ${asPoster.posterSession === 2 ? "II, 1:15 PM" : "I, 10:30 AM"}.` : ""}</p>

      <div class="abs-presenter">
        <div class="initials" aria-hidden="true"><span>${esc(initials(t.presenter))}</span>${photo}</div>
        <div><strong>${esc(t.degrees ? `${t.presenter}, ${t.degrees}` : t.presenter)}</strong>${[t.role, t.department].filter(Boolean).length ? `<span class="small role">${esc([t.role, t.department].filter(Boolean).join(", "))}</span>` : ""}<span class="small">Presenting ${t.start ? `at ${fmt(t.start)}` : ""} in Kinne Auditorium</span></div>
      </div>

      <article class="abs-body">${body}
        ${a && a.keywords ? `<p class="abs-kw"><strong>Keywords:</strong> ${esc(a.keywords)}</p>` : ""}
        ${window.MRFA && a ? MRFA.citeBlock(t) : ""}
      </article>

      <div class="abs-actions">
        ${q ? `<p class="pick">In the forms, choose <strong>${esc(pick)}</strong></p>
               <a class="btn" href="${esc(q)}" target="_blank" rel="noopener">Ask a question</a>
               ${window.MRFARating ? MRFARating.button(t, data.event) : ""}
               <button class="btn ghost" type="button" id="show-qr">Show QR code</button>`
            : `<span class="btn" aria-disabled="true">Questions open on the day</span>`}
      </div>
      ${window.MRFA ? `<div class="mini-row">${MRFA.saveBtn(t.id)}${MRFA.calBtn(t.id)}<button class="mini-btn" type="button" onclick="window.print()"><span aria-hidden="true">⎙</span> Print</button></div>` : ""}
      <nav class="abs-nav" aria-label="Other abstracts">${navLink(prev, "prev", "Previous")}${navLink(next, "next", "Next")}</nav>`;

    if (window.MRFARating) MRFARating.init(data.event);
    wireExtras(data, t);
    const qrBtn = $("show-qr");
    if (qrBtn) qrBtn.addEventListener("click", () => {
      $("qr-sub").innerHTML = `Then choose <strong>${esc(pick)}</strong> in the form.`;
      const qr = qrcode(0, "M"); qr.addData(q); qr.make();
      $("qr-big").innerHTML = qr.createSvgTag({ cellSize: 4, margin: 0, scalable: true });
      $("qr-dialog").showModal();
    });
  }

  function renderPoster(data, abstracts, pid) {
    const list = data.posters || [];
    const i = list.findIndex((p) => p.id === pid);
    if (i < 0) { $("abs").innerHTML = `<p class="empty">That poster isn’t listed. <a href="speakers.html#posters">See all posters</a>.</p>`; return; }
    const p = list[i], a = abstracts[pid] || {};
    if (p.talk) { location.replace(`abstract.html?talk=${encodeURIComponent(p.talk)}`); return; }
    const own = list.filter((x) => !x.talk), k = own.indexOf(p);
    const ps = p.posterSession === 2 ? ["II", "1:15 PM"] : ["I", "10:30 AM"];
    document.title = `${p.title} | MRFA Research Day, Florida 2026`;
    document.querySelectorAll(".abs-back").forEach((el) => { el.href = "speakers.html#posters"; el.textContent = "Back to posters"; });
    const multi = a.affiliations && a.affiliations.length > 1;
    const isPres = (n) => clean(n) === clean(p.presenter) || n.split(" ").pop() === p.presenter.split(" ").pop() && n[0] === p.presenter[0];
    const onBehalf = a.authors && !a.authors.some(isPres);
    const authors = (a.authors || [p.presenter]).map((n, k) => {
      const sup = multi && a.authorAffil ? `<sup>${a.authorAffil[k] || ""}</sup>` : "";
      return clean(n) === clean(p.presenter) || n.split(" ").pop() === p.presenter.split(" ").pop() && n[0] === p.presenter[0]
        ? `<span class="presenting">${esc(n)}</span>${sup}` : `${esc(n)}${sup}`;
    }).join(", ");
    const affil = a.affiliations ? `<ul class="abs-affil">${a.affiliations.map((x, k) => `<li>${multi ? `<sup>${k + 1}</sup> ` : ""}${esc(x)}</li>`).join("")}</ul>` : "";
    const body = (a.sections || []).map((s) => `${s.h ? `<h2>${esc(s.h)}</h2>` : ""}${s.p.map((x) => `<p>${esc(x)}</p>`).join("")}`).join("") || `<p class="abs-missing">The abstract for this poster will be posted soon.</p>`;
    const nav = (x, cls, label) => x ? `<a class="${cls}" href="abstract.html?poster=${esc(x.id)}"><small>${label}: ${esc(x.number)}</small><span>${esc(clean(x.presenter))}</span></a>` : "";
    const who = [p.role, p.department].filter(Boolean).join(", ");
    $("abs").innerHTML = `
      <p class="abs-meta"><span class="fmt poster">Poster</span><span class="abs-code">Abstract ${esc(p.code || p.number)}</span><span>Poster session ${ps[0]}</span>
        ${p.category ? `<span class="sep" aria-hidden="true"></span><span>${esc(p.category)}</span>` : ""}</p>
      <h1 class="abs-title">${esc(p.title)}</h1>
      <p class="abs-authors">${authors}</p>
      ${affil}
      <p class="abs-note">${onBehalf ? `Presented by ${esc(p.presenter)} on behalf of the authors.` : "Presenting author underlined."}${p.pi ? ` Principal investigator: ${esc(p.pi)}.` : ""}</p>
      <div class="abs-presenter">
        <div class="initials" aria-hidden="true"><span>${esc(initials(p.presenter))}</span></div>
        <div><strong>${esc(p.degrees ? `${p.presenter}, ${p.degrees}` : p.presenter)}</strong>${who ? `<span class="small role">${esc(who)}</span>` : ""}<span class="small">Presenting at poster session ${ps[0]}, ${ps[1]}</span></div>
      </div>
      <article class="abs-body">${body}${a.keywords ? `<p class="abs-kw"><strong>Keywords:</strong> ${esc(a.keywords)}</p>` : ""}${window.MRFA && p.citation ? MRFA.citeBlock(p) : ""}</article>
      ${window.MRFA ? `<div class="mini-row abs-mini">${MRFA.saveBtn(p.id)}<button class="mini-btn" type="button" onclick="window.print()"><span aria-hidden="true">⎙</span> Print</button></div>` : ""}
      <nav class="abs-nav" aria-label="Other posters">${nav(own[k - 1], "prev", "Previous")}${nav(own[k + 1], "next", "Next")}</nav>`;
    wireExtras(data, p);
  }

  function wireExtras(data, item) {
    if (!window.MRFA) return;
    document.querySelectorAll("[data-copy-cite]").forEach((b) => b.addEventListener("click", () => {
      MRFA.copyText(item.citation, b);
    }));
    document.querySelectorAll("[data-save]").forEach((b) => b.addEventListener("click", () => MRFA.saved.toggle(b.dataset.save)));
    document.querySelectorAll("[data-cal]").forEach((b) => b.addEventListener("click", () =>
      MRFA.calendar.talks(data.event, [item], `${item.code}-${item.presenter.split(" ").pop()}.ics`)));
  }

  // Comma-separated author list, where credentials like "MD" also follow commas.
  function splitNames(s) {
    if (!s) return [];
    const parts = s.split(/,\s*/), out = [];
    for (const p of parts) {
      if (/^(MD|PhD|DO|MBBS|MBChB|MPH|MS|MSc|RN|PharmD|DNP|BS|BA|LP|ABPP-CN)\.?$/i.test(p) && out.length) out[out.length - 1] += ", " + p;
      else out.push(p);
    }
    return out;
  }
})();
