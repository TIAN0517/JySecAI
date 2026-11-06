(function () {
    'use strict';

    let pollTimer = null;
    let activeProject = '';

    function tr(key, fallback) {
        if (typeof window.t !== 'function') return fallback;
        const value = window.t(key);
        return !value || value === key ? fallback : value;
    }
    function toast(message, type) {
        if (typeof showToast === 'function') showToast(message, type || 'info');
    }
    function $(id) { return document.getElementById(id); }
    function lines(value) {
        return String(value || '').split(/\r?\n/u).map((item) => item.trim()).filter(Boolean);
    }
    function esc(value) {
        return String(value || '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    }

    window.initReconPage = function initReconPage() {
        const form = $('recon-scan-form');
        if (form && !form.dataset.bound) {
            form.dataset.bound = '1';
            form.addEventListener('submit', startRecon);
        }
        const report = $('recon-report-btn');
        if (report && !report.dataset.bound) {
            report.dataset.bound = '1';
            report.addEventListener('click', downloadReconReport);
        }
        if (activeProject) refreshRecon(activeProject);
    };

    async function startRecon(event) {
        event.preventDefault();
        const projectId = ($('recon-project').value || '').trim();
        const targetLines = lines($('recon-target') && $('recon-target').value);
        const patterns = lines($('recon-patterns') && $('recon-patterns').value);
        const days = Number($('recon-days').value || 7);
        const now = new Date();
        const payload = {
            projectId: projectId,
            engine: 'xalgorix',
            profile: 'audit',
            targets: targetLines,
            objective: tr('reconPage.objective', '授权范围内的资产侦察与暴露面审查'),
            authorization: {
                id: ($('recon-auth').value || '').trim(),
                projectId: projectId,
                targetPatterns: patterns,
                operations: ['passive_discovery'],
                validFrom: now.toISOString(),
                validUntil: new Date(now.getTime() + days * 86400000).toISOString(),
                approvedBy: ($('recon-approver').value || '').trim(),
                attested: $('recon-attested').checked,
            },
            idempotencyKey: window.crypto && crypto.randomUUID ? crypto.randomUUID() : `recon-${Date.now()}`,
        };
        try {
            const res = await window.apiFetch('/api/security-ops/runs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
            });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                toast((data && data.message) || (data && data.error) || tr('reconPage.failed', '侦察启动失败'), 'error');
                return;
            }
            activeProject = projectId;
            toast(tr('reconPage.started', '审查任务已建立，批准后才会执行'), 'success');
            await refreshRecon(projectId);
            if (pollTimer) clearInterval(pollTimer);
            pollTimer = setInterval(() => refreshRecon(projectId), 4000);
        } catch (err) {
            toast(tr('reconPage.failed', '侦察启动失败'), 'error');
        }
    }

    async function refreshRecon(projectId) {
        const box = $('recon-result');
        const status = $('recon-status');
        if (!box) return;
        const res = await window.apiFetch('/api/security-ops/runs?limit=30&projectId=' + encodeURIComponent(projectId));
        const data = await res.json().catch(() => ({}));
        const runs = (data.items || []).filter((run) => run.operation === 'passive_discovery' || !run.operation);
        if (status) status.textContent = runs.length ? tr('reconPage.tracking', '正在跟踪任务') : tr('reconPage.idle', '尚未启动');
        const terminal = runs.length && runs.every((run) => ['completed', 'failed', 'cancelled'].includes(run.status));
        if (terminal && pollTimer) {
            clearInterval(pollTimer);
            pollTimer = null;
            toast(tr('reconPage.reportReady', '侦察状态已更新，可下载渗透报告'), 'success');
        }
        box.innerHTML = '<table class="data-table"><thead><tr><th>' + esc(tr('reconPage.colStatus', '状态')) + '</th><th>' + esc(tr('reconPage.colTarget', '目标')) + '</th><th>' + esc(tr('reconPage.colWhen', '时间')) + '</th></tr></thead><tbody>' +
            (runs.map((run) => '<tr><td>' + esc(run.status || '') + '</td><td>' + esc((run.targets || []).join(', ')) + '</td><td>' + esc(run.createdAt ? new Date(run.createdAt).toLocaleString() : '') + '</td></tr>').join('') || '<tr><td colspan="3">' + esc(tr('reconPage.empty', '尚无审查任务')) + '</td></tr>') +
            '</tbody></table>';
    }

    function downloadReconReport() {
        const projectId = (($('recon-project') && $('recon-project').value) || activeProject || '').trim();
        if (!projectId) {
            toast(tr('reconPage.needProject', '请先填写项目 ID'), 'error');
            return;
        }
        downloadAuthenticated('/api/projects/' + encodeURIComponent(projectId) + '/pentest-report', 'pentest-report.html')
            .catch((error) => toast(error && error.message ? error.message : tr('reconPage.reportFailed', '无法下载渗透报告'), 'error'));
    }
})();
