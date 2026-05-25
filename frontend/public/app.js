const API = "http://localhost:8000";

// ------------------------------------------------------------------ API HELPERS

async function apiFetch(path, opts = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const detail = err.detail;
    const msg = Array.isArray(detail)
      ? detail.map(d => `${d.loc?.at(-1) ?? "Feld"}: ${d.msg}`).join(" · ")
      : typeof detail === "string" ? detail : JSON.stringify(detail);
    throw new Error(msg || res.statusText);
  }
  if (res.status === 204) return null;
  return res.json();
}

const get  = (path)         => apiFetch(path);
const post = (path, body)   => apiFetch(path, { method: "POST",   body: JSON.stringify(body) });
const put  = (path, body)   => apiFetch(path, { method: "PUT",    body: JSON.stringify(body) });
const del  = (path)         => apiFetch(path, { method: "DELETE" });

// ------------------------------------------------------------------ TOAST

function toast(msg, type = "info") {
  const el = document.getElementById("toast");
  el.textContent = msg;
  el.className = `toast ${type}`;
  clearTimeout(el._t);
  el._t = setTimeout(() => { el.className = "toast hidden"; }, 3500);
}

// ------------------------------------------------------------------ MODAL

function openModal(html) {
  document.getElementById("modalCard").innerHTML = html;
  document.getElementById("modal").showModal();
}
function closeModal() { document.getElementById("modal").close(); }

// ------------------------------------------------------------------ ROUTER

const views = { dashboard, kurse, firmen, teilnehmer, angebote, rechnungen, ki };
const titles = { dashboard: "Dashboard", kurse: "Kurse", firmen: "Firmen", teilnehmer: "Teilnehmer", angebote: "Angebote", rechnungen: "Rechnungen", ki: "KI-Assistent" };

function navigate(view) {
  const name = view || "dashboard";
  document.querySelectorAll(".nav-item").forEach(el => el.classList.toggle("active", el.dataset.view === name));
  document.getElementById("topbarTitle").textContent = titles[name] || name;
  const content = document.getElementById("content");
  content.innerHTML = `<div class="loading">Lädt…</div>`;
  (views[name] || dashboard)(content);
}

window.addEventListener("hashchange", () => navigate(location.hash.slice(1)));

// ------------------------------------------------------------------ API STATUS

async function checkApi() {
  const dot  = document.getElementById("apiStatus");
  const text = document.getElementById("apiStatusText");
  try {
    await get("/health");
    dot.className = "status-dot online";
    text.textContent = "Backend online";
  } catch {
    dot.className = "status-dot offline";
    text.textContent = "Backend offline";
  }
}

// ------------------------------------------------------------------ BADGE HELPERS

function statusBadge(status) {
  const map = {
    offen: "badge-yellow", angenommen: "badge-green", abgelehnt: "badge-red",
    storniert: "badge-gray", bezahlt: "badge-green", "rückerstattet": "badge-blue",
  };
  return `<span class="badge ${map[status] || 'badge-gray'}">${status}</span>`;
}

function teilnehmerBadge(statusName) {
  const gruen = ["Angemeldet", "Teilgenommen", "Rechnung beglichen"];
  const rot   = ["Storniert"];
  const cls   = gruen.includes(statusName) ? "badge-green" : rot.includes(statusName) ? "badge-red" : "badge-yellow";
  return `<span class="badge ${cls}">${statusName || "–"}</span>`;
}

// ================================================================== VIEWS

