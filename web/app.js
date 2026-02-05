const API_BASE = "https://apweb-zhfm.onrender.com";

const PROFILES = {
  1: { pin: "3221", user: "p1", pass: "p1pass" },
  2: { pin: "6969", user: "p2", pass: "p2pass" },
  3: { pin: "2626", user: "p3", pass: "p3pass" },
  4: { pin: "3859", user: "p4", pass: "p4pass" },
};

const state = {
  profile: null,
  token: null,
  view: "login",
  items: [],
  summary: {},
  currentItem: null,
  detail: null,
  rankingsMode: "mine",
  rankings: null,
};

const app = document.getElementById("app");

function saveToken(profile, token) {
  localStorage.setItem(`token_p${profile}`, token);
}

function loadToken(profile) {
  return localStorage.getItem(`token_p${profile}`);
}

function setAuth(profile, token) {
  state.profile = profile;
  state.token = token;
  if (token) saveToken(profile, token);
}

function toast(msg) {
  const el = document.createElement("div");
  el.className = "card hint";
  el.textContent = msg;
  app.prepend(el);
  setTimeout(() => el.remove(), 2500);
}

async function api(path, opts = {}) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 10000);
  const headers = opts.headers || {};
  headers["Content-Type"] = "application/json";
  if (state.token) headers["Authorization"] = `Bearer ${state.token}`;

  try {
    const res = await fetch(`${API_BASE}${path}`, { ...opts, headers, signal: controller.signal });
    clearTimeout(timeout);

    if (res.status === 401) throw { status: 401 };
    if (res.status === 403) {
      const data = await res.json().catch(() => ({}));
      throw { status: 403, detail: data.detail || "Forbidden" };
    }
    if (!res.ok) {
      const data = await res.json().catch(() => ({}));
      throw { status: res.status, detail: data.detail || "Error" };
    }
    if (res.status === 204) return {};
    return await res.json();
  } catch (err) {
    clearTimeout(timeout);
    if (err.name === "AbortError") throw { status: 0, detail: "timeout" };
    throw err;
  }
}

function renderLogin() {
  state.view = "login";
  app.innerHTML = `
    <div class="header"><h1>Perfil</h1></div>
    <div class="card">
      <div class="grid">
        <button class="btn block" data-profile="1">1</button>
        <button class="btn block" data-profile="2">2</button>
        <button class="btn block" data-profile="3">3</button>
        <button class="btn block" data-profile="4">4</button>
      </div>
    </div>
    <div id="pinBox" class="card hidden">
      <div class="small">PIN (numérico)</div>
      <input id="pinInput" class="input" type="password" inputmode="numeric" />
      <div class="row">
        <button id="pinCancel" class="btn secondary">Cancelar</button>
        <button id="pinOk" class="btn">Entrar</button>
      </div>
    </div>
  `;

  const pinBox = document.getElementById("pinBox");
  let selectedProfile = null;

  app.querySelectorAll("[data-profile]").forEach(btn => {
    btn.addEventListener("click", () => {
      selectedProfile = parseInt(btn.dataset.profile, 10);
      pinBox.classList.remove("hidden");
      document.getElementById("pinInput").focus();
    });
  });

  document.getElementById("pinCancel").onclick = () => {
    pinBox.classList.add("hidden");
    document.getElementById("pinInput").value = "";
  };

  document.getElementById("pinOk").onclick = async () => {
    const pin = document.getElementById("pinInput").value.trim();
    if (!selectedProfile) return;
    if (pin !== PROFILES[selectedProfile].pin) {
      toast("PIN incorrecto");
      return;
    }
    const existing = loadToken(selectedProfile);
    if (existing) {
      setAuth(selectedProfile, existing);
      await renderItems();
      return;
    }
    try {
      const res = await api("/auth/pin", {
        method: "POST",
        body: JSON.stringify({ profile: String(selectedProfile), pin }),
      });
      setAuth(selectedProfile, res.access_token);
      await renderItems();
    } catch (e) {
      if (e.status === 0) toast("Servidor no disponible");
      else toast(e.detail || "Error de login");
    }
  };
}

