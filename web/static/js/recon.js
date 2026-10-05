(function () {
    'use strict';

    let pollTimer = null;
    let lastRunId = '';

    function toast(message, type) {
        if (typeof showToast === 'function') showToast(message, type || 'info');
    }

    function reconFetch(url, options) {
        const opts = Object.assign({ credentials: 'include' }, options || {});
        opts.headers = Object.assign({ 'Content-Type': 'application/json' }, opts.headers || {});
        return fetch(url, opts);
    }

    function $(id) { return document.getElementById(id); }

    window.initReconPage = function initReconPage() {
        const startBtn = $('recon-start-btn');
        const autoBtn = $('recon-auto-btn');
        const cancelBtn = $('recon-cancel-btn');
        if (startBtn && !startBtn.dataset.bound) {
            startBtn.dataset.bound = '1';
            startBtn.addEventListener('click', () => startRecon('quick'));
        }
        if (autoBtn && !autoBtn.dataset.bound) {
            autoBtn.dataset.bound = '1';
            autoBtn.addEventListener('click', () => startRecon('auto'));
        }
        if (cancelBtn && !cancelBtn.dataset.bound) {
            cancelBtn.dataset.bound = '1';
            cancelBtn.addEventListener('click', cancelRecon);
        }
        if (lastRunId) pollRecon(lastRunId);
    };

    async function startRecon(mode) {
        const target = ($('recon-target') && $('recon-target').value || '').trim();
        if (!target) {
            toast('請先填授權範圍內的目標（網域或 URL）', 'error');
            return;
        }
        const profile = ($('recon-profile') && $('recon-profile').value) || 'quick';
        const path = mode === 'auto' ? '/api/recon/auto' : '/api/recon/runs';
        const body = mode === 'auto' ? { target, profile: 'deep' } : { target, profile };
        try {
            const res = await reconFetch(path, { method: 'POST', body: JSON.stringify(body) });
            const data = await res.json().catch(() => ({}));
            if (!res.ok) {
                toast(data.message || data.error || ('偵察啟動失敗 ' + res.status), 'error');
                return;
            }
            lastRunId = data.id || '';
            renderRun(data);
            toast('偵察已啟動', 'success');
            if (lastRunId) {
                if (pollTimer) clearInterval(pollTimer);
                pollTimer = setInterval(() => pollRecon(lastRunId), 2000);
            }
        } catch (err) {
            toast('偵察請求失敗', 'error');
        }
    }

    async function pollRecon(id) {
        try {
            const res = await reconFetch('/api/recon/runs/' + encodeURIComponent(id));
            const data = await res.json().catch(() => ({}));
            if (!res.ok) return;
            renderRun(data);
            if (data.status && data.status !== 'running') {
                if (pollTimer) clearInterval(pollTimer);
                pollTimer = null;
            }
        } catch (e) { /* keep polling */ }
    }

    async function cancelRecon() {
        if (!lastRunId) return;
        const res = await reconFetch('/api/recon/runs/' + encodeURIComponent(lastRunId) + '/cancel', { method: 'POST' });
        if (res.ok) toast('已要求停止', 'info');
    }

    function renderRun(run) {
        const box = $('recon-result');
        if (!box) return;
        const results = Array.isArray(run.results) ? run.results : [];
        const rows = results.map(function (r) {
            const assets = (r.assets || []).slice(0, 8).map(function (a) {
                return (a.type || '') + ' ' + (a.value || '');
            }).join('；');
            return '<tr><td>' + escapeHtml(r.name || '') + '</td><td>' + escapeHtml(r.phase || '') +
                '</td><td>' + escapeHtml(r.status || '') + '</td><td>' + escapeHtml(r.summary || r.error || '') +
                '</td><td>' + escapeHtml(assets) + '</td></tr>';
        }).join('');
        box.innerHTML = '<p>任務 ' + escapeHtml(run.id || '') + '　狀態 ' + escapeHtml(run.status || '') +
            '　目標 ' + escapeHtml(run.target || '') + '</p>' +
            '<table class="data-table"><thead><tr><th>收集器</th><th>階段</th><th>狀態</th><th>摘要</th><th>資產</th></tr></thead><tbody>' +
            (rows || '<tr><td colspan="5">尚無結果</td></tr>') + '</tbody></table>';
    }

    function escapeHtml(s) {
        return String(s || '').replace(/[&<>"']/g, function (c) {
            return ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c];
        });
    }
})();