// ------------------------------------------------------------------ DASHBOARD
async function dashboard(el) {
  try {
    const [kurseList, firmenList, teilnehmerList, rechnungenList] = await Promise.all([
      get("/kurse/"), get("/firmen/"), get("/teilnehmer/"), get("/rechnungen/"),
    ]);
    const offeneRechnungen = rechnungenList.filter(r => r.rechnung_status === "offen").length;
    el.innerHTML = `
      <div class="stat-grid">
        <div class="stat-card"><div class="num">${kurseList.length}</div><div class="label">Kurse</div></div>
        <div class="stat-card"><div class="num">${firmenList.length}</div><div class="label">Firmen</div></div>
        <div class="stat-card"><div class="num">${teilnehmerList.length}</div><div class="label">Teilnehmer</div></div>
        <div class="stat-card"><div class="num">${offeneRechnungen}</div><div class="label">Offene Rechnungen</div></div>
      </div>
      <div class="card">
        <h2>Nächste Kurse</h2>
        ${kurseList.length === 0 ? '<p class="empty">Noch keine Kurse angelegt.</p>' : `
        <div class="table-wrap">
          <table>
            <thead><tr><th>Name</th><th>Typ</th><th>Beginn</th><th>Ende</th></tr></thead>
            <tbody>
              ${kurseList.slice(0, 5).map(k => `<tr>
                <td>${k.kurs_name}</td>
                <td>${k.kurs_typ}</td>
                <td>${k.kurs_datum_beginn || "–"}</td>
                <td>${k.kurs_datum_ende || "–"}</td>
              </tr>`).join("")}
            </tbody>
          </table>
        </div>`}
      </div>`;
  } catch (e) {
    el.innerHTML = `<div class="card"><p class="empty">Backend nicht erreichbar: ${e.message}</p></div>`;
  }
}

// ------------------------------------------------------------------ KURSE
async function kurse(el) {
  let list = [];
  try { list = await get("/kurse/"); } catch (e) { el.innerHTML = `<p class="empty">${e.message}</p>`; return; }

  el.innerHTML = `
    <div class="section-header">
      <h2>Alle Kurse (${list.length})</h2>
      <button class="btn btn-primary" onclick="kurseCreateModal()">+ Neuer Kurs</button>
    </div>
    <div class="card">
      <div class="table-wrap">
        ${list.length === 0 ? '<p class="empty">Noch keine Kurse.</p>' : `
        <table>
          <thead><tr><th>ID</th><th>Name</th><th>Typ</th><th>Ort</th><th>Beginn</th><th>Ende</th><th></th></tr></thead>
          <tbody>
            ${list.map(k => `<tr>
              <td class="muted">#${k.kurs_id}</td>
              <td><strong>${k.kurs_name}</strong></td>
              <td>${k.kurs_typ}</td>
              <td>${k.kurs_ort || "–"}</td>
              <td>${k.kurs_datum_beginn || "–"}</td>
              <td>${k.kurs_datum_ende || "–"}</td>
              <td><button class="btn btn-sm" onclick="kursDetail(${k.kurs_id})">Detail</button></td>
            </tr>`).join("")}
          </tbody>
        </table>`}
      </div>
    </div>`;
}

window.kursDetail = async function(id) {
  try {
    const k = await get(`/kurse/${id}/detail`);
    const termine = (k.termine || []).map(t =>
      `<tr><td>${t.datum}</td><td>${t.uhrzeit_start} – ${t.uhrzeit_ende}</td></tr>`
    ).join("") || "<tr><td colspan='2' class='muted'>Keine Termine</td></tr>";
    openModal(`
      <header><h3>${k.kurs_name}</h3><button class="icon-btn" onclick="closeModal()">✕</button></header>
      <p><span class="badge badge-blue">${k.kurs_typ}</span> · ${k.kurs_ort}</p>
      <p class="muted">${k.kurs_datum_beginn} → ${k.kurs_datum_ende} · ${k.kurs_tage} Tag(e)</p>
      ${k.kommentar ? `<p>${k.kommentar}</p>` : ""}
      <h3 style="font-size:.9rem;margin-top:.5rem">Termine</h3>
      <table><thead><tr><th>Datum</th><th>Uhrzeit</th></tr></thead><tbody>${termine}</tbody></table>
    `);
  } catch(e) { toast(e.message, "error"); }
};

