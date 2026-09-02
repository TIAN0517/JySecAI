const state = {
  catalog: null,
  usage: null,
  billing: null,
  runs: [],
  detailRunId: null,
};

const $ = (selector) => document.querySelector(selector);
const terminalStatuses = new Set(["completed", "failed", "cancelled"]);

function currentIdentity() {
  return {
    tenantId: localStorage.getItem("jysec.tenant") || "dev-tenant",
    userId: localStorage.getItem("jysec.user") || "dev-owner",
    accessToken: sessionStorage.getItem("jysec.accessToken") || "",
  };
}

function requestHeaders() {
  const identity = currentIdentity();
  if (identity.accessToken) {
    return { "content-type": "application/json", authorization: `Bearer ${identity.accessToken}` };
  }
  return {
    "content-type": "application/json",
    "x-jysec-tenant": identity.tenantId,
    "x-jysec-user": identity.userId,
    "x-jysec-roles": "owner,admin,security_operator,security_approver",
  };
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { ...requestHeaders(), ...(options.headers || {}) },
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) setTimeout(() => openConnectionDialog(), 0);
    const message = payload?.error?.message || `HTTP ${response.status}`;
    const details = payload?.error?.details?.reasons;
    throw new Error(Array.isArray(details) ? `${message}: ${details.join("; ")}` : message);
  }
  return payload;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function errorText(error) {
  return error instanceof Error ? error.message : String(error);
}

function toast(message) {
  const element = $("#toast");
  element.textContent = message;
  element.classList.add("show");
  setTimeout(() => element.classList.remove("show"), 3200);
}

function renderEngines(catalog) {
  const palette = ["#35ddff", "#8d5cff", "#4de8a2", "#ffcb68"];
  $("#engine-grid").innerHTML = catalog.engines
    .map(
      (engine, index) => `
        <article class="engine-card" style="--accent:${palette[index % palette.length]}">
          <header><h3>${escapeHtml(engine.name)}</h3><i class="engine-state"></i></header>
          <p>${escapeHtml(engine.description)}</p>
          <footer>
            <span class="chip">${escapeHtml(engine.category)}</span>
            <span class="chip">${escapeHtml(engine.maturity)}</span>
            <span class="chip">${escapeHtml(engine.connector)}</span>
          </footer>
        </article>`,
    )
    .join("");
  $("#engine-value").textContent = String(catalog.engines.filter((engine) => engine.active).length);
  $("#engine-select").innerHTML = catalog.engines
    .filter((engine) => engine.active)
    .map((engine) => `<option value="${escapeHtml(engine.id)}">${escapeHtml(engine.name)}</option>`)
    .join("");
}

function renderRuns(runs) {
  state.runs = runs;
  $("#active-value").textContent = String(runs.filter((run) => !terminalStatuses.has(run.status)).length);
  if (!runs.length) {
    $("#run-list").innerHTML = '<p class="empty">尚未建立任務。所有已授權測試會在這裡同步。</p>';
    return;
  }
  $("#run-list").innerHTML = runs
    .map((run) => {
      const approve = run.status === "awaiting_approval"
        ? `<button class="run-action" data-approve="${escapeHtml(run.id)}">核准</button>`
        : "";
      const cancel = !terminalStatuses.has(run.status)
        ? `<button class="run-action" data-cancel="${escapeHtml(run.id)}">取消</button>`
        : "";
      return `
        <article class="run-item">
          <header>
            <h3 title="${escapeHtml(run.objective)}">${escapeHtml(run.objective)}</h3>
            <div class="run-actions">
              <button class="run-action" data-events="${escapeHtml(run.id)}">軌跡</button>
              ${approve}${cancel}
              <span class="status status-${escapeHtml(run.status)}">${escapeHtml(run.status)}</span>
            </div>
          </header>
          <p>${escapeHtml(run.engine)} · ${escapeHtml(run.profile)} · ${escapeHtml(run.targets.join(", "))}</p>
          <footer><span>${new Date(run.createdAt).toLocaleString("zh-TW")}</span><span>${run.reservedCredits} credits</span></footer>
        </article>`;
    })
    .join("");

  document.querySelectorAll("[data-approve]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await api(`/v1/runs/${encodeURIComponent(button.dataset.approve)}/approve`, { method: "POST" });
        toast("任務已核准並進入受管佇列");
        await refreshOperations();
      } catch (error) {
        toast(errorText(error));
      }
    });
  });
  document.querySelectorAll("[data-cancel]").forEach((button) => {
    button.addEventListener("click", async () => {
      try {
        await api(`/v1/runs/${encodeURIComponent(button.dataset.cancel)}/cancel`, { method: "POST" });
        toast("取消要求已送出並寫入稽核軌跡");
        await refreshOperations();
      } catch (error) {
        toast(errorText(error));
      }
    });
  });
  document.querySelectorAll("[data-events]").forEach((button) => {
    button.addEventListener("click", () => openRunDetail(button.dataset.events));
  });
}