async function renderItems() {
  state.view = "items";
  app.innerHTML = `
    <div class="header">
      <h1>Items</h1>
      <div class="footer-actions">
        <button id="goSummary" class="btn secondary">Resumen</button>
        <button id="logout" class="btn secondary">Salir</button>
      </div>
    </div>
    <div class="card">
      <div class="row">
        <input id="newCode" class="input" placeholder="Código" />
        <input id="newName" class="input" placeholder="Nombre (opcional)" />
      </div>
      <button id="createItem" class="btn">Crear item</button>
    </div>
    <div id="itemsList" class="list"></div>
  `;

  document.getElementById("logout").onclick = () => {
    state.token = null;
    state.profile = null;
    renderLogin();
  };

  document.getElementById("goSummary").onclick = () => renderRankings();

  document.getElementById("createItem").onclick = async () => {
    const code = document.getElementById("newCode").value.trim();
    const name = document.getElementById("newName").value.trim();
    if (!code) return toast("Código requerido");
    try {
      const res = await api("/items", { method: "POST", body: JSON.stringify({ code, name }) });
      await renderDetail(res.id);
    } catch (e) {
      if (e.status === 401) return handle401();
      if (e.status === 0) return toast("Servidor no disponible");
      toast(e.detail || "Error al crear");
    }
  };

  try {
    const [items, summary] = await Promise.all([
      api("/items"),
      api("/items/summary?range=all").catch(() => []),
    ]);
    state.items = items || [];
    state.summary = {};
    (summary || []).forEach(r => (state.summary[r.id] = r));
    renderItemsList();
  } catch (e) {
    if (e.status === 401) return handle401();
    toast("Servidor no disponible");
  }
}

function renderItemsList() {
  const list = document.getElementById("itemsList");
  list.innerHTML = "";
  if (!state.items.length) {
    list.innerHTML = `<div class="notice">No hay items</div>`;
    return;
  }
  state.items.forEach(it => {
    const sum = state.summary[it.id] || {};
    const val = sum.my_best_total;
    const total = typeof val === "number" ? val.toFixed(1) : "—";
    const row = document.createElement("div");
    row.className = "list-item";
    row.innerHTML = `
      <div class="code">${it.code}</div>
      <div class="value">${total}</div>
    `;
    row.onclick = () => renderDetail(it.id);
    list.appendChild(row);
  });
}

async function renderDetail(itemId) {
  state.view = "detail";
  app.innerHTML = `
    <div class="header">
      <h1>Detalle</h1>
      <div class="footer-actions">
        <button id="backItems" class="btn secondary">Volver</button>
      </div>
    </div>
    <div id="detailBox" class="card"></div>
  `;
  document.getElementById("backItems").onclick = () => renderItems();

  try {
    const data = await api(`/items/${itemId}/detail`);
    state.detail = data;
    renderDetailContent(data);
  } catch (e) {
    if (e.status === 401) return handle401();
    toast(e.status === 0 ? "Servidor no disponible" : (e.detail || "Error"));
  }
}

function renderDetailContent(data) {
  const box = document.getElementById("detailBox");
  const item = data.item || {};
  const canView = data.can_view_others;
  const rows = data.ratings_by_profile || [];

  const listRows = rows.map(r => {
    if (!canView || !r.rating) return `P${r.profile} | —`;
    const v = r.rating;
    return `P${r.profile} | Total ${v.total} | A ${v.a} B ${v.b} C ${v.c} D ${v.d} N ${v.n}`;
  });

  box.innerHTML = `
    <div class="header"><h1>${item.code || "Item"}</h1></div>
    <div class="card hint">
      <div class="small">Puntuaciones (1-4)</div>
      ${!canView ? `<div class="notice">Puntúa para ver a los demás</div>` : ""}
      <div class="list">
        ${listRows.map(t => `<div class="small">${t}</div>`).join("")}
      </div>
    </div>

    <div class="card">
      <div class="small">Mi puntuación</div>
      ${ratingControlsHTML(data.my_rating)}
      <button id="saveRating" class="btn block">${data.my_rating ? "Modificar mi puntuación" : "Puntuar ahora"}</button>
    </div>
  `;

  bindRatingControls(data.my_rating);
  document.getElementById("saveRating").onclick = () => saveRating(item.id);
}