window.kurseCreateModal = function() {
  openModal(`
    <header><h3>Neuer Kurs</h3><button class="icon-btn" onclick="closeModal()">✕</button></header>
    <form id="kursForm" class="form-grid">
      <div class="form-row">
        <label>Kursname<input name="kurs_name" required /></label>
        <label>Typ<select name="kurs_typ"><option>Webinar</option><option>Präsenz</option></select></label>
      </div>
      <label>Ort<input name="kurs_ort" value="online (MS Teams)" /></label>
      <div class="form-row">
        <label>Beginn<input type="date" name="kurs_datum_beginn" required /></label>
        <label>Ende<input type="date" name="kurs_datum_ende" required /></label>
      </div>
      <div class="form-row">
        <label>Zeitraum<input name="kurs_zeitraum" placeholder="z.B. 09:00–17:00" required /></label>
        <label>Tage<input type="number" name="kurs_tage" value="1" min="1" required /></label>
      </div>
      <label>Kommentar<textarea name="kommentar"></textarea></label>
      <div class="btn-row">
        <button type="submit" class="btn btn-primary">Speichern</button>
        <button type="button" class="btn" onclick="closeModal()">Abbrechen</button>
      </div>
    </form>
  `);
  document.getElementById("kursForm").addEventListener("submit", async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    const datum_beginn = fd.get("kurs_datum_beginn");
    const datum_ende   = fd.get("kurs_datum_ende");
    try {
      await post("/kurse/komplett/", {
        kurs_name: fd.get("kurs_name"), kurs_typ: fd.get("kurs_typ"),
        kurs_ort: fd.get("kurs_ort"), kurs_datum_beginn: datum_beginn,
        kurs_datum_ende: datum_ende, kurs_zeitraum: fd.get("kurs_zeitraum"),
        kurs_tage: Number(fd.get("kurs_tage")), kommentar: fd.get("kommentar"),
        termine: [{ datum: datum_beginn, start: `${datum_beginn} 09:00:00`, ende: `${datum_beginn} 17:00:00` }],
      });
      closeModal(); toast("Kurs angelegt", "success"); navigate("kurse");
    } catch(err) { toast(err.message, "error"); }
  });
};

// ------------------------------------------------------------------ FIRMEN
async function firmen(el) {
  let list = [];
  try { list = await get("/firmen/"); } catch (e) { el.innerHTML = `<p class="empty">${e.message}</p>`; return; }

  el.innerHTML = `
    <div class="section-header">
      <h2>Alle Firmen (${list.length})</h2>
      <button class="btn btn-primary" onclick="firmenCreateModal()">+ Neue Firma</button>
    </div>
    <div class="card">
      <div class="table-wrap">
        ${list.length === 0 ? '<p class="empty">Noch keine Firmen.</p>' : `
        <table>
          <thead><tr><th>ID</th><th>Name</th><th>Rechnungs-E-Mail</th><th>Adresse</th></tr></thead>
          <tbody>
            ${list.map(f => `<tr>
              <td class="muted">#${f.firma_id}</td>
              <td><strong>${f.firma_name}</strong></td>
              <td>${f.email_rechnungsversand}</td>
              <td class="muted">${f.rechnungsadresse?.slice(0, 40) || "–"}</td>
            </tr>`).join("")}
          </tbody>
        </table>`}
      </div>
    </div>`;
}

window.firmenCreateModal = function() {
  openModal(`
    <header><h3>Neue Firma</h3><button class="icon-btn" onclick="closeModal()">✕</button></header>
    <form id="firmaForm" class="form-grid">
      <label>Firmenname<input name="firma_name" required /></label>
      <label>Rechnungsadresse<textarea name="rechnungsadresse" required></textarea></label>
      <label>Rechnungs-E-Mail<input type="email" name="email_rechnungsversand" required /></label>
      <label>Kommentar<textarea name="kommentar"></textarea></label>
      <fieldset style="border:1px solid var(--line);border-radius:10px;padding:.75rem">
        <legend style="font-weight:700;font-size:.85rem;padding:0 .4rem">Ansprechpartner</legend>
        <div class="form-grid" style="margin-top:.5rem">
          <div class="form-row">
            <label>Vorname<input name="ap_vorname" required /></label>
            <label>Nachname<input name="ap_nachname" required /></label>
          </div>
          <label>E-Mail<input type="email" name="ap_email" required /></label>
          <div class="form-row">
            <label>Telefon<input name="ap_telefon" /></label>
            <label>Position<input name="ap_position" /></label>
          </div>
        </div>
      </fieldset>
      <div class="btn-row">
        <button type="submit" class="btn btn-primary">Speichern</button>
        <button type="button" class="btn" onclick="closeModal()">Abbrechen</button>
      </div>
    </form>
  `);
  document.getElementById("firmaForm").addEventListener("submit", async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await post("/firmen/komplett/", Object.fromEntries(fd));
      closeModal(); toast("Firma angelegt", "success"); navigate("firmen");
    } catch(err) { toast(err.message, "error"); }
  });
};