function renderFindings(findings) {
  $("#finding-count").textContent = `${findings.length} findings`;
  if (!findings.length) {
    $("#finding-list").innerHTML = '<p class="empty">尚無已驗證發現；引擎輸出必須符合統一證據契約才會列入。</p>';
    return;
  }
  $("#finding-list").innerHTML = findings
    .map(
      (finding) => `
        <article class="finding-item">
          <span class="finding-severity finding-severity-${escapeHtml(finding.severity)}">${escapeHtml(finding.severity)}</span>
          <div class="finding-copy">
            <strong title="${escapeHtml(finding.title)}">${escapeHtml(finding.title)}</strong>
            <small>${escapeHtml(finding.projectId)} · ${escapeHtml(finding.engine)} · ${escapeHtml(finding.status)} · ${finding.evidenceRefs.length} evidence refs</small>
          </div>
          <span class="finding-confidence">${Math.round(Number(finding.confidence) * 100)}% confidence</span>
        </article>`,
    )
    .join("");
}

function renderPlans() {
  if (!state.catalog || !state.usage) return;
  const selfService = new Set(state.billing?.selfServicePlans || []);
  $("#plan-grid").innerHTML = state.catalog.plans
    .map((plan) => {
      const current = plan.id === state.usage.plan.id;
      const canCheckout = Boolean(state.billing?.enabled && selfService.has(plan.id) && !current);
      const action = current
        ? '<button class="button button-ghost" type="button" disabled>目前方案</button>'
        : canCheckout
          ? `<button class="button button-primary" type="button" data-checkout="${escapeHtml(plan.id)}">升級此方案</button>`
          : '<button class="button button-ghost" type="button" disabled>洽 Jy 技術團隊</button>';
      return `
        <article class="plan-card${current ? " current" : ""}">
          <h3>${escapeHtml(plan.displayName)}</h3>
          <p>${plan.monthlyCredits.toLocaleString()} credits／月 · ${plan.maxConcurrentRuns} 並發 · ${plan.auditRetentionDays} 天稽核保存</p>
          ${action}
        </article>`;
    })
    .join("");
  $("#billing-notice").textContent = state.billing?.enabled
    ? "Stripe Checkout 已啟用。方案價格由 Stripe Dashboard 的 Price ID 控制。"
    : "尚未配置 Stripe 金鑰與 Price ID；平台功能正常，但自助付款按鈕暫停。";
  document.querySelectorAll("[data-checkout]").forEach((button) => {
    button.addEventListener("click", () => beginCheckout(button.dataset.checkout));
  });
}

async function loadCatalog() {
  const catalog = await api("/v1/catalog");
  state.catalog = catalog;
  renderEngines(catalog);
  renderPlans();
}

async function loadUsage() {
  const usage = await api("/v1/usage");
  state.usage = usage;
  $("#plan-badge").textContent = usage.plan.displayName;
  $("#usage-value").textContent = `${usage.usedCredits.toLocaleString()} / ${usage.plan.monthlyCredits.toLocaleString()}`;
  $("#usage-caption").textContent = `${usage.period} · ${usage.plan.maxConcurrentRuns} 個並發額度`;
  renderPlans();
}

async function loadBilling() {
  state.billing = await api("/v1/billing/status");
  renderPlans();
}

async function loadRuns() {
  const page = await api("/v1/runs?limit=50");
  renderRuns(page.items);
}

async function loadFindings() {
  const projects = [...new Set(state.runs.map((run) => run.projectId))];
  if (!projects.length) {
    renderFindings([]);
    return;
  }
  const responses = await Promise.all(
    projects.map((projectId) => api(`/v1/projects/${encodeURIComponent(projectId)}/findings?limit=100`)),
  );
  const findings = responses
    .flatMap((response) => response.findings || [])
    .sort((left, right) => String(right.createdAt).localeCompare(String(left.createdAt)))
    .slice(0, 200);
  renderFindings(findings);
}

async function refreshOperations() {
  await Promise.all([loadRuns(), loadUsage()]);
  await loadFindings();
  if (state.detailRunId && $("#run-detail-dialog").open) await loadRunDetail(state.detailRunId);
}

function lines(value) {
  return value.split(/\r?\n/u).map((item) => item.trim()).filter(Boolean);
}

async function submitRun(form) {
  const values = new FormData(form);
  const now = new Date();
  const validUntil = new Date(now.getTime() + Number(values.get("validDays")) * 86_400_000);
  const engine = String(values.get("engine"));
  const operation = state.catalog.engines.find((item) => item.id === engine)?.requiredOperation || "active_scan";
  const payload = {
    projectId: String(values.get("projectId")),
    engine,
    profile: String(values.get("profile")),
    targets: lines(String(values.get("targets"))),
    objective: String(values.get("objective")),
    authorization: {
      id: String(values.get("authorizationId")),
      projectId: String(values.get("projectId")),
      tenantId: currentIdentity().tenantId,
      targetPatterns: lines(String(values.get("patterns"))),
      operations: [operation],
      validFrom: now.toISOString(),
      validUntil: validUntil.toISOString(),
      approvedBy: String(values.get("approvedBy")),
      attested: true,
    },
    config: {},
    idempotencyKey: crypto.randomUUID(),
  };
  return api("/v1/runs", { method: "POST", body: JSON.stringify(payload) });
}

