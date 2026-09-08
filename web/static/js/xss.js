// XSS 收割模块前端逻辑
// 支持: 接管载荷生成/复制/删除、收割回显列表/详情/状态流转、收集服务开关

(function() {
    'use strict';

    const XSS = {
        payloads: [],
        payloadTotal: 0,
        captures: [],
        captureTotal: 0,
        capturePageSize: 50,
        loadedPayloads: false,
        loadedCaptures: false
    };

    const API_BASE = '/api/xss';
    const CONFIG_API = '/api/config';

    function apiRequest(method, url, data) {
        const options = {
            method: method,
            headers: { 'Content-Type': 'application/json' }
        };
        if (data && (method === 'POST' || method === 'PUT' || method === 'PATCH' || method === 'DELETE')) {
            options.body = JSON.stringify(data);
        }
        if (typeof apiFetch === 'function') {
            return apiFetch(url, options).then(function(r) { return r.json(); });
        }
        return fetch(url, options).then(function(r) { return r.json(); });
    }

    function showToast(message, type) {
        if (window.showToast) {
            window.showToast(message, type || 'info');
            return;
        }
        const container = document.createElement('div');
        container.style.cssText = 'position:fixed;top:20px;right:20px;z-index:10200;padding:10px 18px;border-radius:6px;color:#fff;background:#3182ce;font-size:0.875rem;box-shadow:0 4px 12px rgba(0,0,0,0.2);';
        if (type === 'error') container.style.background = '#e53e3e';
        else if (type === 'success') container.style.background = '#38a169';
        else if (type === 'warn') container.style.background = '#d69e2e';
        container.textContent = message;
        document.body.appendChild(container);
        setTimeout(function() { container.remove(); }, 3500);
    }

    function escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = String(text);
        return div.innerHTML;
    }

    function escapeAttr(text) {
        return escapeHtml(text).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function formatTime(dateStr) {
        if (!dateStr) return '-';
        try { return new Date(dateStr).toLocaleString(); } catch (e) { return String(dateStr); }
    }

    function statusLabel(status) {
        const map = {
            armed: ['armed', '已就绪'],
            fired: ['fired', '已回连'],
            expired: ['expired', '已过期'],
            new: ['new', '未处理'],
            seized: ['seized', '已接管'],
            analyzed: ['analyzed', '已分析'],
            ignored: ['ignored', '已忽略']
        };
        const entry = map[String(status || '').trim()];
        if (!entry) return escapeHtml(status || '');
        return '<span class="xss-status xss-status-' + entry[0] + '">' + entry[1] + '</span>';
    }

    function sel(id) {
        return document.getElementById(id);
    }

    function closeModal(elm) {
        const overlay = elm && elm.classList && elm.classList.contains('xss-modal-overlay')
            ? elm
            : (elm && elm.closest ? elm.closest('.xss-modal-overlay') : null);
        if (overlay) overlay.style.display = 'none';
    }

    // ============================================================================
    // 页面初始化
    // ============================================================================

    XSS.init = function(force) {
        if (force || !XSS.loadedPayloads) {
            XSS.loadConfig(true);
            XSS.loadPayloads();
        } else {
            XSS.renderPayloadBar();
            XSS.renderStatusBar(document.getElementById('xss-status-last'));
        }
        XSS.loadCaptures();
    };

    // ============================================================================
    // 收集服务状态
    // ============================================================================

    XSS.loadConfig = function(renderBar) {
        apiRequest('GET', API_BASE + '/config').then(function(data) {
            if (data && typeof data.enabled === 'boolean') {
                XSS.statusEnabled = data.enabled;
                XSS.statusPublicURL = data.public_url || '';
                if (renderBar) XSS.renderStatusBar();
            }
        }).catch(function(err) {
            console.warn('加载XSS收集服务配置失败:', err);
        });
    };

    function renderStatusBar() {
        const bar = sel('xss-status-bar');
        if (!bar) return;
        if (!XSS.statusEnabled) {
            bar.innerHTML = '<span class="xss-status-dot xss-off"></span><span>收集服务<strong>未启用</strong>——启用后生成的载荷才可回连收割。</span>';
            return;
        }
        const url = XSS.statusPublicURL ? escapeHtml(XSS.statusPublicURL) : '-';
        bar.innerHTML = '<span class="xss-status-dot xss-on"></span><span>收集服务<strong>已启用</strong>，收割地址：<code>' + url + '/api/xss/capture</code></span>';
        const last = sel('xss-status-last');
        if (last) last.textContent = formatTime(new Date().toISOString());
    }

    function renderPayloadBar() {
        const count = sel('xss-payload-count');
        if (count) count.textContent = String(XSS.payloadTotal);
    }

    XSS.renderStatusBar = renderStatusBar;
    XSS.renderPayloadBar = renderPayloadBar;

    // ============================================================================
    // 接管载荷
    // ============================================================================

    XSS.loadPayloads = function() {
        XSS.loadedPayloads = true;
        apiRequest('GET', API_BASE + '/payloads').then(function(data) {
            XSS.payloads = (data && data.payloads) || [];
            XSS.payloadTotal = (data && data.total) || 0;
            XSS.renderPayloads();
            XSS.renderPayloadBar();
        }).catch(function(err) {
            console.warn('加载XSS载荷失败:', err);
            showToast('加载XSS载荷失败', 'error');
        });
    };

    XSS.renderPayloads = function() {
        const tbody = sel('xss-payload-list');
        const empty = sel('xss-payload-empty');
        if (!tbody) return;
        if (!XSS.payloads.length) {
            tbody.innerHTML = '';
            if (empty) empty.hidden = false;
            return;
        }
        if (empty) empty.hidden = true;
        let html = '';
        XSS.payloads.forEach(function(p) {
            const name = escapeHtml(p.name || '(未命名载荷)');
            const src = p.source_url ? escapeHtml(p.source_url) : '<span class="xss-muted">-</span>';
            const fired = String(p.status) === 'fired';
            const statusBadge = fired
                ? '<span class="xss-state-badge xss-badge-fired">已回连</span>'
                : '<span class="xss-state-badge">' + statusLabel(p.status) + '</span>';
            html +=
                '<tr data-xss-payload="' + escapeAttr(p.id) + '">' +
                    '<td class="xss-cell-name">' + name + '</td>' +
                    '<td>' + src + '</td>' +
                    '<td>' + statusBadge + '</td>' +
                    '<td class="xss-muted">' + formatTime(p.created_at) + '</td>' +
                    '<td class="xss-cell-actions">' +
                        '<button type="button" class="btn-secondary btn-sm" data-xss-action="show-script" data-xss-id="' + escapeAttr(p.id) + '" data-require-permission="xss:read">查看脚本</button>' +
                        '<button type="button" class="btn-secondary btn-sm" data-xss-action="copy-script" data-xss-id="' + escapeAttr(p.id) + '" data-require-permission="xss:read">复制</button>' +
                        '<button type="button" class="btn-danger-outline btn-sm" data-xss-action="delete-payload" data-xss-id="' + escapeAttr(p.id) + '" data-require-permission="xss:delete">删除</button>' +
                    '</td>' +
                '</tr>';
        });
        tbody.innerHTML = html;
    };

    XSS.openGenerateModal = function() {
        const modal = sel('xss-generate-modal');
        if (!modal) return;
        sel('xss-generate-name').value = '';
        sel('xss-generate-source').value = '';
        modal.style.display = 'flex';
        window.setTimeout(function() { if (sel('xss-generate-name')) sel('xss-generate-name').focus(); }, 50);
    };

    XSS.generatePayload = function() {
        const name = sel('xss-generate-name').value.trim();
        const source = sel('xss-generate-source').value.trim();
        if (!name) {
            showToast('请输入载荷名称', 'warn');
            return;
        }
        const body = { name: name, source_url: source };
        if (typeof getActiveProjectId === 'function') {
            const activeProjectId = getActiveProjectId();
            if (activeProjectId) body.project_id = activeProjectId;
        }
        apiRequest('POST', API_BASE + '/payloads/generate', body).then(function(data) {
            if (data && data.error) {
                showToast(data.error, 'error');
                return;
            }
            const payload = data && data.payload;
            closeModal(sel('xss-generate-modal'));
            XSS.loadPayloads();
            if (payload && payload.script) {
                XSS.openScriptModal(payload);
            }
        }).catch(function(err) {
            console.warn('生成XSS载荷失败:', err);
            showToast('生成XSS载荷失败', 'error');
        });
    };

    XSS.openScriptModal = function(payload) {
        const modal = sel('xss-script-modal');
        if (!modal) return;
        sel('xss-script-text').value = payload.script || '';
        const hint = modal.querySelector('.xss-modal-hint');
        if (hint && payload.id) {
            hint.innerHTML = '载荷ID：<code>' + escapeHtml(payload.id) + '</code>。将以下脚本植入目标页面的 XSS 触发点（如 <code>&lt;script&gt;</code>、事件属性、URL 参数注入点）。目标浏览器打开后会自动回连收集服务。';
        }
        modal.style.display = 'flex';
    };

    XSS.loadPayloadScript = function(id, openModal) {
        apiRequest('GET', API_BASE + '/payloads/' + encodeURIComponent(id)).then(function(data) {
            if (data && data.payload) {
                if (openModal) XSS.openScriptModal(data.payload);
                else if (window.navigator.clipboard) {
                    window.navigator.clipboard.writeText(data.payload.script || '').then(function() {
                        showToast('脚本已复制', 'success');
                    }).catch(function() {
                        fallbackCopy(data.payload.script || '');
                        showToast('脚本已复制', 'success');
                    });
                } else {
                    fallbackCopy(data.payload.script || '');
                    showToast('脚本已复制', 'success');
                }
            } else if (data && data.error) {
                showToast(data.error, 'error');
            }
        }).catch(function(err) {
            console.warn('加载XSS载荷脚本失败:', err);
            showToast('加载载荷脚本失败', 'error');
        });
    };

    function fallbackCopy(text) {
        const ta = document.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.left = '-9999px';
        document.body.appendChild(ta);
        ta.select();
        try { document.execCommand('copy'); } catch (e) { /* ignore */ }
        document.body.removeChild(ta);
    }

    XSS.copyScript = function() {
        const ta = sel('xss-script-text');
        if (!ta) return;
        if (window.navigator.clipboard) {
            window.navigator.clipboard.writeText(ta.value).then(function() {
                showToast('脚本已复制', 'success');
            }).catch(function() {
                fallbackCopy(ta.value);
                showToast('脚本已复制', 'success');
            });
        } else {
            fallbackCopy(ta.value);
            showToast('脚本已复制', 'success');
        }
    };

    XSS.deletePayload = function(id) {
        if (!window.confirm('确定删除该接管载荷？（不影响已收割到的记录）')) return;
        apiRequest('DELETE', API_BASE + '/payloads/' + encodeURIComponent(id)).then(function(data) {
            if (data && data.error) {
                showToast(data.error, 'error');
                return;
            }
            showToast('载荷已删除', 'success');
            XSS.loadPayloads();
        }).catch(function(err) {
            console.warn('删除XSS载荷失败:', err);
            showToast('删除载荷失败', 'error');
        });
    };

    // ============================================================================
    // 回显收割
    // ============================================================================

    XSS.loadCaptures = function() {
        const status = sel('xss-capture-status') ? sel('xss-capture-status').value : '';
        let url = API_BASE + '/captures?page=1&page_size=' + XSS.capturePageSize;
        if (status) url += '&status=' + encodeURIComponent(status);
        apiRequest('GET', url).then(function(data) {
            XSS.captures = (data && data.captures) || [];
            XSS.captureTotal = (data && data.total) || 0;
            XSS.renderCaptures();
        }).catch(function(err) {
            console.warn('加载XSS收割记录失败:', err);
            showToast('加载收割记录失败', 'error');
        });
    };

    function cookieSummary(cookies) {
        if (!cookies || !cookies.length) return '<span class="xss-muted">无（浏览器未暴露 HttpOnly Cookie）</span>';
        return cookies.map(function(c) {
            return '<code class="xss-cookie-chip">' + escapeHtml(c.name) + '</code>';
        }).join(' ');
    }

    XSS.renderCaptures = function() {
        const tbody = sel('xss-capture-list');
        const empty = sel('xss-capture-empty');
        const count = sel('xss-capture-count');
        if (!tbody) return;
        if (count) count.textContent = String(XSS.captureTotal);
        if (!XSS.captures.length) {
            tbody.innerHTML = '';
            if (empty) empty.hidden = false;
            return;
        }
        if (empty) empty.hidden = true;
        let html = '';
        XSS.captures.forEach(function(cap) {
            const page = cap.page_title ? escapeHtml(cap.page_title) : '<span class="xss-muted">-</span>';
            html +=
                '<tr data-xss-capture="' + escapeAttr(cap.id) + '">' +
                    '<td class="xss-muted">' + formatTime(cap.created_at) + '</td>' +
                    '<td class="xss-cell-source">' + escapeHtml(cap.source_url || '-') + '</td>' +
                    '<td>' + page + '</td>' +
                    '<td>' + cookieSummary(cap.cookies) + '</td>' +
                    '<td>' + statusLabel(cap.status) + '</td>' +
                    '<td class="xss-cell-actions">' +
                        '<button type="button" class="btn-secondary btn-sm" data-xss-action="show-capture" data-xss-id="' + escapeAttr(cap.id) + '" data-require-permission="xss:read">详情</button>' +
                        '<button type="button" class="btn-secondary btn-sm" data-xss-action="mark-seized" data-xss-id="' + escapeAttr(cap.id) + '" data-require-permission="xss:write">标记接管</button>' +
                        '<button type="button" class="btn-danger-outline btn-sm" data-xss-action="delete-capture" data-xss-id="' + escapeAttr(cap.id) + '" data-require-permission="xss:delete">删除</button>' +
                    '</td>' +
                '</tr>';
        });
        tbody.innerHTML = html;
    };

    function kvTable(mapObj, emptyText) {
        const entries = Object.entries(mapObj || {});
        if (!entries.length) return '<p class="xss-muted">' + (emptyText || '无') + '</p>';
        let html = '<table class="xss-kv-table"><thead><tr><th>键</th><th>值</th></tr></thead><tbody>';
        entries.forEach(function(kv) {
            html += '<tr><td>' + escapeHtml(kv[0]) + '</td><td><code>' + escapeHtml(String(kv[1] || '')) + '</code></td></tr>';
        });
        html += '</tbody></table>';
        return html;
    }

    function cookieTable(cookies) {
        if (!cookies || !cookies.length) return '<p class="xss-muted">无（HttpOnly Cookie 不会暴露给 document.cookie）</p>';
        let html = '<table class="xss-kv-table"><thead><tr><th>名称</th><th>值</th><th>Domain</th><th>Path</th></tr></thead><tbody>';
        cookies.forEach(function(c) {
            const flags = [];
            if (c.secure) flags.push('Secure');
            if (c.http_only === true) flags.push('HttpOnly');
            html += '<tr><td>' + escapeHtml(c.name) + '</td><td><code class="xss-cookie-value">' + escapeHtml(c.value) + '</code></td><td>' + escapeHtml(c.domain || '-') + '</td><td>' + escapeHtml(c.path || '-') + (flags.length ? ' <span class="xss-muted">(' + flags.join('/') + ')</span>' : '') + '</td></tr>';
        });
        html += '</tbody></table>';
        return html;
    }

    XSS.openCaptureDetail = function(id) {
        apiRequest('GET', API_BASE + '/captures/' + encodeURIComponent(id)).then(function(data) {
            if (data && data.error) {
                showToast(data.error, 'error');
                return;
            }
            const cap = data && data.capture;
            if (!cap) {
                showToast('收割记录不存在', 'error');
                return;
            }
            const modal = sel('xss-detail-modal');
            const body = sel('xss-detail-body');
            if (!modal || !body) return;
            const details = [
                ['来源 URL', escapeHtml(cap.source_url || '-')],
                ['页面标题', escapeHtml(cap.page_title || '-')],
                ['URL 片段', escapeHtml(cap.url_fragment || '-')],
                ['客户端 IP', escapeHtml(cap.client_ip || '-')],
                ['浏览器 / UA', escapeHtml(cap.user_agent || '-')],
                ['收割时间', formatTime(cap.created_at)]
            ].map(function(row) {
                return '<tr><th>' + row[0] + '</th><td>' + row[1] + '</td></tr>';
            }).join('');
            body.innerHTML =
                '<table class="xss-kv-table"><tbody>' + details + '</tbody></table>' +
                '<div class="xss-detail-block"><h4>Cookie</h4>' + cookieTable(cap.cookies) + '</div>' +
                '<div class="xss-detail-block"><h4>localStorage</h4>' + kvTable(cap.local_storage) + '</div>' +
                '<div class="xss-detail-block"><h4>sessionStorage</h4>' + kvTable(cap.session_storage) + '</div>';
            modal.style.display = 'flex';
        }).catch(function(err) {
            console.warn('加载收割详情失败:', err);
            showToast('加载收割详情失败', 'error');
        });
    };

    XSS.updateCaptureStatus = function(id, status) {
        apiRequest('PUT', API_BASE + '/captures/' + encodeURIComponent(id) + '/status', { status: status }).then(function(data) {
            if (data && data.error) {
                showToast(data.error, 'error');
                return;
            }
            showToast('状态已更新', 'success');
            XSS.loadCaptures();
        }).catch(function(err) {
            console.warn('更新收割记录状态失败:', err);
            showToast('更新状态失败', 'error');
        });
    };

    XSS.deleteCapture = function(id) {
        if (!window.confirm('确定删除该收割记录？')) return;
        apiRequest('DELETE', API_BASE + '/captures/' + encodeURIComponent(id)).then(function(data) {
            if (data && data.error) {
                showToast(data.error, 'error');
                return;
            }
            showToast('收割记录已删除', 'success');
            XSS.loadCaptures();
        }).catch(function(err) {
            console.warn('删除收割记录失败:', err);
            showToast('删除收割记录失败', 'error');
        });
    };

    // ============================================================================
    // 收集服务配置（写入 /api/config）
    // ============================================================================

    XSS.showConfig = function() {
        const modal = sel('xss-config-modal');
        if (!modal) return;
        apiRequest('GET', API_BASE + '/config').then(function(data) {
            const enabled = !!(data && data.enabled);
            const url = (data && data.public_url) || '';
            sel('xss-config-enabled').checked = enabled;
            sel('xss-config-bind').value = url.split('://')[1] || url || '-';
            sel('xss-config-url').value = url || '-';
            sel('xss-config-cooldown').value = '';
            apiRequest('GET', CONFIG_API).then(function(cfg) {
                const xs = cfg && cfg.xss;
                if (!xs) return;
                if (sel('xss-config-bind') && xs.bind_host) sel('xss-config-bind').value = xs.bind_host + ':' + (xs.bind_port || '-');
                if (sel('xss-config-cooldown') && typeof xs.cooldown_seconds === 'number') sel('xss-config-cooldown').value = String(xs.cooldown_seconds);
            }).catch(function() { /* status-only fallback */ });
        }).catch(function(err) {
            console.warn('加载XSS收集服务配置失败:', err);
            showToast('加载配置失败', 'error');
            return;
        });
        modal.style.display = 'flex';
    };

    XSS.saveConfig = function() {
        const enabled = sel('xss-config-enabled').checked;
        const body = { xss: { enabled: enabled } };
        apiRequest('PUT', CONFIG_API, body).then(function(data) {
            if (data && data.error) {
                showToast(data.error, 'error');
                return;
            }
            showToast('收集服务开关已保存（重启服务器后生效）', 'success');
            closeModal(sel('xss-config-modal'));
            XSS.loadConfig(true);
        }).catch(function(err) {
            console.warn('保存XSS收集服务配置失败:', err);
            showToast('保存配置失败', 'error');
        });
    };

    // ============================================================================
    // 动态内容操作按钮 — 事件委托，避免把用户可控值拼入 inline onclick
    // ============================================================================

    function bindXSSActionDelegation() {
        if (document.documentElement.dataset.xssActionsBound === '1') return;
        document.documentElement.dataset.xssActionsBound = '1';
        document.addEventListener('click', function(e) {
            const btn = e.target.closest('[data-xss-action]');
            if (!btn) return;
            e.preventDefault();
            e.stopImmediatePropagation();
            const action = btn.getAttribute('data-xss-action');
            const id = btn.getAttribute('data-xss-id');
            if (action === 'show-script') { XSS.loadPayloadScript(id, true); }
            else if (action === 'copy-script') { XSS.loadPayloadScript(id, false); }
            else if (action === 'delete-payload') { XSS.deletePayload(id); }
            else if (action === 'show-capture') { XSS.openCaptureDetail(id); }
            else if (action === 'mark-seized') { XSS.updateCaptureStatus(id, 'seized'); }
            else if (action === 'delete-capture') { XSS.deleteCapture(id); }
        });
    }
    bindXSSActionDelegation();

    XSS.closeModal = closeModal;

    window.XSS = XSS;
})();