// ------------------------------------------------------------------ TEILNEHMER
async function teilnehmer(el) {
  let list = [], statusList = [];
  try {
    [list, statusList] = await Promise.all([get("/teilnehmer/"), get("/teilnehmer-status/")]);
  } catch (e) { el.innerHTML = `<p class="empty">${e.message}</p>`; return; }

  const statusMap = Object.fromEntries(statusList.map(s => [s.status_id, s.status_name]));

  el.innerHTML = `
    <div class="section-header">
      <h2>Alle Teilnehmer (${list.length})</h2>
      <button class="btn btn-primary" onclick="teilnehmerCreateModal()">+ Neuer Teilnehmer</button>
    </div>
    <div class="card">
      <div class="table-wrap">
        ${list.length === 0 ? '<p class="empty">Noch keine Teilnehmer.</p>' : `
        <table>
          <thead><tr><th>ID</th><th>Name</th><th>E-Mail</th><th>Status</th><th></th></tr></thead>
          <tbody>
            ${list.map(t => `<tr>
              <td class="muted">#${t.teilnehmerid}</td>
              <td><strong>${t.vorname} ${t.nachname}</strong></td>
              <td>${t.email}</td>
              <td>${teilnehmerBadge(statusMap[t.status_id])}</td>
              <td><button class="btn btn-sm" onclick="teilnehmerStatusModal(${t.teilnehmerid}, '${t.vorname} ${t.nachname}')">Status</button></td>
            </tr>`).join("")}
          </tbody>
        </table>`}
      </div>
    </div>`;

  window._statusList = statusList;
}

window.teilnehmerCreateModal = async function() {
  let firmenList = [];
  try { firmenList = await get("/firmen/"); } catch {}
  openModal(`
    <header><h3>Neuer Teilnehmer</h3><button class="icon-btn" onclick="closeModal()">✕</button></header>
    <form id="teilnehmerForm" class="form-grid">
      <label>Firma
        <select name="firma_id" required>
          ${firmenList.map(f => `<option value="${f.firma_id}">${f.firma_name}</option>`).join("")}
        </select>
      </label>
      <div class="form-row">
        <label>Vorname<input name="vorname" required /></label>
        <label>Nachname<input name="nachname" required /></label>
      </div>
      <label>E-Mail<input type="email" name="email" required /></label>
      <div class="btn-row">
        <button type="submit" class="btn btn-primary">Speichern</button>
        <button type="button" class="btn" onclick="closeModal()">Abbrechen</button>
      </div>
    </form>
  `);
  document.getElementById("teilnehmerForm").addEventListener("submit", async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await post("/teilnehmer/", { firma_id: Number(fd.get("firma_id")), vorname: fd.get("vorname"), nachname: fd.get("nachname"), email: fd.get("email") });
      closeModal(); toast("Teilnehmer angelegt", "success"); navigate("teilnehmer");
    } catch(err) { toast(err.message, "error"); }
  });
};