function ratingControlsHTML(prefill) {
  const a = prefill ? prefill.a : 0;
  const b = prefill ? prefill.b : 0;
  const c = prefill ? prefill.c : 0;
  const d = prefill ? prefill.d : 0;
  const n = prefill ? prefill.n : 0;
  return `
    ${sliderRow("A", "a", a)}
    ${sliderRow("B", "b", b)}
    ${sliderRow("C", "c", c)}
    ${sliderRow("D", "d", d)}
    ${sliderRow("N", "n", n, 0, 2)}
  `;
}

function sliderRow(label, key, value, min = 0, max = 10) {
  return `
    <div class="slider-row">
      <label>${label}</label>
      <input id="s_${key}" type="range" min="${min}" max="${max}" value="${value}" step="1" />
      <span id="v_${key}">${value}</span>
    </div>
  `;
}

function bindRatingControls(prefill) {
  ["a", "b", "c", "d", "n"].forEach(k => {
    const s = document.getElementById(`s_${k}`);
    const v = document.getElementById(`v_${k}`);
    if (!s) return;
    v.textContent = s.value;
    s.oninput = () => (v.textContent = s.value);
  });
}

async function saveRating(itemId) {
  const a = parseInt(document.getElementById("s_a").value, 10);
  const b = parseInt(document.getElementById("s_b").value, 10);
  const c = parseInt(document.getElementById("s_c").value, 10);
  const d = parseInt(document.getElementById("s_d").value, 10);
  const n = parseInt(document.getElementById("s_n").value, 10);
  try {
    await api(`/items/${itemId}/ratings`, {
      method: "POST",
      body: JSON.stringify({ a, b, c, d, n }),
    });
    toast("Guardado");
    await renderDetail(itemId);
  } catch (e) {
    if (e.status === 401) return handle401();
    if (e.detail === "COOLDOWN_RATING_5MIN") return toast("Espera 5 minutos para modificar esta puntuación");
    toast(e.status === 0 ? "Servidor no disponible" : (e.detail || "Error"));
  }
}

async function renderRankings() {
  state.view = "rankings";
  app.innerHTML = `
    <div class="header">
      <h1>Resumen</h1>
      <div class="footer-actions">
        <button id="backItems" class="btn secondary">Volver</button>
      </div>
    </div>
    <div class="tabs">
      <div class="tab" data-mode="mine">Míos</div>
      <div class="tab" data-mode="global">Global</div>
    </div>
    <div id="rankingsBody"></div>
  `;
  document.getElementById("backItems").onclick = () => renderItems();

  app.querySelectorAll(".tab").forEach(tab => {
    tab.onclick = () => {
      state.rankingsMode = tab.dataset.mode;
      renderRankings();
    };
    if (tab.dataset.mode === state.rankingsMode) tab.classList.add("active");
  });

  try {
    const data = await api(`/rankings?mode=${state.rankingsMode}`);
    state.rankings = data;
    renderRankingsBody();
  } catch (e) {
    if (e.status === 401) return handle401();
    toast(e.status === 0 ? "Servidor no disponible" : (e.detail || "Error"));
  }
}

function renderRankingsBody() {
  const body = document.getElementById("rankingsBody");
  const data = state.rankings || {};
  const metrics = ["total", "a", "b", "c", "d", "n"];
  body.innerHTML = metrics
    .map(m => renderRankingSection(m, data[m] || []))
    .join("");

  body.querySelectorAll("[data-item]").forEach(el => {
    el.onclick = () => renderDetail(el.dataset.item);
  });
}

function renderRankingSection(metric, list) {
  const title = metric.toUpperCase();
  const rows = list.length
    ? list.map((r, i) => `
        <div class="list-item" data-item="${r.item_id}">
          <div class="code">#${i + 1} ${r.code}</div>
          <div class="value">${r.value.toFixed(1)}</div>
        </div>
      `).join("")
    : `<div class="notice">Sin datos</div>`;

  return `
    <div class="card">
      <div class="small">Top ${title}</div>
      <div class="list">${rows}</div>
    </div>
  `;
}

function handle401() {
  toast("Sesión caducada");
  renderLogin();
}

renderLogin();
