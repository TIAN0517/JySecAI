(function () {
    'use strict';

    const state = {
        catalog: null,
        operation: 'passive_discovery',
        timer: null,
        detailRunId: '',
        runStatus: {},
        announced: {},
    };
    const terminalStatuses = new Set(['completed', 'failed', 'cancelled']);
    const operationLabels = {
        passive_discovery: '审查',
        active_scan: '扫描',
        exploit_validation: '利用验证',
    };
    const statusLabels = {
        awaiting_approval: '待审批', queued: '排队中', dispatching: '下发中', running: '运行中',
        paused: '已暂停', completed: '已完成', failed: '失败', cancelled: '已取消', budget_paused: '额度暂停',
    };

    function el(id) { return document.getElementById(id); }
    function esc(value) {
        return String(value == null ? '' : value)
            .replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;')
            .replaceAll('"', '&quot;').replaceAll("'", '&#039;');
    }
    function lines(value) {
        return String(value || '').split(/\r?\n/u).map((item) => item.trim()).filter(Boolean);
    }
    function currentPageIsSecurityOps() {
        return window.location.hash.replace(/^#/, '').split('?')[0] === 'security-ops';
    }
    function tr(key, fallback) {
        if (typeof window.t !== 'function') return fallback;
        const value = window.t(key);
        return !value || value === key ? fallback : value;
    }
    function notify(message, type) {
        if (typeof window.showToast === 'function') window.showToast(message, type || 'info');
        else if (type === 'error') console.error(message);
    }

    async function request(path, options) {
        const response = await window.apiFetch(path, options || {});
        const payload = await response.json().catch(() => ({}));
        if (!response.ok) {
            const error = payload && payload.error;
            const message = payload && typeof payload.message === 'string' ? payload.message : '';
            const reason = message || (typeof error === 'string' ? error : (error && error.message) || `HTTP ${response.status}`);
            const details = (error && error.details && error.details.reasons) || (payload && payload.details && payload.details.reasons);
            throw new Error(Array.isArray(details) && details.length ? `${reason}: ${details.join('; ')}` : reason);
        }
        return payload;
    }

    function activeEnginesForOperation() {
        const engines = state.catalog && Array.isArray(state.catalog.engines) ? state.catalog.engines : [];
        return engines.filter((engine) => engine.active && Array.isArray(engine.supportedOperations)
            && engine.supportedOperations.includes(state.operation));
    }

    function renderEngineOptions() {
        const select = el('security-ops-engine');
        if (!select) return;
        const previous = select.value;
        const engines = activeEnginesForOperation();
        select.innerHTML = engines.length
            ? engines.map((engine) => `<option value="${esc(engine.id)}">${esc(engine.name)}</option>`).join('')
            : '<option value="">当前没有可用引擎</option>';
        if (engines.some((engine) => engine.id === previous)) select.value = previous;
        select.disabled = engines.length === 0;
        syncEngine();
    }

    function syncEngine() {
        const engineId = el('security-ops-engine') ? el('security-ops-engine').value : '';
        const engines = state.catalog && state.catalog.engines ? state.catalog.engines : [];
        const engine = engines.find((item) => item.id === engineId);
        const profile = el('security-ops-profile');
        const submit = el('security-ops-submit');
        const hint = el('security-ops-engine-hint');
        const profiles = engine && Array.isArray(engine.profiles) ? engine.profiles : [];
        if (profile) {
            profile.innerHTML = profiles.map((item) => `<option value="${esc(item)}">${esc(item)}</option>`).join('');
            if (state.operation === 'passive_discovery' && profiles.includes('audit')) profile.value = 'audit';
        }
        if (hint) hint.textContent = engine ? `${engine.description} · ${engine.connector}` : '请先配置支持该模式的扫描引擎';
        if (submit) submit.disabled = !engine;
    }

    function selectMode(operation) {
        if (!Object.prototype.hasOwnProperty.call(operationLabels, operation)) return;
        state.operation = operation;
        document.querySelectorAll('.security-ops-mode').forEach((button) => {
            button.classList.toggle('active', button.dataset.operation === operation);
        });
        const warning = el('security-ops-mode-warning');
        if (warning) warning.hidden = operation !== 'exploit_validation';
        const submit = el('security-ops-submit');
        if (submit) submit.textContent = `创建${operationLabels[operation]}任务`;
        renderEngineOptions();
    }

    async function loadCatalog() {
        const health = el('security-ops-health');
        try {
            state.catalog = await request('/api/security-ops/catalog');
            const ready = (state.catalog.engines || []).filter((engine) => engine.active).length;
            if (health) {
                health.textContent = state.catalog.note || `控制面在线 · ${ready} 个引擎可用`;
                health.classList.toggle('online', ready > 0);
            }
            renderEngineOptions();
        } catch (error) {
            if (health) {
                health.textContent = '控制面离线';
                health.classList.remove('online');
            }
            const select = el('security-ops-engine');
            if (select) select.innerHTML = '<option value="">控制面不可用</option>';
            throw error;
        }
    }

    function renderRuns(runs) {
        const host = el('security-ops-runs');
        const count = el('security-ops-run-count');
        if (!host) return;
        if (count) count.textContent = `${runs.length} 条`;
        if (!runs.length) {
            host.innerHTML = '<div class="security-ops-empty">暂无运行记录</div>';
            return;
        }
        const canWrite = typeof window.hasPermission !== 'function' || window.hasPermission('tasks:write');
        const canApprove = typeof window.hasPermission !== 'function' || window.hasPermission('hitl:write');
        runs.forEach((run) => {
            const previous = state.runStatus[run.id];
            if (previous && previous !== 'completed' && run.status === 'completed' && !state.announced[run.id]) {
                state.announced[run.id] = true;
                notify(tr('securityOps.reportReady', '扫描已完成，渗透报告已可下载'), 'success');
            }
            state.runStatus[run.id] = run.status;
        });
        host.innerHTML = runs.map((run) => {
            const approve = run.status === 'awaiting_approval' && canApprove
                ? `<button type="button" class="btn-primary btn-small" data-security-approve="${esc(run.id)}">批准</button>` : '';
            const cancel = !terminalStatuses.has(run.status) && canWrite
                ? `<button type="button" class="btn-secondary btn-small" data-security-cancel="${esc(run.id)}">取消</button>` : '';
            return `<article class="security-ops-run">
                <div class="security-ops-run-main">
                    <div class="security-ops-run-title"><strong>${esc(run.objective)}</strong><span class="security-ops-status status-${esc(run.status)}">${esc(statusLabels[run.status] || run.status)}</span></div>
                    <div class="security-ops-run-meta"><span>${esc(run.engine)} / ${esc(run.profile)}</span><span>${esc((run.targets || []).join(', '))}</span>${run.currentPhase ? `<span>P${esc(run.currentPhase)}</span>` : ''}${run.vulnCount ? `<span>${esc(run.vulnCount)}</span>` : ''}<span>${esc(new Date(run.createdAt).toLocaleString())}</span></div>
                    ${run.statusReason ? `<div class="security-ops-run-reason">${esc(run.statusReason)}</div>` : ''}
                </div>
                <div class="security-ops-run-actions"><button type="button" class="btn-secondary btn-small" data-security-report="${esc(run.projectId || '')}" data-security-run="${esc(run.id)}">${esc(tr('securityOps.downloadReport', '下载渗透报告'))}</button><button type="button" class="btn-secondary btn-small" data-security-detail="${esc(run.id)}">详情</button>${approve}${cancel}</div>
            </article>`;
        }).join('');
        host.querySelectorAll('[data-security-report]').forEach((button) => button.addEventListener('click', () => downloadReport(button.dataset.securityReport, button.dataset.securityRun)));
        host.querySelectorAll('[data-security-detail]').forEach((button) => button.addEventListener('click', () => openDetail(button.dataset.securityDetail)));
        host.querySelectorAll('[data-security-approve]').forEach((button) => button.addEventListener('click', () => approveRun(button.dataset.securityApprove)));
        host.querySelectorAll('[data-security-cancel]').forEach((button) => button.addEventListener('click', () => cancelRun(button.dataset.securityCancel)));
    }

    async function loadRuns(silent) {
        const projectId = (el('security-ops-project-filter') || {}).value || '';
        const query = new URLSearchParams({ limit: '50' });
        if (projectId.trim()) query.set('projectId', projectId.trim());
        try {
            const payload = await request(`/api/security-ops/runs?${query.toString()}`);
            const items = Array.isArray(payload.items) ? payload.items : [];
            renderRuns(items);
            const projectId = (el('security-ops-project-filter') || {}).value || '';
            if (projectId.trim()) await refreshReportBadge(projectId.trim());
        } catch (error) {
            const host = el('security-ops-runs');
            if (host) host.innerHTML = `<div class="security-ops-empty error">${esc(error.message)}</div>`;
            if (!silent) notify(error.message, 'error');
        }
    }

    async function submitRun(event) {
        event.preventDefault();
        const form = event.currentTarget;
        if (!form.reportValidity()) return;
        if (state.operation === 'exploit_validation' && !window.confirm('确认创建“利用验证”任务？创建后仍需审批人员批准才会执行。')) return;
        const values = new FormData(form);
        const now = new Date();
        const validDays = Number(values.get('validDays'));
        const payload = {
            projectId: String(values.get('projectId')).trim(),
            engine: String(values.get('engine')),
            profile: String(values.get('profile')),
            targets: lines(values.get('targets')),
            objective: String(values.get('objective')).trim(),
            authorization: {
                id: String(values.get('authorizationId')).trim(),
                projectId: String(values.get('projectId')).trim(),
                tenantId: 'bound-by-server',
                targetPatterns: lines(values.get('patterns')),
                operations: [state.operation],
                validFrom: now.toISOString(),
                validUntil: new Date(now.getTime() + validDays * 86400000).toISOString(),
                approvedBy: String(values.get('approvedBy')).trim(),
                attested: values.get('attested') === 'on',
            },
            config: { autoValidate: state.operation === 'exploit_validation' },
            idempotencyKey: window.crypto && crypto.randomUUID ? crypto.randomUUID() : `run-${Date.now()}-${Math.random().toString(16).slice(2)}`,
        };
        const button = el('security-ops-submit');
        if (button) button.disabled = true;
        try {
            const result = await request('/api/security-ops/runs', {
                method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload),
            });
            notify(`任务已创建：${result.run && result.run.id ? result.run.id : '等待审批'}`, 'success');
            if (el('security-ops-project-filter')) el('security-ops-project-filter').value = payload.projectId;
            await loadRuns(true);
        } catch (error) {
            notify(error.message, 'error');
        } finally {
            if (button) button.disabled = false;
        }
    }

    async function approveRun(runId) {
        if (!window.confirm('确认批准此任务进入执行队列？')) return;
        try {
            await request(`/api/security-ops/runs/${encodeURIComponent(runId)}/approve`, { method: 'POST' });
            notify('任务已批准', 'success');
            await loadRuns(true);
        } catch (error) { notify(error.message, 'error'); }
    }

    async function cancelRun(runId) {
        if (!window.confirm('确认取消此任务？')) return;
        try {
            await request(`/api/security-ops/runs/${encodeURIComponent(runId)}/cancel`, { method: 'POST' });
            notify('任务已取消', 'success');
            await loadRuns(true);
        } catch (error) { notify(error.message, 'error'); }
    }

    function renderTimeline(host, items, kind) {
        if (!host) return;
        host.innerHTML = items.length ? items.map((item) => {
            const title = kind === 'event' ? `#${item.sequence || '-'} ${item.type || 'event'}` : `${item.kind || 'artifact'} · ${item.sizeBytes || 0} bytes`;
            const time = item.at || item.createdAt;
            const data = kind === 'event' ? item.data : { objectKey: item.objectKey, sha256: item.sha256 };
            const download = item.downloadPath ? `<button type="button" data-auth-download="${esc(item.downloadPath)}">${item.kind === 'pentest_report' ? esc(tr('securityOps.downloadReport', '下载渗透报告')) : 'PDF'}</button>` : '';
            return `<article><time>${esc(time ? new Date(time).toLocaleString() : '')}</time><strong>${esc(title)}</strong>${download}<pre>${esc(JSON.stringify(data || {}, null, 2))}</pre></article>`;
        }).join('') : '<div class="security-ops-empty">暂无数据</div>';
        host.querySelectorAll('[data-auth-download]').forEach((button) => {
            button.addEventListener('click', () => {
                const path = button.getAttribute('data-auth-download');
                if (!path || typeof downloadAuthenticated !== 'function') return;
                downloadAuthenticated(path, 'pentest-report.html').catch((error) => notify(error.message, 'error'));
            });
        });
    }

    async function openDetail(runId) {
        state.detailRunId = runId;
        const section = el('security-ops-detail');
        if (section) section.hidden = false;
        if (el('security-ops-detail-id')) el('security-ops-detail-id').textContent = runId;
        if (el('security-ops-events')) el('security-ops-events').innerHTML = '<div class="loading-spinner">加载中…</div>';
        if (el('security-ops-artifacts')) el('security-ops-artifacts').innerHTML = '<div class="loading-spinner">加载中…</div>';
        try {
            const [eventPayload, artifactPayload] = await Promise.all([
                request(`/api/security-ops/runs/${encodeURIComponent(runId)}/events?after=0&limit=500`),
                request(`/api/security-ops/runs/${encodeURIComponent(runId)}/artifacts?limit=200`),
            ]);
            renderTimeline(el('security-ops-events'), eventPayload.events || [], 'event');
            renderTimeline(el('security-ops-artifacts'), artifactPayload.artifacts || [], 'artifact');
            if (section) section.scrollIntoView({ behavior: 'smooth', block: 'start' });
        } catch (error) { notify(error.message, 'error'); }
    }

    function closeDetail() {
        state.detailRunId = '';
        if (el('security-ops-detail')) el('security-ops-detail').hidden = true;
    }

    async function loadFindings() {
        const projectId = ((el('security-ops-project-filter') || {}).value || '').trim();
        if (!projectId) {
            notify('请先输入项目 ID', 'warning');
            return;
        }
        try {
            const payload = await request(`/api/security-ops/projects/${encodeURIComponent(projectId)}/findings?limit=200`);
            const findings = payload.findings || [];
            if (el('security-ops-finding-count')) el('security-ops-finding-count').textContent = `${findings.length} 条`;
            const host = el('security-ops-findings');
            if (host) host.innerHTML = findings.length ? findings.map((finding) => `<article class="security-ops-finding">
                <span class="security-ops-severity severity-${esc(finding.severity)}">${esc(finding.severity)}</span>
                <div><strong>${esc(finding.title)}</strong><p>${esc(finding.description || finding.status || '')}</p></div>
                <span>${Math.round(Number(finding.confidence || 0) * 100)}%</span>
            </article>`).join('') : '<div class="security-ops-empty">该项目暂无发现</div>';
        } catch (error) { notify(error.message, 'error'); }
    }

    async function refresh() {
        try {
            if (!state.catalog) await loadCatalog();
            await loadRuns(false);
            if (state.detailRunId) await openDetail(state.detailRunId);
        } catch (error) { notify(error.message, 'error'); }
    }

    function downloadReport(projectId, runId) {
        const id = String(projectId || (el('security-ops-project-filter') || {}).value || '').trim();
        if (!id) {
            notify(tr('securityOps.needProject', '请先填写项目 ID'), 'warning');
            return;
        }
        const query = runId ? `?runId=${encodeURIComponent(runId)}` : '';
        downloadAuthenticated(`/api/projects/${encodeURIComponent(id)}/pentest-report${query}`, 'pentest-report.html')
            .catch((error) => notify(error.message, 'error'));
    }

    async function refreshReportBadge(projectId) {
        const badge = el('security-ops-report-badge');
        if (!badge || !projectId) return;
        try {
            const meta = await request(`/api/projects/${encodeURIComponent(projectId)}/pentest-report?format=meta`);
            badge.textContent = meta.qualified ? tr('securityOps.qualified', '报告合格') : tr('securityOps.draft', '报告草稿');
            badge.title = Array.isArray(meta.gaps) ? meta.gaps.join('\n') : '';
        } catch (error) {
            badge.textContent = '';
        }
    }

    async function init() {
        selectMode(state.operation);
        await refresh();
        if (!state.timer) {
            state.timer = window.setInterval(() => {
                if (currentPageIsSecurityOps() && !document.hidden) loadRuns(true);
            }, 6000);
        }
    }

    window.initSecurityOpsPage = init;
    window.refreshSecurityOps = refresh;
    window.refreshSecurityOpsRuns = () => loadRuns(false);
    window.refreshSecurityOpsFindings = loadFindings;
    window.selectSecurityOpsMode = selectMode;
    window.syncSecurityOpsEngine = syncEngine;
    window.submitSecurityOpsRun = submitRun;
    window.downloadSecurityOpsPentestReport = () => downloadReport('', '');
    window.closeSecurityOpsDetail = closeDetail;
}());