function openConnectionDialog() {
  const identity = currentIdentity();
  const form = $("#connection-form");
  form.elements.accessToken.value = identity.accessToken;
  form.elements.tenantId.value = identity.tenantId;
  form.elements.userId.value = identity.userId;
  const dialog = $("#connection-dialog");
  if (!dialog.open) dialog.showModal();
}

async function beginCheckout(planId) {
  try {
    const result = await api("/v1/billing/checkout", {
      method: "POST",
      body: JSON.stringify({ planId }),
    });
    window.location.assign(result.url);
  } catch (error) {
    toast(errorText(error));
  }
}

async function openBillingPortal() {
  try {
    const result = await api("/v1/billing/portal", { method: "POST" });
    window.location.assign(result.url);
  } catch (error) {
    toast(errorText(error));
  }
}

async function loadRunDetail(runId) {
  const [eventResult, artifactResult] = await Promise.all([
    api(`/v1/runs/${encodeURIComponent(runId)}/events?after=0&limit=1000`),
    api(`/v1/runs/${encodeURIComponent(runId)}/artifacts?limit=200`),
  ]);
  const events = eventResult.events || [];
  const artifacts = artifactResult.artifacts || [];
  $("#event-list").innerHTML = [
    ...events.map(
      (event) => `
        <article class="event-item">
          <time>${new Date(event.at).toLocaleString("zh-TW")}</time>
          <div><strong>#${event.sequence} ${escapeHtml(event.type)}</strong><pre>${escapeHtml(JSON.stringify(event.data, null, 2))}</pre></div>
        </article>`,
    ),
    ...artifacts.map(
      (artifact) => `
        <article class="event-item">
          <time>${new Date(artifact.createdAt).toLocaleString("zh-TW")}</time>
          <div><strong>artifact ${escapeHtml(artifact.kind)}</strong><pre>${escapeHtml(`${artifact.objectKey}\nsha256:${artifact.sha256}\n${artifact.sizeBytes} bytes · encrypted`)}</pre></div>
        </article>`,
    ),
  ].join("") || '<p class="empty">尚無事件。</p>';
}

async function openRunDetail(runId) {
  state.detailRunId = runId;
  const run = state.runs.find((item) => item.id === runId);
  $("#run-detail-title").textContent = run ? `${run.engine} · ${run.status}` : "任務稽核軌跡";
  $("#event-list").innerHTML = '<p class="loading">正在讀取事件…</p>';
  $("#run-detail-dialog").showModal();
  try {
    await loadRunDetail(runId);
  } catch (error) {
    $("#event-list").innerHTML = `<p class="empty">${escapeHtml(errorText(error))}</p>`;
  }
}

function bindUI() {
  const runDialog = $("#run-dialog");
  $("#new-run-button").addEventListener("click", () => runDialog.showModal());
  $("#close-dialog").addEventListener("click", () => runDialog.close());
  $("#cancel-dialog").addEventListener("click", () => runDialog.close());
  $("#refresh-button").addEventListener("click", () => refreshOperations().catch((error) => toast(errorText(error))));
  $("#connection-button").addEventListener("click", openConnectionDialog);
  $("#billing-button").addEventListener("click", () => {
    renderPlans();
    $("#billing-dialog").showModal();
  });
  $("#billing-portal-button").addEventListener("click", openBillingPortal);
  document.querySelectorAll("[data-dialog-close]").forEach((button) => {
    button.addEventListener("click", () => document.getElementById(button.dataset.dialogClose)?.close());
  });
  $("#connection-form").addEventListener("submit", (event) => {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    const token = String(values.get("accessToken") || "").trim();
    if (token) sessionStorage.setItem("jysec.accessToken", token);
    else sessionStorage.removeItem("jysec.accessToken");
    localStorage.setItem("jysec.tenant", String(values.get("tenantId") || "dev-tenant").trim());
    localStorage.setItem("jysec.user", String(values.get("userId") || "dev-owner").trim());
    $("#connection-dialog").close();
    void bootstrapData();
  });
  $("#clear-session-button").addEventListener("click", () => {
    sessionStorage.removeItem("jysec.accessToken");
    toast("目前分頁的正式登入已清除");
    openConnectionDialog();
  });
  $("#run-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const errorElement = $("#form-error");
    errorElement.textContent = "";
    try {
      const result = await submitRun(event.currentTarget);
      runDialog.close();
      event.currentTarget.reset();
      toast(result.run.status === "awaiting_approval" ? "任務已建立，等待人工核准" : "任務已排入佇列");
      await refreshOperations();
    } catch (error) {
      errorElement.textContent = errorText(error);
    }
  });
}

async function bootstrapData() {
  try {
    await Promise.all([loadCatalog(), loadUsage(), loadBilling()]);
    await loadRuns();
    await loadFindings();
    $("#health-text").textContent = "Control plane synchronized";
  } catch (error) {
    $("#health-text").textContent = "Control plane unavailable";
    toast(errorText(error));
  }
}

function bootstrap() {
  bindUI();
  void bootstrapData();
  setInterval(() => refreshOperations().catch(() => {}), 5000);
}

bootstrap();