window.teilnehmerStatusModal = function(id, name) {
  const statusList = window._statusList || [];
  openModal(`
    <header><h3>Status: ${name}</h3><button class="icon-btn" onclick="closeModal()">✕</button></header>
    <div class="form-grid">
      <label>Neuer Status
        <select id="newStatus">
          ${statusList.map(s => `<option value="${s.status_id}">${s.status_name ?? "–"}</option>`).join("")}
        </select>
      </label>
      <div class="btn-row">
        <button class="btn btn-primary" onclick="saveTeilnehmerStatus(${id})">Speichern</button>
        <button class="btn" onclick="closeModal()">Abbrechen</button>
      </div>
    </div>
  `);
};

window.saveTeilnehmerStatus = async function(id) {
  const status_id = Number(document.getElementById("newStatus").value);
  try {
    await put(`/teilnehmer/${id}/status`, { status_id });
    closeModal(); toast("Status aktualisiert", "success"); navigate("teilnehmer");
  } catch(err) { toast(err.message, "error"); }
};

// ------------------------------------------------------------------ ANGEBOTE
async function angebote(el) {
  let list = [];
  try { list = await get("/angebote/"); } catch (e) { el.innerHTML = `<p class="empty">${e.message}</p>`; return; }

  el.innerHTML = `
    <div class="section-header">
      <h2>Alle Angebote (${list.length})</h2>
      <button class="btn btn-primary" onclick="angebotCreateModal()">+ Neues Angebot</button>
    </div>
    <div class="card">
      <div class="table-wrap">
        ${list.length === 0 ? '<p class="empty">Noch keine Angebote.</p>' : `
        <table>
          <thead><tr><th>ID</th><th>Firma</th><th>Kurs</th><th>Betrag</th><th>Status</th><th></th></tr></thead>
          <tbody>
            ${list.map(a => `<tr>
              <td class="muted">#${a.angebot_id}</td>
              <td>#${a.firma_id}</td>
              <td>#${a.kurs_id}</td>
              <td>${Number(a.angebot_betrag).toFixed(2)} €</td>
              <td>${statusBadge(a.angebot_status)}</td>
              <td class="gap-1">
                ${a.angebot_status === "offen" ? `
                  <button class="btn btn-sm btn-success" onclick="updateAngebotStatus(${a.angebot_id},'angenommen')">✓</button>
                  <button class="btn btn-sm btn-danger"  onclick="updateAngebotStatus(${a.angebot_id},'abgelehnt')">✗</button>
                ` : ""}
              </td>
            </tr>`).join("")}
          </tbody>
        </table>`}
      </div>
    </div>`;
}

window.updateAngebotStatus = async function(id, status) {
  try {
    const res = await put(`/angebote/${id}/status`, { status });
    const msg = status === "angenommen" && res.rechnungsnummer
      ? `Angebot angenommen · Rechnung #${res.rechnungsnummer} erstellt`
      : `Status: ${status}`;
    toast(msg, "success"); navigate("angebote");
  } catch(err) { toast(err.message, "error"); }
};

window.angebotCreateModal = async function() {
  let firmenList = [], kurseList = [];
  try { [firmenList, kurseList] = await Promise.all([get("/firmen/"), get("/kurse/")]); } catch {}
  openModal(`
    <header><h3>Neues Angebot</h3><button class="icon-btn" onclick="closeModal()">✕</button></header>
    <form id="angebotForm" class="form-grid">
      <label>Firma
        <select name="firma_id" required>
          ${firmenList.map(f => `<option value="${f.firma_id}">${f.firma_name}</option>`).join("")}
        </select>
      </label>
      <label>Kurs
        <select name="kurs_id" required>
          ${kurseList.map(k => `<option value="${k.kurs_id}">${k.kurs_name}</option>`).join("")}
        </select>
      </label>
      <label>Betrag (netto €)<input type="number" name="angebot_betrag" step="0.01" min="0" required /></label>
      <div class="btn-row">
        <button type="submit" class="btn btn-primary">Speichern</button>
        <button type="button" class="btn" onclick="closeModal()">Abbrechen</button>
      </div>
    </form>
  `);
  document.getElementById("angebotForm").addEventListener("submit", async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await post("/angebote/", { firma_id: Number(fd.get("firma_id")), kurs_id: Number(fd.get("kurs_id")), angebot_betrag: Number(fd.get("angebot_betrag")) });
      closeModal(); toast("Angebot erstellt", "success"); navigate("angebote");
    } catch(err) { toast(err.message, "error"); }
  });
};

