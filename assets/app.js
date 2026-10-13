(() => {
  const TZ = "America/New_York";
  // Missing elements (e.g. on speakers.html) resolve to a detached stand-in so shared code can run on any page.
  const $ = (id) => document.getElementById(id) || document.createElement("div");
  const onIndex = !!document.getElementById("run");
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const toMin = (hhmm) => { const [h, m] = String(hhmm).split(":").map(Number); return h * 60 + m; };
  const fmt = (hhmm) => {
    if (!hhmm) return "";
    let [h, m] = hhmm.split(":").map(Number);
    const ap = h >= 12 ? "PM" : "AM";
    h = h % 12 || 12;
    return `${h}:${String(m).padStart(2, "0")}`+ ` ${ap}`;
  };
  const initials = (name) => { const w = String(name).replace(/\(.*?\)/g, "").split(/\s+/).filter((x) => x && !/^[A-Z]\.$/.test(x)); return ((w[0] || "")[0] + (w.length > 1 ? w[w.length - 1][0] : "")).toUpperCase(); };

  // Current date and minutes-of-day in the event's time zone.
  function nowInTZ() {
    const parts = Object.fromEntries(new Intl.DateTimeFormat("en-CA", {
      timeZone: TZ, year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit", hourCycle: "h23"
    }).formatToParts(new Date()).map((p) => [p.type, p.value]));
    return { date: `${parts.year}-${parts.month}-${parts.day}`, min: Number(parts.hour) * 60 + Number(parts.minute) };
  }
  // ?preview=10:15 lets organizers check how the "Now" view looks before the day.
  const preview = new URLSearchParams(location.search).get("preview");

  let data, talksById = {}, postersById = {};
  const itemById = (id) => talksById[id] || postersById[id];

  fetch(`data/event.json?v=${Date.now()}`, { cache: "no-store" })
    .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then((d) => { data = d; render(); openFromHash(); tick(); setInterval(tick, 15000); if (window.MRFARating) MRFARating.init(d.event); })
    .catch(() => {
      $("run").innerHTML = `<li class="empty">The program couldn’t load. Check that data/event.json is valid JSON (a missing comma is the usual cause), then refresh.</li>`;
    });

  function questionUrl(t) { return t.questionUrl || data.event.defaultQuestionUrl || ""; }

  // Exactly matches the dropdown option in the Q&A form, e.g. "I-4 Paola Suarez Meade".
  const fullName = (t) => t.degrees ? `${t.presenter}, ${t.degrees}` : t.presenter;
  const roleLine = (t) => [t.role, t.department].filter(Boolean).join(", ");
  const pickLabel = (t) => `${t.session === 1 ? "I" : "II"}-${t.order} ${String(t.presenter).replace(/,.*$/, "").trim()}`;
  function actionsHTML(t) {
    const url = questionUrl(t);
    const X = window.MRFA;
    const mini = `<div class="mini-row">
      ${X ? X.saveBtn(t.id) : ""}
      ${t.abstract ? `<a class="mini-btn" href="abstract.html?talk=${esc(t.id)}"><span aria-hidden="true">📄</span> Abstract</a>` : ""}
      ${X && t.citation ? X.citeBtn(t.id) : ""}
      ${X ? X.calBtn(t.id) : ""}
      ${url ? `<button class="mini-btn" type="button" data-qr="${esc(t.id)}"><span aria-hidden="true">▦</span> QR code</button>` : ""}
    </div>`;
    if (!url) return `<div class="actions"><span class="btn" aria-disabled="true">Questions open on the day</span></div>${mini}`;
    return `<p class="pick">In the forms, choose <strong>${esc(pickLabel(t))}</strong></p><div class="actions">
      <a class="btn" href="${esc(url)}" target="_blank" rel="noopener">Ask a question</a>
      ${window.MRFARating ? MRFARating.button(t, data.event) : ""}
    </div>${mini}`;
  }

  function render() {
    const e = data.event;
    document.title = e.fullName || `${e.name} ${e.edition || ""}`.trim();
    $("host").textContent = e.host || "";
    $("event-name").innerHTML = `${esc(e.name)}${e.edition ? ` <span class="yr">${esc(e.edition)}</span>` : ""}`;
    $("event-date").textContent = e.dateLabel || e.date;
    $("event-time").textContent = e.timeLabel || "";
    const place = [e.location, e.room].filter(Boolean).join(", ");
    $("event-place").innerHTML = e.mapUrl ? `<a href="${esc(e.mapUrl)}" style="color:inherit">${esc(place)}</a>` : esc(place);
    $("event-intro").innerHTML = String(e.intro || "").split(/\n\s*\n/).map((x) => `<p>${esc(x)}</p>`).join("");
    if (e.tagline) { $("tagline").textContent = e.tagline; $("tagline").hidden = false; }
    if (e.notice) { $("event-notice").textContent = e.notice; $("event-notice").hidden = false; }
    $("foot-host").textContent = `${e.name} ${e.edition || ""}, ${e.host || ""}`.trim();

    (data.talks || []).forEach((t) => (talksById[t.id] = t));
    (data.posters || []).forEach((p) => (postersById[p.id] = p));

    // Program
    $("run").innerHTML = (data.agenda || []).map((s, i) => {
      const talks = (s.talks || []).map((id) => talksById[id]).filter(Boolean);
      const when = s.start ? `${fmt(s.start)}${s.end ? ` – ${fmt(s.end)}` : ""}` : esc(s.timeLabel || "");
      const meta = [s.moderator ? `<span class="who-row">${s.moderatorPhoto ? avatar({ presenter: s.moderator, photo: s.moderatorPhoto }, "sm") : ""}Moderator: ${esc(s.moderator)}</span>` : "", s.who ? (s.link ? `<a class="slot-link" href="${esc(s.link)}">${esc(s.who)}</a>` : esc(s.who)) : ""].filter(Boolean).join("<br>");
      const counts = talks.length ? `${talks.filter((t) => /full/i.test(t.format)).length} full talks, ${talks.filter((t) => /rapid/i.test(t.format)).length} rapid-fire` : "";
      const nRapid = talks.filter((t) => fmtClass(t.format) === "rapid").length;
      const extra = slotExtra(s);
      const foldable = talks.length || extra;
      const what = talks.length ? "the talks" : extra ? extra.label.replace(/^Show /, "the ") : "";
      const fold = foldable ? `<button type="button" class="slot-fold" data-fold="slot-${i}" aria-expanded="false" aria-label="Show ${esc(what)} in ${esc(s.title)}"><svg viewBox="0 0 20 20" aria-hidden="true"><path d="M5 8l5 5 5-5" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg></button>` : "";
      const people = (s.speakers || []).length ? `<div class="slot-people">${s.speakers.map((p) => `<span class="sp">${avatar({ presenter: p.name, photo: p.photo }, "sm")}<span><strong>${esc(p.name)}</strong>${p.role ? `<small>${esc(p.role)}</small>` : ""}</span></span>`).join("")}</div>` : "";
      return `<li class="slot ${esc(s.type || "")}${foldable ? " foldable folded" : ""}" id="slot-${i}" data-start="${esc(s.start || "")}" data-end="${esc(s.end || "")}">
        <div class="slot-head">
          <span class="slot-title">${esc(s.title)}<span class="now-label" hidden>Now</span></span>
          <span class="slot-when">${when}${fold}</span>
          ${meta ? `<div class="slot-meta">${meta}</div>` : ""}
          ${people}
        </div>
        ${talks.length ? `<ul class="talks" aria-label="${esc(s.title)}: ${counts}">${talks.map(talkHTML).join("")}</ul>` : ""}
        ${extra ? `<div class="slot-extra">${extra.html}</div>` : ""}
      </li>`;
    }).join("");

    // Speakers
    const sessions = [...new Set((data.talks || []).map((t) => t.session).filter(Boolean))];
    const filters = [["all", "All"], ...sessions.map((n) => [`s${n}`, `Session ${n}`]), ["full", "Full oral"], ["rapid", "Rapid-fire"], ...((data.posters || []).length ? [["posters", `Posters (${data.posters.length})`]] : [])];
    $("talk-filters").innerHTML = filters.map(([k, label], i) =>
      `<button type="button" class="chip" data-f="${k}" aria-pressed="${i === 0}">${esc(label)}</button>`).join("");
    setView(location.hash === "#posters" ? "posters" : "all");

    // Posters
    renderPosters("");
    renderAwards();
    renderMine();

    // Info
    // Moderator and judges
    const person = (p) => `<li class="person">
      <div class="person-head">
        ${avatar({ presenter: p.name, photo: p.photo }, "lg")}
        <div>
          <h4>${esc(p.degrees ? `${p.name}, ${p.degrees}` : p.name)}</h4>
          ${p.title ? `<p class="p-title">${esc(p.title)}</p>` : ""}
          ${p.role ? `<p class="p-role">${esc(p.role)}</p>` : ""}
          ${p.sessions ? `<span class="p-tag">${esc(p.sessions)}</span>` : ""}
        </div>
      </div>
      ${p.bio ? String(p.bio).split(/\n\s*\n/).map((x) => `<p class="p-bio">${esc(x)}</p>`).join("") : ""}
    </li>`;
    $("committee-list").innerHTML = (data.committee || []).map(person).join("");
    $("moderator-list").innerHTML = (data.moderators || []).map(person).join("");
    $("judge-list").innerHTML = (data.judges || []).map(person).join("");
    if (data.judgesNote) { $("judges-note").textContent = data.judgesNote; $("judges-note").hidden = false; }
    const mail = (m) => `<a href="mailto:${esc(m)}">${esc(m)}</a>`;
    $("faq").innerHTML = (data.info || []).map((f) => `<dt>${esc(f.q)}</dt><dd>${esc(f.a)}${f.email ? ` ${mail(f.email)}.` : ""}${
      f.groups ? `<div class="menu">${f.groups.map((g) => `<div><h4>${esc(g.h)}</h4><ul>${g.items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>`).join("")}</div>` : ""}</dd>`).join("");
    if (e.contactEmail && !(data.info || []).some((f) => f.email)) $("faq").innerHTML += `<dt>Email</dt><dd>${mail(e.contactEmail)}</dd>`;
    makeQR($("site-qr"), location.href.split("#")[0].split("?")[0], 112);
    if (e.award && e.ratingUrl) {
      $("award-card").hidden = false;
      $("award-title").textContent = e.award.title;
      $("award-text").innerHTML = e.award.text.map((p) => `<p>${esc(p)}</p>`).join("");
      $("award-open").dataset.url = e.ratingUrl;
      makeQR($("award-qr"), e.ratingUrl);
    }
    if (e.defaultQuestionUrl) {
      $("qa-card").hidden = false;
      $("qa-open").href = e.defaultQuestionUrl;
      makeQR($("qa-qr"), e.defaultQuestionUrl, 112);
    }
  }

  // Portrait if assets/img/speakers/<name>.jpg exists, otherwise initials.
  const avatar = (t, cls = "") => `<div class="initials ${cls}" aria-hidden="true"><span>${esc(initials(t.presenter.replace(/\(.*?\)/g, "").replace(/,.*$/, "")))}</span>${
    t.photo ? `<img src="${esc(t.photo)}" alt="" loading="lazy" onerror="this.remove()">` : ""}</div>`;
  const fmtClass = (f) => (/rapid/i.test(f || "") ? "rapid" : "full");
  const shortName = (t) => String(t.presenter).replace(/\(.*?\)\s*/g, "").replace(/,.*$/, "").trim();
  // Collapsible extras for poster-session and meal slots (hidden until the slot's checkbox is ticked).
  function slotExtra(s) {
    if (s.type === "posters") {
      const n = s.start < "12:00" ? 1 : 2;
      const ps = (data.posters || []).filter((p) => (p.posterSession || 1) === n);
      if (!ps.length) return null;
      const link = (p) => p.talk ? `abstract.html?talk=${esc(p.talk)}` : `abstract.html?poster=${esc(p.id)}`;
      return { label: `Show posters (${ps.length})`, html: `<ul class="mini-list">${ps.map((p) => {
        const t = p.talk && talksById[p.talk];
        return `<li>
          <span class="pnum">${esc(p.number)}</span>
          <div class="ml-body">
            ${p.abstract ? `<a class="ml-title" href="${link(p)}">${esc(p.title)}</a>` : `<span class="ml-title">${esc(p.title)}</span>`}
            <span class="ml-who"><strong>${esc(fullName(p))}</strong>${p.department ? `, ${esc(p.department)}` : ""}</span>
            <span class="ml-area">${esc(p.category || "")}${t ? ` · Also oral ${esc(t.code)}` : ""}${!p.abstract ? " · Abstract to be posted" : ""}</span>
            ${window.MRFA ? `<div class="mini-row">${MRFA.saveBtn(p.id)}${p.citation ? MRFA.citeBtn(p.id) : ""}</div>` : ""}
          </div>
        </li>`; }).join("")}</ul>
        <p class="ml-more"><a href="speakers.html#posters">Search all posters</a></p>` };
    }
    if (/lunch/i.test(s.title || "")) {
      const food = (data.info || []).find((f) => f.groups);
      if (!food) return null;
      return { label: "Show menu", html: `<div class="menu">${food.groups.map((g) => `<div><h4>${esc(g.h)}</h4><ul>${g.items.map((x) => `<li>${esc(x)}</li>`).join("")}</ul></div>`).join("")}</div>` };
    }
    return null;
  }
  function talkHTML(t) {
    return `<li class="${fmtClass(t.format) === "full" ? "is-full" : "is-rapid"}"><details class="talk" id="talk-${esc(t.id)}" data-start="${esc(t.start || "")}">
      <summary>
        <span class="ord">${esc(t.order)}${t.start ? `<small>${fmt(t.start)}</small>` : ""}</span>
        <span class="talk-main">
          ${t.format ? `<span class="fmt ${fmtClass(t.format)}">${esc(t.format)}</span>` : ""}${t.code ? `<span class="code">${esc(t.code)}</span>` : ""}
          <span class="talk-title">${esc(t.title)}</span>
          <span class="talk-who">${esc(fullName(t))}</span><span class="talk-who-short">${esc(shortName(t))}</span>
        </span>
        <svg class="chev" viewBox="0 0 20 20" aria-hidden="true"><path d="M5 8l5 5 5-5" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
      </summary>
      <div class="talk-detail">
        <dl>
          ${t.minutes ? `<dt>Time</dt><dd>${fmt(t.start)}, ${esc(t.minutes)} minutes</dd>` : ""}
          <dt>Presenter</dt><dd class="who-row">${avatar(t, "sm")}<span>${esc(fullName(t))}${roleLine(t) ? `<br><small class="role">${esc(roleLine(t))}</small>` : ""}</span></dd>
          ${t.pi ? `<dt>PI / lab</dt><dd>${esc(t.pi)}</dd>` : ""}
          ${t.coauthors ? `<dt>Co-authors</dt><dd>${esc(t.coauthors)}</dd>` : ""}
        </dl>
        ${actionsHTML(t)}
      </div>
    </details></li>`;
  }

  // Speakers page: the chips switch between speaker cards and the poster list.
  function setView(f) {
    document.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", c.dataset.f === f));
    const posters = f === "posters";
    $("speaker-list").hidden = posters;
    $("posters").hidden = !posters;
    if (!posters) renderSpeakers(f);
    if (!onIndex) document.querySelectorAll(".tabs-inner > a").forEach((x) => x.setAttribute("aria-current", x.getAttribute("href") === (posters ? "speakers.html#posters" : "speakers.html")));
  }
  window.addEventListener("hashchange", () => { if (!onIndex && data) setView(location.hash === "#posters" ? "posters" : "all"); });

  function renderSpeakers(f) {
    const list = (data.talks || []).filter((t) =>
      f === "all" || f === `s${t.session}` || (f === "full" && fmtClass(t.format) === "full") || (f === "rapid" && fmtClass(t.format) === "rapid"));
    $("speaker-list").innerHTML = list.map((t) => `<li class="speaker${fmtClass(t.format) === "full" ? " is-full" : ""}">
      ${avatar(t)}
      <div>
        <h3>${esc(fullName(t))}</h3>
        <p class="aff">${esc(roleLine(t))}${t.pi ? `<br>PI: ${esc(t.pi)}` : ""}</p>
        <p class="ttl">${esc(t.title)}</p>
        <p class="when"><a href="${onIndex ? "" : "./"}#talk-${esc(t.id)}" data-open="${esc(t.id)}">Session ${esc(t.session)}, talk ${esc(t.order)}${t.start ? ` at ${fmt(t.start)}` : ""}</a>, ${esc(t.format || "")}</p>
        ${actionsHTML(t)}
      </div>
    </li>`).join("");
  }

  function renderPosters(q) {
    q = q.trim().toLowerCase();
    const all = data.posters || [];
    const list = all.filter((p) => !q || [p.number, p.boardId, p.presenter, p.title, p.category, p.department].join(" ").toLowerCase().includes(q));
    const sessions = [[1, "Poster session I", "10:30 – 11:30 AM"], [2, "Poster session II", "1:15 – 2:15 PM"]];
    const link = (p) => p.talk ? `abstract.html?talk=${esc(p.talk)}` : `abstract.html?poster=${esc(p.id)}`;
    $("poster-list").innerHTML = sessions.map(([n, label, time]) => {
      const items = list.filter((p) => (p.posterSession || 1) === n);
      if (!items.length) return "";
      return `<li class="pgroup"><h3>${esc(label)}, ${esc(time)} <span>${items.length}</span></h3><ul>${items.map((p) => {
        const t = p.talk && talksById[p.talk];
        return `<li class="poster">
        <span class="pnum">${esc(p.number)}</span>
        <div>
          <div class="ttl">${p.abstract ? `<a href="${link(p)}">${esc(p.title)}</a>` : esc(p.title)}</div>
          <div class="who"><strong>${esc(fullName(p))}</strong>${p.department ? `, ${esc(p.department)}` : ""}</div>
          <div class="parea">${esc(p.category || "")}${t ? ` · Also an oral presentation, ${esc(t.code)} at ${fmt(t.start)}` : ""}${!p.abstract ? " · Abstract to be posted" : ""}</div>
          ${window.MRFA ? `<div class="mini-row">${MRFA.saveBtn(p.id)}${p.citation ? MRFA.citeBtn(p.id) : ""}</div>` : ""}
        </div>
      </li>`;
      }).join("")}</ul></li>`;
    }).join("");
    $("poster-empty").hidden = list.length > 0;
  }

  function renderAwards() {
    $("awards-note").textContent = data.awardsNote || "";
    $("award-list").innerHTML = (data.awards || []).map((a) => {
      const w = a.winner && itemById(a.winner.id);
      if (!w) return `<li class="award pending"><h3>${esc(a.title)}</h3><p>To be announced at 2:15 PM</p></li>`;
      const isPoster = !!postersById[w.id];
      const link = isPoster ? (w.talk ? `abstract.html?talk=${esc(w.talk)}` : `abstract.html?poster=${esc(w.id)}`) : `abstract.html?talk=${esc(w.id)}`;
      return `<li class="award won">
        <h3><span aria-hidden="true">🏆</span> ${esc(a.title)}</h3>
        <div class="award-win">
          ${avatar({ presenter: w.presenter, photo: w.photo }, "lg")}
          <div>
            <p class="w-name">${esc(fullName(w))}</p>
            ${roleLine(w) ? `<p class="w-role">${esc(roleLine(w))}</p>` : ""}
            <p class="w-title"><a href="${link}">${esc(w.title)}</a></p>
            <p class="w-code">${esc(w.code || "")}${a.winner.note ? `, ${esc(a.winner.note)}` : ""}</p>
          </div>
        </div>
      </li>`;
    }).join("");
  }

  function renderMine() {
    if (!window.MRFA) return;
    const ids = MRFA.saved.all();
    const talks = ids.map((id) => talksById[id]).filter(Boolean).sort((a, b) => toMin(a.start) - toMin(b.start));
    const posters = ids.map((id) => postersById[id]).filter(Boolean);
    $("mine-list").innerHTML = [
      ...talks.map((t) => `<li class="mine-item"><span class="mine-time">${fmt(t.start)}</span>
        <div><a href="#talk-${esc(t.id)}" data-open="${esc(t.id)}">${esc(t.title)}</a><span class="mine-who">${esc(fullName(t))}, ${esc(t.code)}</span></div>
        ${MRFA.saveBtn(t.id)}</li>`),
      ...posters.map((p) => `<li class="mine-item"><span class="mine-time">Poster</span>
        <div><a href="${p.talk ? `abstract.html?talk=${esc(p.talk)}` : `abstract.html?poster=${esc(p.id)}`}">${esc(p.title)}</a><span class="mine-who">${esc(fullName(p))}, ${esc(p.code)}, poster session ${p.posterSession === 2 ? "II" : "I"}</span></div>
        ${MRFA.saveBtn(p.id)}</li>`),
    ].join("");
    $("mine-empty").hidden = ids.length > 0;
    $("mine-cal").hidden = talks.length === 0;
  }

  function makeQR(el, text) {
    el.innerHTML = "";
    if (!window.qrcode || !text) return;
    const qr = qrcode(0, "M"); qr.addData(text); qr.make();
    el.innerHTML = qr.createSvgTag({ cellSize: 4, margin: 0, scalable: true });
  }

  // Live "now / next", computed from the agenda so it works on every page.
  function liveState() {
    const n = nowInTZ();
    const isDay = !!preview || n.date === data.event.date;
    const min = preview ? toMin(preview) : n.min;
    const ag = (data.agenda || []).filter((a) => a.start && a.end);
    const cur = isDay ? ag.find((a) => min >= toMin(a.start) && min < toMin(a.end)) : null;
    const next = isDay ? ag.find((a) => toMin(a.start) > min) : null;
    let live = null, after = null;
    if (cur && cur.talks) {
      const ts = cur.talks.map((id) => talksById[id]).filter((t) => t && t.start);
      ts.forEach((t, i) => {
        const e = ts[i + 1] ? toMin(ts[i + 1].start) : toMin(cur.end);
        if (min >= toMin(t.start) && min < e) { live = t; after = ts[i + 1] || null; }
      });
    }
    return { n, isDay, min, cur, next, live, after, idx: (a) => (data.agenda || []).indexOf(a) };
  }

  function tick() {
    if (!data) return;
    const st = liveState();
    document.querySelectorAll(".slot").forEach((el) => {
      if (!el.dataset.start || !el.dataset.end) return;
      const isNow = st.isDay && st.min >= toMin(el.dataset.start) && st.min < toMin(el.dataset.end);
      el.classList.toggle("now", isNow);
      el.classList.toggle("past", st.isDay && st.min >= toMin(el.dataset.end));
      el.querySelector(".now-label").hidden = !isNow;
    });
    document.querySelectorAll(".talk").forEach((t) => t.classList.toggle("live", !!st.live && t.id === `talk-${st.live.id}`));
    // Event day: open the current block once (unless the visitor folded it).
    const curEl = st.cur && document.getElementById(`slot-${st.idx(st.cur)}`);
    if (curEl && curEl.classList.contains("foldable") && !curEl.dataset.touched && !curEl.dataset.auto) { setFold(curEl, false); curEl.dataset.auto = "1"; }
    const card = $("now-card");
    card.hidden = !st.isDay || (!st.cur && !st.next);
    if (!card.hidden) card.innerHTML = nowHTML(st);
    renderStrip(st);
    if (window.MRFARating) MRFARating.refresh();
  }

  const talkLink = (t) => `${onIndex ? "" : "./"}#talk-${esc(t.id)}`;
  function nowHTML(st) {
    const { cur, next, live, after } = st;
    const when = (a) => `${fmt(a.start)} – ${fmt(a.end)}`;
    const upNext = live && after ? `${fmt(after.start)} · ${esc(after.title)}, ${esc(fullName(after))}` : next ? `${fmt(next.start)} · ${esc(next.title)}` : "";
    if (!cur) return next ? `<p class="nc-kicker">Starting soon</p><p class="nc-next"><strong>${fmt(next.start)}</strong> ${esc(next.title)}</p>` : `<p class="nc-kicker">That’s a wrap</p><p class="nc-next">Thank you for joining MRFA Research Day.</p>`;
    return `
      <p class="nc-kicker"><span class="nc-dot" aria-hidden="true"></span>Happening now · ${esc(cur.title)} <span class="nc-when">${when(cur)}</span></p>
      ${live ? `<div class="nc-talk">${avatar(live, "md")}<div>
          <p class="nc-meta">${esc(live.format)} · ${esc(live.code)} · ${fmt(live.start)}</p>
          <a class="nc-title" href="${talkLink(live)}" data-open="${esc(live.id)}">${esc(live.title)}</a>
          <p class="nc-who">${esc(fullName(live))}${roleLine(live) ? ` · ${esc(roleLine(live))}` : ""}</p>
          <div class="nc-actions">${questionUrl(live) ? `<a class="btn" href="${esc(questionUrl(live))}" target="_blank" rel="noopener">Ask a question</a>` : ""}${window.MRFARating ? MRFARating.button(live, data.event) : ""}</div>
        </div></div>` : ""}
      ${upNext ? `<p class="nc-next"><strong>Up next</strong> ${upNext}</p>` : ""}`;
  }

  // Collapsed "Happening now" strip under the tabs, with the time (24 h) and date in Florida.
  function renderStrip(st) {
    const strip = document.getElementById("nowstrip");
    if (!strip) return;
    const [y, mo, d] = (preview ? data.event.date : st.n.date).split("-").map(Number);
    const months = ["January","February","March","April","May","June","July","August","September","October","November","December"];
    const hh = Math.floor(st.min / 60), mm = st.min % 60;
    $("ns-clock").textContent = `${String(hh).padStart(2, "0")}:${String(mm).padStart(2, "0")} · ${months[mo - 1]} ${d}, ${y}`;
    let label, text;
    if (st.isDay && st.cur) { label = "Happening now"; text = st.live ? `${shortName(st.live)}: ${st.live.title}` : st.cur.title; }
    else if (st.isDay && st.next) { label = "Up next"; text = `${fmt(st.next.start)} ${st.next.title}`; }
    else if (st.isDay) { label = "Research Day"; text = "That’s a wrap. Thank you for joining!"; }
    else {
      const days = Math.round((Date.UTC(...data.event.date.split("-").map((v, i) => i === 1 ? v - 1 : +v)) - Date.UTC(y, mo - 1, d)) / 864e5);
      label = "Research Day";
      text = days > 0 ? `Thursday, October 29 · in ${days} day${days === 1 ? "" : "s"}` : "Thank you for joining MRFA Research Day 2026";
    }
    strip.classList.toggle("is-live", st.isDay && !!st.cur);
    $("ns-label").textContent = label;
    $("ns-text").textContent = text;
    $("ns-body").innerHTML = st.isDay ? nowHTML(st) + (onIndex ? "" : `<p class="nc-next"><a href="./#program">Open the full program</a></p>`)
      : `<p class="nc-next">The live view starts on the day: the current session, the talk on stage with Ask and Rate buttons, and what’s up next. ${data.event.timeLabel ? `Program: ${esc(data.event.timeLabel)}, ` : ""}${esc(data.event.location || "Kinne Auditorium")}.</p>`;
  }

  // Expand/collapse a slot's rapid-fire talks, poster list or menu.
  document.addEventListener("change", (ev) => {
    const cb = ev.target.closest("[data-expand]");
    if (cb) $(cb.dataset.expand).classList.toggle("expanded", cb.checked);
  });
  // Arrow in a session header: show or hide all of that session's talks.
  document.addEventListener("click", (ev) => {
    let b = ev.target.closest("[data-fold]");
    if (!b) {
      const head = ev.target.closest(".foldable > .slot-head");
      if (!head || ev.target.closest("a, button, input, label")) return;
      b = head.querySelector("[data-fold]");
    }
    if (!b) return;
    const slot = $(b.dataset.fold);
    setFold(slot, !slot.classList.contains("folded"));
    slot.dataset.touched = "1";
  });
  // Opening index.html#talk-… (e.g. from the Speakers page) expands that talk.
  function openFromHash() {
    if (location.hash === "#awards") $("awards-fold").open = true;
    const m = location.hash.match(/^#talk-(.+)$/);
    if (!m) return;
    const d = document.getElementById("talk-" + m[1]);
    if (!d) return;
    unfold(d);
    d.open = true; d.scrollIntoView({ block: "center" });
  }
  function setFold(slot, folded) {
    slot.classList.toggle("folded", folded);
    const b = slot.querySelector("[data-fold]");
    if (b) { b.setAttribute("aria-expanded", String(!folded)); b.setAttribute("aria-label", b.getAttribute("aria-label").replace(/^(Show|Hide)/, folded ? "Show" : "Hide")); }
  }
  function unfold(d) { const slot = d.closest(".slot"); if (slot && slot.classList.contains("folded")) setFold(slot, false); }
  window.addEventListener("hashchange", openFromHash);
  document.addEventListener("click", (ev) => { if (ev.target.closest('a[href$="#awards"]')) $("awards-fold").open = true; });

  // Events
  document.addEventListener("click", (ev) => {
    const chip = ev.target.closest(".chip");
    if (chip) {
      setView(chip.dataset.f);
      if (!onIndex) history.replaceState(null, "", chip.dataset.f === "posters" ? "#posters" : location.pathname);
      if (window.MRFARating) MRFARating.refresh();
      return;
    }
    const qrBtn = ev.target.closest("[data-qr]");
    if (qrBtn) {
      const t = talksById[qrBtn.dataset.qr];
      $("qr-sub").innerHTML = `Then choose <strong>${esc(pickLabel(t))}</strong> in the form.`;
      makeQR($("qr-big"), questionUrl(t), 280);
      $("qr-dialog").showModal();
      return;
    }
    const sv = ev.target.closest("[data-save]");
    if (sv) { MRFA.saved.toggle(sv.dataset.save); renderMine(); return; }
    const ct = ev.target.closest("[data-cite]");
    if (ct) { MRFA.openCite(itemById(ct.dataset.cite)); return; }
    const cl = ev.target.closest("[data-cal]");
    if (cl) { const t = talksById[cl.dataset.cal]; MRFA.calendar.talks(data.event, [t], `${t.code}-${t.presenter.split(" ").pop()}.ics`); return; }
    if (ev.target.closest("#add-cal")) { MRFA.calendar.event(data.event); return; }
    if (ev.target.closest("#mine-cal")) {
      MRFA.calendar.talks(data.event, MRFA.saved.all().map((id) => talksById[id]).filter(Boolean), "My-MRFA-agenda.ics"); return;
    }
    const open = ev.target.closest("[data-open]");
    if (open && onIndex) {
      const d = document.getElementById("talk-" + open.dataset.open);
      if (d) { unfold(d); d.open = true; }
    }
  });
  $("poster-search").addEventListener("input", (e) => renderPosters(e.target.value));

  // Highlight the tab for the section in view
  const tabs = onIndex ? [...document.querySelectorAll(".tabs-inner > a")] : [];
  const io = new IntersectionObserver((entries) => {
    entries.forEach((en) => {
      if (en.isIntersecting) tabs.forEach((a) => a.setAttribute("aria-current", a.getAttribute("href") === "#" + en.target.id));
    });
  }, { rootMargin: "-40% 0px -55% 0px" });
  document.querySelectorAll("main section").forEach((s) => io.observe(s));
})();
