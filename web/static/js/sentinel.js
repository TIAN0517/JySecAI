// 零零哨兵 (Surface Watch) 暴露面巡檢前端控制器
(function () {
    let currentSnapshot = null;
    let pollInterval = null;
    let activeTab = 'overview';
    let findingSevFilter = 'all';
    let findingCatFilter = 'all';

    const DB_CHECKLIST = [
        { id: "elasticsearch", name: "Elasticsearch", ports: [9200], method: "HTTP GET / 識別 You Know, for Search" },
        { id: "opensearch", name: "OpenSearch", ports: [9200], method: "HTTP GET / OpenSearch 橫幅" },
        { id: "es-transport", name: "Elasticsearch Transport", ports: [9300], method: "TCP 傳輸層連通" },
        { id: "kibana", name: "Kibana", ports: [5601], method: "HTTP 控制台可達" },
        { id: "mysql", name: "MySQL / MariaDB", ports: [3306, 3307], method: "TCP 握手版本串" },
        { id: "sqlserver", name: "SQL Server", ports: [1433], method: "TDS PRELOGIN" },
        { id: "db2", name: "IBM DB2", ports: [50000, 50001], method: "DRDA 橫幅" },
        { id: "mongodb", name: "MongoDB", ports: [27017, 27018], method: "isMaster 未授權探測" },
        { id: "postgresql", name: "PostgreSQL", ports: [5432], method: "啟動/SSL 握手" },
        { id: "redis", name: "Redis", ports: [6379, 6380], method: "INFO / NOAUTH" },
        { id: "oracle", name: "Oracle", ports: [1521], method: "TNS ping" },
        { id: "couchdb", name: "CouchDB", ports: [5984], method: "HTTP Welcome JSON" },
        { id: "cassandra", name: "Cassandra", ports: [9042], method: "CQL native OPTIONS" },
        { id: "memcached", name: "Memcached", ports: [11211], method: "stats 未授權" },
        { id: "clickhouse", name: "ClickHouse", ports: [8123], method: "HTTP /ping" },
        { id: "influxdb", name: "InfluxDB", ports: [8086], method: "HTTP /ping" },
        { id: "neo4j", name: "Neo4j", ports: [7474], method: "HTTP 發現接口" },
        { id: "solr", name: "Apache Solr", ports: [8983], method: "HTTP /solr/" },
        { id: "etcd", name: "etcd", ports: [2379], method: "HTTP /version" },
        { id: "couchbase", name: "Couchbase", ports: [8091], method: "HTTP /pools" },
        { id: "arangodb", name: "ArangoDB", ports: [8529], method: "HTTP /_api/version" },
        { id: "rethinkdb", name: "RethinkDB", ports: [28015], method: "TCP 握手" },
        { id: "firebird", name: "Firebird", ports: [3050], method: "TCP 橫幅" },
        { id: "tidb", name: "TiDB", ports: [4000], method: "MySQL 兼容握手" },
        { id: "oceanbase", name: "OceanBase", ports: [2881], method: "握手橫幅" },
        { id: "kingbase", name: "人大金倉 KingbaseES", ports: [54321], method: "PostgreSQL 兼容握手" },
        { id: "cockroachdb", name: "CockroachDB", ports: [26257], method: "PostgreSQL 兼容握手" },
        { id: "hbase", name: "Apache HBase", ports: [16010], method: "HTTP /master-status" },
        { id: "hive", name: "Apache Hive", ports: [10000], method: "HiveServer2 默認口" },
        { id: "dameng", name: "達夢 Dameng", ports: [5236], method: "TCP 默認口 / 橫幅" }
    ];

    const SEV_LABELS = { high: '高危', medium: '中危', low: '低危', info: '信息' };
    const CAT_LABELS = {
        login: '登錄頁', test: '測試系統', sample: '樣例系統', database: '數據庫',
        tls: '證書', port: '端口', storage: '存儲桶', api: '接口', other: '資產'
    };
    const SCOPE_LABELS = { official: '主域', product: '業務', related: '子域' };

    function showToast(message, type = 'info') {
        if (typeof window.showToast === 'function') {
            window.showToast(message, type);
        } else if (typeof showNotification === 'function') {
            showNotification(message, type);
        } else {
            console.log(`[${type}]`, message);
        }
    }

    function sentinelFetch(url, options = {}) {
        if (typeof apiFetch === 'function') {
            return apiFetch(url, options);
        }
        const opts = { ...options };
        opts.credentials = opts.credentials || 'same-origin';
        return fetch(url, opts);
    }

    function initSentinelPage() {
        const form = document.getElementById('sentinel-scan-form');
        if (form && !form.dataset.bound) {
            form.dataset.bound = 'true';
            form.addEventListener('submit', (e) => {
                e.preventDefault();
                startSentinelScan();
            });
        }

        const input = document.getElementById('sentinel-target-input');
        if (input && !input.dataset.bound) {
            input.dataset.bound = 'true';
            input.addEventListener('input', () => {
                const hint = document.getElementById('sentinel-input-error');
                if (hint) hint.textContent = '';
            });
        }

        renderDbChecklist();
        loadLatestSentinelScan();
    }

    async function loadLatestSentinelScan() {
        try {
            const res = await sentinelFetch('/api/sentinel/latest');
            if (!res.ok) return;
            const data = await res.json();
            if (data && data.target) {
                currentSnapshot = data;
                renderSnapshot(data);
            }
        } catch (err) {
            console.warn('加載最近快照失敗', err);
        }
    }

    async function startSentinelScan() {
        const input = document.getElementById('sentinel-target-input');
        const errHint = document.getElementById('sentinel-input-error');
        const target = (input ? input.value : '').trim();

        if (!target) {
            if (errHint) errHint.textContent = '請輸入二級域名或公網 IPv4';
            return;
        }

        const btn = document.getElementById('sentinel-submit-btn');
        if (btn) {
            btn.disabled = true;
            btn.innerHTML = '<span class="loading-spinner" style="display:inline-block;width:14px;height:14px;border:2px solid #fff;border-top-color:transparent;border-radius:50%;animation:spin 0.8s linear infinite;margin-right:6px;"></span>檢測中...';
        }

        try {
            const res = await sentinelFetch('/api/sentinel/scan', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ target })
            });
            const data = await res.json();
            if (!res.ok) {
                if (errHint) errHint.textContent = data.error || '啟動檢測失敗';
                resetScanButton();
                return;
            }

            if (errHint) errHint.textContent = '';
            showToast(`已啟動對 ${target} 的暴露面巡檢`, 'info');

            // 輪詢狀態
            if (pollInterval) clearInterval(pollInterval);
            pollInterval = setInterval(() => pollSentinelStatus(data.scan_id), 1500);
        } catch (err) {
            if (errHint) errHint.textContent = '網絡異常，請稍後重試';
            resetScanButton();
        }
    }

    async function pollSentinelStatus(scanId) {
        try {
            const res = await sentinelFetch(`/api/sentinel/status/${encodeURIComponent(scanId)}`);
            if (!res.ok) return;
            const snapshot = await res.json();

            if (snapshot.status === 'completed' || snapshot.status === 'failed') {
                clearInterval(pollInterval);
                pollInterval = null;
                resetScanButton();

                if (snapshot.status === 'completed') {
                    currentSnapshot = snapshot;
                    renderSnapshot(snapshot);
                    showToast(`${snapshot.target} 本輪巡檢完成！`, 'success');
                } else {
                    const errHint = document.getElementById('sentinel-input-error');
                    if (errHint) errHint.textContent = snapshot.error || '掃描異常終止';
                    showToast('暴露面探測失敗: ' + (snapshot.error || ''), 'error');
                }
            }
        } catch (e) {
            console.warn('輪詢快照失敗', e);
        }
    }

    function resetScanButton() {
        const btn = document.getElementById('sentinel-submit-btn');
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = `<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="2"></circle><path d="M16.24 7.76A6 6 0 1 0 8.23 16.67"></path><path d="M19.07 4.93A10 10 0 0 0 6.99 3.34"></path></svg> 開始檢測`;
        }
    }

    function renderSnapshot(s) {
        if (!s) return;

        // 更新統計卡片
        const hostEl = document.getElementById('sentinel-kpi-hosts');
        const loginEl = document.getElementById('sentinel-kpi-logins');
        const dbEl = document.getElementById('sentinel-kpi-databases');
        const highEl = document.getElementById('sentinel-kpi-high');

        if (hostEl) {
            hostEl.textContent = s.summary.aliveCount || 0;
            const sub = hostEl.nextElementSibling;
            if (sub) sub.textContent = `共解析 ${s.summary.hostCount || 0}`;
        }
        if (loginEl) {
            loginEl.textContent = s.summary.loginCount || 0;
            const sub = loginEl.nextElementSibling;
            if (sub) sub.textContent = '頁 · 接口 · 郵箱';
        }
        if (dbEl) {
            dbEl.textContent = s.summary.databaseCount || 0;
            const sub = dbEl.nextElementSibling;
            if (sub) sub.textContent = '默認口 · 橫幅';
        }
        if (highEl) {
            highEl.textContent = s.summary.highCount || 0;
            const sub = highEl.nextElementSibling;
            if (sub) sub.textContent = `中危 ${s.summary.mediumCount || 0}`;
        }

        // 更新目標元信息
        const metaEl = document.getElementById('sentinel-finish-meta');
        if (metaEl) {
            const timeStr = s.finishedAt ? new Date(s.finishedAt).toLocaleString() : '剛才';
            metaEl.textContent = `目標 ${s.target} · 完成於 ${timeStr} · 開放端口 ${s.summary.openPortCount || 0} · 探測路徑 ${s.summary.endpointCount || 0} (耗時 ${s.duration_ms || 0}ms)`;
        }

        // 啟用同步按鈕
        const syncAssetsBtn = document.getElementById('sentinel-sync-assets-btn');
        const syncVulnsBtn = document.getElementById('sentinel-sync-vulns-btn');
        const exportBtn = document.getElementById('sentinel-export-btn');
        if (syncAssetsBtn) syncAssetsBtn.disabled = false;
        if (syncVulnsBtn) syncVulnsBtn.disabled = false;
        if (exportBtn) exportBtn.disabled = false;

        // 渲染當前選中的視圖
        renderActiveView();
    }

    function switchSentinelTab(tab) {
        activeTab = tab;
        document.querySelectorAll('.sentinel-tab-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.tab === tab);
        });
        document.querySelectorAll('.sentinel-tab-pane').forEach(pane => {
            pane.classList.toggle('active', pane.dataset.pane === tab);
        });
        renderActiveView();
    }
    window.switchSentinelTab = switchSentinelTab;

    function renderActiveView() {
        if (!currentSnapshot) return;
        switch (activeTab) {
            case 'overview':
                renderOverviewTab();
                break;
            case 'logins':
                renderLoginsTab();
                break;
            case 'labs':
                renderLabsTab();
                break;
            case 'databases':
                renderDatabasesTab();
                break;
            case 'assets':
                renderAssetsTab();
                break;
            case 'findings':
                renderFindingsTab();
                break;
        }
    }

    function renderOverviewTab() {
        const container = document.getElementById('sentinel-overview-findings');
        if (!container) return;
        const priority = (currentSnapshot.findings || []).filter(f => f.severity === 'high' || f.severity === 'medium');
        if (priority.length === 0) {
            container.innerHTML = '<div style="padding:24px;text-align:center;color:var(--text-muted);border:1px dashed var(--border-color);border-radius:8px;">本輪未發現中高危暴露面風險</div>';
            return;
        }
        container.innerHTML = priority.map(f => createFindingCardHTML(f)).join('');
    }

    function renderLoginsTab() {
        const findingsEl = document.getElementById('sentinel-logins-findings');
        const pathsEl = document.getElementById('sentinel-logins-paths');
        const loginFindings = (currentSnapshot.findings || []).filter(f => f.category === 'login');
        if (findingsEl) {
            findingsEl.innerHTML = loginFindings.length ? loginFindings.map(f => createFindingCardHTML(f)).join('') : '<p style="color:var(--text-muted);font-size:13px;">未發現對外登錄頁。</p>';
        }
        if (pathsEl) {
            const loginEps = (currentSnapshot.endpoints || []).filter(ep => (ep.tags || []).some(t => t === 'login' || t === 'auth'));
            pathsEl.innerHTML = renderEndpointsTable(loginEps);
        }
    }

    function renderLabsTab() {
        const findingsEl = document.getElementById('sentinel-labs-findings');
        const pathsEl = document.getElementById('sentinel-labs-paths');
        const labFindings = (currentSnapshot.findings || []).filter(f => f.category === 'test' || f.category === 'sample');
        if (findingsEl) {
            findingsEl.innerHTML = labFindings.length ? labFindings.map(f => createFindingCardHTML(f)).join('') : '<p style="color:var(--text-muted);font-size:13px;">未發現在線的測試或樣例系統。</p>';
        }
        if (pathsEl) {
            const labEps = (currentSnapshot.endpoints || []).filter(ep => (ep.tags || []).some(t => t === 'test' || t === 'sample') || /\/(test|demo|sample|staging|dev)/i.test(ep.url));
            pathsEl.innerHTML = renderEndpointsTable(labEps);
        }
    }

    function renderDatabasesTab() {
        const container = document.getElementById('sentinel-databases-table-wrap');
        if (!container) return;
        const dbs = currentSnapshot.databases || [];
        if (dbs.length === 0) {
            container.innerHTML = '<p style="color:var(--text-muted);font-size:13px;padding:12px;">本輪未命中數據庫默認口。</p>';
            return;
        }

        let html = `
        <table class="sentinel-table">
            <thead>
                <tr>
                    <th>引擎</th>
                    <th>主機</th>
                    <th>端口</th>
                    <th>風險</th>
                    <th>證據</th>
                </tr>
            </thead>
            <tbody>
        `;
        dbs.forEach(d => {
            const tone = d.risk === 'unauth' ? 'high' : 'medium';
            const text = d.risk === 'unauth' ? '未授權' : (d.risk === 'identified' ? '握手暴露' : '端口開放');
            html += `
                <tr>
                    <td><strong>${escapeHTML(d.engineName)}</strong></td>
                    <td class="sentinel-code">${escapeHTML(d.host)}</td>
                    <td class="sentinel-code">${d.port}</td>
                    <td><span class="sentinel-badge sentinel-badge-${tone}">${text}</span></td>
                    <td style="color:var(--text-secondary);">${escapeHTML(d.evidence || '—')}</td>
                </tr>
            `;
        });
        html += '</tbody></table>';
        container.innerHTML = html;
    }

    function renderAssetsTab() {
        const assetsWrap = document.getElementById('sentinel-assets-table-wrap');
        const portsWrap = document.getElementById('sentinel-ports-table-wrap');

        if (assetsWrap) {
            const assets = currentSnapshot.assets || [];
            let html = `
            <table class="sentinel-table">
                <thead>
                    <tr>
                        <th>主機</th>
                        <th>範圍</th>
                        <th>IP</th>
                        <th>證書</th>
                        <th>標題</th>
                    </tr>
                </thead>
                <tbody>
            `;
            assets.forEach(a => {
                const scopeText = SCOPE_LABELS[a.scope] || a.scope || '子域';
                const certBadge = a.tlsValid ? '<span class="sentinel-badge" style="background:rgba(40,167,69,0.15);color:#28a745;">有效</span>' : '<span class="sentinel-badge" style="color:var(--text-muted);">—</span>';
                html += `
                    <tr>
                        <td class="sentinel-code" style="font-weight:${a.alive ? '600' : '400'};color:${a.alive ? 'var(--text-primary)' : 'var(--text-muted)'};">${escapeHTML(a.host)}</td>
                        <td>${scopeText}</td>
                        <td class="sentinel-code">${escapeHTML(a.ip || '無解析')}</td>
                        <td>${certBadge}</td>
                        <td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escapeHTML(a.title || '—')}</td>
                    </tr>
                `;
            });
            html += '</tbody></table>';
            assetsWrap.innerHTML = html;
        }

        if (portsWrap) {
            const ports = currentSnapshot.ports || [];
            if (ports.length === 0) {
                portsWrap.innerHTML = '<p style="color:var(--text-muted);font-size:13px;padding:12px;">本輪未發現開放端口。</p>';
            } else {
                let html = `
                <table class="sentinel-table">
                    <thead>
                        <tr>
                            <th>主機</th>
                            <th>IP</th>
                            <th>端口</th>
                            <th>服務</th>
                        </tr>
                    </thead>
                    <tbody>
                `;
                ports.forEach(p => {
                    html += `
                        <tr>
                            <td class="sentinel-code">${escapeHTML(p.host)}</td>
                            <td class="sentinel-code" style="color:var(--text-muted);">${escapeHTML(p.ip || '—')}</td>
                            <td class="sentinel-code"><strong>${p.port}</strong></td>
                            <td>${escapeHTML(p.service || 'TCP')}</td>
                        </tr>
                    `;
                });
                html += '</tbody></table>';
                portsWrap.innerHTML = html;
            }
        }
    }

    function renderFindingsTab() {
        const container = document.getElementById('sentinel-findings-list');
        if (!container) return;

        let list = currentSnapshot.findings || [];
        if (findingSevFilter !== 'all') {
            list = list.filter(f => f.severity === findingSevFilter);
        }
        if (findingCatFilter !== 'all') {
            list = list.filter(f => f.category === findingCatFilter);
        }

        const countEl = document.getElementById('sentinel-findings-count');
        if (countEl) countEl.textContent = `${(currentSnapshot.findings || []).length} 條 · 當前顯示 ${list.length} 條`;

        if (list.length === 0) {
            container.innerHTML = '<div style="padding:32px;text-align:center;color:var(--text-muted);border:1px dashed var(--border-color);border-radius:8px;">沒有符合條件的發現項</div>';
            return;
        }
        container.innerHTML = list.map(f => createFindingCardHTML(f)).join('');
    }

    function setFindingFilter(type, val) {
        if (type === 'sev') {
            findingSevFilter = val;
            document.querySelectorAll('.sentinel-sev-btn').forEach(b => b.classList.toggle('active', b.dataset.val === val));
        } else {
            findingCatFilter = val;
            document.querySelectorAll('.sentinel-cat-btn').forEach(b => b.classList.toggle('active', b.dataset.val === val));
        }
        renderFindingsTab();
    }
    window.setFindingFilter = setFindingFilter;

    function renderEndpointsTable(eps) {
        if (!eps || eps.length === 0) {
            return '<p style="color:var(--text-muted);font-size:13px;">沒有匹配的路徑。</p>';
        }
        let html = `
        <table class="sentinel-table">
            <thead>
                <tr>
                    <th>URL</th>
                    <th>狀態</th>
                    <th>標記</th>
                    <th>說明</th>
                </tr>
            </thead>
            <tbody>
        `;
        eps.forEach(ep => {
            const tags = (ep.tags || []).map(t => `<span class="sentinel-badge sentinel-badge-info" style="margin-right:4px;">${escapeHTML(t)}</span>`).join('');
            const spaTag = ep.spaFallback ? '<span class="sentinel-badge sentinel-badge-spa">spa 回退</span>' : '';
            html += `
                <tr>
                    <td class="sentinel-code"><a href="${escapeHTML(ep.url)}" target="_blank" style="color:var(--accent-color);text-decoration:none;">${escapeHTML(ep.url)}</a></td>
                    <td class="sentinel-code">${ep.status || 'err'}</td>
                    <td>${tags}${spaTag}</td>
                    <td style="color:var(--text-secondary);max-width:320px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">${escapeHTML(ep.title || ep.snippet || '—')}</td>
                </tr>
            `;
        });
        html += '</tbody></table>';
        return html;
    }

    function createFindingCardHTML(f) {
        const sevBadge = `<span class="sentinel-badge sentinel-badge-${f.severity}">${SEV_LABELS[f.severity] || f.severity}</span>`;
        const catBadge = `<span class="sentinel-badge" style="background:var(--bg-secondary);border:1px solid var(--border-color);">${CAT_LABELS[f.category] || f.category}</span>`;
        const hostSpan = f.host ? `<span class="sentinel-code" style="color:var(--text-muted);font-size:12px;">${escapeHTML(f.host)}</span>` : '';
        const urlP = f.url ? `<p style="margin:4px 0 0 0;font-family:monospace;font-size:12px;color:var(--accent-color);"><a href="${escapeHTML(f.url)}" target="_blank" style="color:inherit;text-decoration:none;">${escapeHTML(f.url)}</a></p>` : '';

        return `
            <article class="sentinel-finding-card">
                <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
                    ${sevBadge}
                    ${catBadge}
                    ${hostSpan}
                </div>
                <h4 style="margin:6px 0 2px 0;font-size:14px;color:var(--text-primary);">${escapeHTML(f.title)}</h4>
                <p style="margin:0;font-size:13px;color:var(--text-secondary);line-height:1.5;">${escapeHTML(f.detail)}</p>
                ${urlP}
            </article>
        `;
    }

    function renderDbChecklist() {
        const container = document.getElementById('sentinel-db-checklist');
        if (!container) return;
        container.innerHTML = DB_CHECKLIST.map(d => `
            <div class="sentinel-checklist-card">
                <div style="font-weight:600;font-size:13px;color:var(--text-primary);">${escapeHTML(d.name)}</div>
                <div class="sentinel-code" style="font-size:12px;color:var(--text-muted);margin-top:4px;">${d.ports.join(', ')} · ${escapeHTML(d.method)}</div>
            </div>
        `).join('');
    }

    async function syncSentinelToAssets() {
        if (!currentSnapshot || !currentSnapshot.id) return;
        const btn = document.getElementById('sentinel-sync-assets-btn');
        if (btn) btn.disabled = true;

        const projId = (typeof vulnerabilityFilters !== 'undefined' && vulnerabilityFilters.project_id)
            ? vulnerabilityFilters.project_id
            : (document.getElementById('asset-project-filter')?.value || document.getElementById('vulnerability-project-filter')?.value || '');

        try {
            const res = await sentinelFetch('/api/sentinel/sync/assets', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scan_id: currentSnapshot.id, project_id: projId })
            });
            const data = await res.json();
            if (res.ok) {
                showToast(`成功同步資產至系統資產庫 (新增: ${data.created}, 更新: ${data.updated}, 跳過: ${data.skipped})`, 'success');
            } else {
                showToast(data.error || '同步失敗', 'error');
            }
        } catch (e) {
            showToast('網絡異常，請稍後重試', 'error');
        } finally {
            if (btn) btn.disabled = false;
        }
    }
    window.syncSentinelToAssets = syncSentinelToAssets;

    async function syncSentinelToVulns() {
        if (!currentSnapshot || !currentSnapshot.id) return;
        const btn = document.getElementById('sentinel-sync-vulns-btn');
        if (btn) btn.disabled = true;

        const projId = (typeof vulnerabilityFilters !== 'undefined' && vulnerabilityFilters.project_id)
            ? vulnerabilityFilters.project_id
            : (document.getElementById('asset-project-filter')?.value || document.getElementById('vulnerability-project-filter')?.value || '');

        try {
            const res = await sentinelFetch('/api/sentinel/sync/vulnerabilities', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ scan_id: currentSnapshot.id, project_id: projId })
            });
            const data = await res.json();
            if (res.ok) {
                showToast(`成功同步至漏洞庫 (新增: ${data.created} 條, 跳過重複: ${data.skipped} 條)`, 'success');
            } else {
                showToast(data.error || '同步失敗', 'error');
            }
        } catch (e) {
            showToast('網絡異常，請稍後重試', 'error');
        } finally {
            if (btn) btn.disabled = false;
        }
    }
    window.syncSentinelToVulns = syncSentinelToVulns;

    function exportSentinelReport() {
        if (!currentSnapshot) return;
        const blob = new Blob([JSON.stringify(currentSnapshot, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `sentinel-report-${currentSnapshot.target || 'scan'}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
    }
    window.exportSentinelReport = exportSentinelReport;

    function escapeHTML(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    window.initSentinelPage = initSentinelPage;
})();