// ------------------------------------------------------------------ RECHNUNGEN
async function rechnungen(el) {
  let list = [];
  try { list = await get("/rechnungen/"); } catch (e) { el.innerHTML = `<p class="empty">${e.message}</p>`; return; }

  el.innerHTML = `
    <div class="section-header">
      <h2>Alle Rechnungen (${list.length})</h2>
    </div>
    <div class="card">
      <div class="table-wrap">
        ${list.length === 0 ? '<p class="empty">Noch keine Rechnungen.</p>' : `
        <table>
          <thead><tr><th>Nr.</th><th>Firma</th><th>Betrag</th><th>Zahltermin</th><th>Status</th><th></th></tr></thead>
          <tbody>
            ${list.map(r => `<tr>
              <td class="muted">#${r.rechnungsnummer}</td>
              <td>#${r.firma_id}</td>
              <td>${Number(r.betrag_brutto).toFixed(2)} €</td>
              <td>${r.zahltermin || "–"}</td>
              <td>${statusBadge(r.rechnung_status)}</td>
              <td>
                ${r.rechnung_status === "offen" ? `<button class="btn btn-sm btn-success" onclick="zahlungModal(${r.rechnungsnummer}, ${r.betrag_brutto})">Zahlung</button>` : ""}
              </td>
            </tr>`).join("")}
          </tbody>
        </table>`}
      </div>
    </div>`;
}

window.zahlungModal = function(nr, betrag) {
  openModal(`
    <header><h3>Zahlung erfassen · Rechnung #${nr}</h3><button class="icon-btn" onclick="closeModal()">✕</button></header>
    <form id="zahlungForm" class="form-grid">
      <label>Betrag (€)<input type="number" name="betrag" value="${betrag}" step="0.01" min="0.01" required /></label>
      <label>Zahlungsmethode
        <select name="zahlungsmethode">
          <option>Überweisung</option>
          <option>Kreditkarte</option>
          <option>PayPal</option>
        </select>
      </label>
      <div class="btn-row">
        <button type="submit" class="btn btn-primary">Speichern</button>
        <button type="button" class="btn" onclick="closeModal()">Abbrechen</button>
      </div>
    </form>
  `);
  document.getElementById("zahlungForm").addEventListener("submit", async e => {
    e.preventDefault();
    const fd = new FormData(e.target);
    try {
      await post(`/rechnungen/${nr}/zahlung/`, { betrag: Number(fd.get("betrag")), zahlungsmethode: fd.get("zahlungsmethode") });
      closeModal(); toast("Zahlung erfasst", "success"); navigate("rechnungen");
    } catch(err) { toast(err.message, "error"); }
  });
};

// ------------------------------------------------------------------ KI-ASSISTENT
async function ki(el) {
  el.innerHTML = `
    <div class="card">
      <h2>Angebotstext generieren</h2>
      <form id="kiAngebotForm" class="form-grid">
        <div class="form-row">
          <label>Firmenname<input name="firma_name" placeholder="Musterfirma GmbH" /></label>
          <label>Kursname<input name="kurs_name" placeholder="Python Grundlagen" /></label>
        </div>
        <div class="form-row">
          <label>Typ<select name="kurs_typ"><option>Webinar</option><option>Präsenz</option></select></label>
          <label>Betrag (€)<input type="number" name="betrag" value="1500" step="0.01" /></label>
        </div>
        <div class="form-row">
          <label>Beginn<input type="date" name="kurs_datum_beginn" /></label>
          <label>Ende<input type="date" name="kurs_datum_ende" /></label>
        </div>
        <button type="submit" class="btn btn-primary" style="justify-self:start">Text generieren</button>
      </form>
      <div id="kiAngebotOut" class="ki-output" style="margin-top:1rem;display:none"></div>
    </div>

    <div class="card">
      <h2>Kursbeschreibung generieren</h2>
      <form id="kiKursForm" class="form-grid">
        <div class="form-row">
          <label>Kursname<input name="kurs_name" placeholder="Excel für Fortgeschrittene" /></label>
          <label>Typ<select name="kurs_typ"><option>Webinar</option><option>Präsenz</option></select></label>
        </div>
        <div class="form-row">
          <label>Tage<input type="number" name="kurs_tage" value="2" min="1" /></label>
          <label>Themen/Stichworte<input name="themen" placeholder="Pivot, Makros, Diagramme" /></label>
        </div>
        <button type="submit" class="btn btn-primary" style="justify-self:start">Beschreibung generieren</button>
      </form>
      <div id="kiKursOut" class="ki-output" style="margin-top:1rem;display:none"></div>
    </div>

    <div class="card">
      <h2>Mahnungs-E-Mail generieren</h2>
      <form id="kiMahnungForm" class="form-grid">
        <div class="form-row">
          <label>Firmenname<input name="firma_name" placeholder="Musterfirma GmbH" /></label>
          <label>Rechnungsnummer<input type="number" name="rechnungsnummer" placeholder="42" /></label>
        </div>
        <div class="form-row">
          <label>Offener Betrag (€)<input type="number" name="betrag" placeholder="1500" step="0.01" /></label>
          <label>Zahltermin<input type="date" name="zahltermin" /></label>
        </div>
        <label>Mahnstufe
          <select name="mahnstufe"><option value="1">1 – Erinnerung</option><option value="2">2 – Mahnung</option><option value="3">3 – Letzte Mahnung</option></select>
        </label>
        <button type="submit" class="btn btn-primary" style="justify-self:start">E-Mail generieren</button>
      </form>
      <div id="kiMahnungOut" class="ki-output" style="margin-top:1rem;display:none"></div>
    </div>`;

  async function kiSubmit(formId, outId, path, buildBody) {
    document.getElementById(formId).addEventListener("submit", async e => {
      e.preventDefault();
      const fd = new FormData(e.target);
      const out = document.getElementById(outId);
      out.style.display = "block";
      out.textContent = "Generiere…";
      try {
        const res = await post(path, buildBody(fd));
        out.textContent = res.text;
      } catch(err) {
        out.textContent = `Fehler: ${err.message}`;
      }
    });
  }

  kiSubmit("kiAngebotForm", "kiAngebotOut", "/ollama/angebot-text", fd => ({
    firma_name: fd.get("firma_name"), kurs_name: fd.get("kurs_name"),
    kurs_typ: fd.get("kurs_typ"), betrag: Number(fd.get("betrag")),
    kurs_datum_beginn: fd.get("kurs_datum_beginn"), kurs_datum_ende: fd.get("kurs_datum_ende"),
  }));

  kiSubmit("kiKursForm", "kiKursOut", "/ollama/kurs-beschreibung", fd => ({
    kurs_name: fd.get("kurs_name"), kurs_typ: fd.get("kurs_typ"),
    kurs_tage: Number(fd.get("kurs_tage")), themen_stichworte: fd.get("themen"),
  }));

  kiSubmit("kiMahnungForm", "kiMahnungOut", "/ollama/mahnung", fd => ({
    firma_name: fd.get("firma_name"), rechnungsnummer: Number(fd.get("rechnungsnummer")),
    betrag: Number(fd.get("betrag")), zahltermin: fd.get("zahltermin"),
    mahnstufe: Number(fd.get("mahnstufe")),
  }));
}

// ------------------------------------------------------------------ INIT

document.getElementById("menuBtn").addEventListener("click", () => {
  document.getElementById("sidebar").classList.toggle("open");
});

document.querySelectorAll(".nav-item").forEach(el => {
  el.addEventListener("click", () => {
    document.getElementById("sidebar").classList.remove("open");
  });
});

checkApi();
setInterval(checkApi, 30000);
navigate(location.hash.slice(1) || "dashboard");
