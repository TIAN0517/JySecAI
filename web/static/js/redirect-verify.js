(function () {
    'use strict';

    // 批次受控跳轉驗證控制台。
    //
    // 流程：情蒐（FOFA / ZoomEye / Quake / Shodan）→ 巡站發掘跳轉參數 → 批次驗證 → 自動上鍊（漏洞紀錄）→ 報告。
    // 「跳轉目標」是操作者自己的受控回連端點；目標清單可手動貼上，也可從情蒐／巡站匯入。

    let pollTimer = null;
    let currentRunId = '';
    let lastReportId = '';
    // 植入載荷的「型態 × 編碼」相容矩陣，來自後端 GET /api/redirect-verify/implant。
    // 規則只存在後端一份（internal/redirect.ImplantEncodingMatrix），
    // 前端不自己複製一份規則 —— 規則寫兩份一定會漂移。
    let implantEncodingsByKind = null;

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
        return String(value == null ? '' : value).replace(/[&<>"']/g, (c) => ({
            '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
        }[c]));
    }

    function setStatus(message) {
        const el = $('redirect-verify-status');
        if (el) el.textContent = message;
    }

    // readTargets 讀取目標清單 textarea 的內容。
    function readTargets() {
        const el = $('redirect-verify-targets');
        return el ? lines(el.value) : [];
    }

    // writeTargets 覆寫目標清單（匯入情蒐／巡站結果時使用）。
    function writeTargets(values) {
        const el = $('redirect-verify-targets');
        if (!el) return;
        const merged = [];
        const seen = new Set();
        lines(el.value).concat(values || []).forEach((item) => {
            if (!item || seen.has(item)) return;
            seen.add(item);
            merged.push(item);
        });
        el.value = merged.join('\n');
    }

    // 代理出口與代理群組二選一：選了群組就由代理池挑代理，
    // 使用者不必每次把帶帳密的代理網址貼進來。
    function proxyGroupValue() {
        return (($('redirect-verify-proxy-group') || {}).value || '').trim();
    }

    function proxyURLValue() {
        if (proxyGroupValue()) return '';
        return (($('redirect-verify-proxy') || {}).value || '').trim();
    }

    function syncProxyGroupInputs() {
        const groupSelect = $('redirect-verify-proxy-group');
        const proxyInput = $('redirect-verify-proxy');
        if (!groupSelect || !proxyInput) return;
        const useGroup = !!proxyGroupValue();
        proxyInput.disabled = useGroup;
        proxyInput.placeholder = useGroup
            ? tr('redirectVerifyPage.proxyGroupActive', '由代理池提供出口')
            : 'socks5://user:pass@host:1080';
    }

    // normalizeImportedURLs 過濾匯入的 URL：只留 http/https，去重。
    function normalizeImportedURLs(values) {
        const out = [];
        const seen = new Set();
        (Array.isArray(values) ? values : []).forEach((item) => {
            const value = String(item == null ? '' : item).trim();
            if (!value || seen.has(value)) return;
            if (!/^https?:\/\//i.test(value)) return;
            seen.add(value);
            out.push(value);
        });
        return out;
    }

    // importVulnTargets 把既有漏洞紀錄的目標 URL 匯入目標清單。
    //
    // 既有紀錄的 Target 裡就是待複測的跳轉入口；匯入後批次引擎會自動
    // 把受控端點代入該 URL 的跳轉參數，等於用自己的端點把整批重跑一次。
    async function importVulnTargets() {
        const btn = $('redirect-verify-import-vulns');
        if (btn) btn.disabled = true;
        try {
            const response = await apiFetch('/api/vulnerabilities/export-urls');
            const result = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(result.error || ('HTTP ' + response.status));
            }
            const urls = normalizeImportedURLs(result.urls);
            if (!urls.length) {
                toast(tr('redirectVerifyPage.importVulnsEmpty', '既有漏洞没有可用的目标 URL'), 'info');
                return;
            }
            writeTargets(urls);
            toast(tr('redirectVerifyPage.importVulnsDone', '已汇入既有漏洞目标') + ': ' + urls.length, 'success');
        } catch (error) {
            console.error('failed to import vulnerability targets:', error);
            toast(tr('redirectVerifyPage.importVulnsFailed', '汇入既有漏洞失败') + ': ' +
                (error && error.message ? error.message : String(error)), 'error');
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    window.initRedirectVerifyPage = function initRedirectVerifyPage() {
        loadEndpoints();
        loadRuns();

        const groupSelect = $('redirect-verify-proxy-group');
        if (groupSelect && !groupSelect.dataset.bound) {
            groupSelect.dataset.bound = '1';
            groupSelect.addEventListener('change', syncProxyGroupInputs);
            syncProxyGroupInputs();
        }

        const importBtn = $('redirect-verify-import-vulns');
        if (importBtn && !importBtn.dataset.bound) {
            importBtn.dataset.bound = '1';
            importBtn.addEventListener('click', importVulnTargets);
        }
        const form = $('redirect-verify-form');
        if (form && !form.dataset.bound) {
            form.dataset.bound = '1';
            form.addEventListener('submit', startRun);
        }
        const cancelBtn = $('redirect-verify-cancel');
        if (cancelBtn && !cancelBtn.dataset.bound) {
            cancelBtn.dataset.bound = '1';
            cancelBtn.addEventListener('click', cancelRun);
        }
        const rewriteBtn = $('redirect-verify-rewrite-endpoints');
        if (rewriteBtn && !rewriteBtn.dataset.bound) {
            rewriteBtn.dataset.bound = '1';
            rewriteBtn.addEventListener('click', rewriteVulnerabilityEndpoints);
        }
        const searchBtn = $('redirect-verify-search-btn');
        if (searchBtn && !searchBtn.dataset.bound) {
            searchBtn.dataset.bound = '1';
            searchBtn.addEventListener('click', searchSeeds);
        }
        const crawlBtn = $('redirect-verify-crawl-btn');
        if (crawlBtn && !crawlBtn.dataset.bound) {
            crawlBtn.dataset.bound = '1';
            crawlBtn.addEventListener('click', runCrawl);
        }
        const implantBtn = $('redirect-verify-implant-btn');
        if (implantBtn && !implantBtn.dataset.bound) {
            implantBtn.dataset.bound = '1';
            implantBtn.addEventListener('click', buildImplant);
        }
        const implantKind = $('redirect-verify-implant-kind');
        if (implantKind && !implantKind.dataset.bound) {
            implantKind.dataset.bound = '1';
            implantKind.addEventListener('change', applyImplantEncodingOptions);
        }
        const injectionScanBtn = $('redirect-verify-injection-scan-btn');
        if (injectionScanBtn && !injectionScanBtn.dataset.bound) {
            injectionScanBtn.dataset.bound = '1';
            injectionScanBtn.addEventListener('click', () => scanInjections(false));
        }
        const injectionImplantBtn = $('redirect-verify-injection-implant-btn');
        if (injectionImplantBtn && !injectionImplantBtn.dataset.bound) {
            injectionImplantBtn.dataset.bound = '1';
            injectionImplantBtn.addEventListener('click', () => scanInjections(true));
        }
        loadImplantCapabilities();
        const refreshBtn = $('redirect-verify-refresh');
        if (refreshBtn && !refreshBtn.dataset.bound) {
            refreshBtn.dataset.bound = '1';
            refreshBtn.addEventListener('click', loadRuns);
        }
    };

    async function loadEndpoints() {
        const el = $('redirect-verify-endpoint');
        if (!el) return;
        try {
            const response = await apiFetch('/api/redirect-verify/endpoints');
            const result = await response.json().catch(() => ({}));
            if (!response.ok) return;
            const endpoints = Array.isArray(result.endpoints) ? result.endpoints : [];
            if (endpoints.length && !el.value.trim()) {
                el.value = endpoints[0];
            }
            const hint = $('redirect-verify-endpoint-hint');
            if (hint) {
                hint.textContent = endpoints.length
                    ? tr('redirectVerifyPage.endpointHintConfigured', '平台已配置受控端点：') + endpoints.join(', ')
                    : tr('redirectVerifyPage.endpointHintMissing', '平台尚未配置受控端点，请填写你的回连地址');
            }
        } catch (error) {
            console.error('failed to load controlled endpoints:', error);
        }
    }

    async function startRun(event) {
        if (event) event.preventDefault();
        const targets = readTargets();
        const seedSource = String((($('redirect-verify-seed-source') || {}).value) || 'manual').trim();
        const seedKeyword = String((($('redirect-verify-seed-keyword') || {}).value) || '').trim();
        if (seedSource === 'manual' && !targets.length) {
            toast(tr('redirectVerifyPage.needTargets', '请先提供至少一个目标 URL'), 'error');
            return;
        }
        if (seedSource !== 'manual' && !seedKeyword) {
            toast(tr('redirectVerifyPage.needSeedKeyword', '请填写分类关键字（例如 娛樂城、SEO、現金版）'), 'error');
            return;
        }
        const endpoint = ($('redirect-verify-endpoint') || {}).value || '';
        const endpointValue = String(endpoint).trim();
        if (!endpointValue) {
            toast(tr('redirectVerifyPage.needEndpoint', '请填写跳转目标（受控端点）'), 'error');
            return;
        }

        const body = {
            targets: targets,
            endpoints: [endpointValue],
            param: (($('redirect-verify-param') || {}).value || '').trim(),
            method: (($('redirect-verify-method') || {}).value || 'GET').trim(),
            project_id: (($('redirect-verify-project') || {}).value || '').trim(),
            proxy: proxyURLValue(),
            proxy_group: proxyGroupValue(),
            auto_record: !!($('redirect-verify-auto-record') || {}).checked,
            crawl: !!($('redirect-verify-auto-crawl') || {}).checked,
            seed_source: seedSource,
            seed_keyword: seedKeyword,
            encoding: String((($('redirect-verify-encoding') || {}).value) || 'none').trim()
        };
        const concurrency = parseInt((($('redirect-verify-concurrency') || {}).value) || '', 10);
        if (concurrency > 0) body.concurrency = concurrency;
        const seedLimit = parseInt((($('redirect-verify-seed-limit') || {}).value) || '', 10);
        if (seedLimit > 0) body.seed_limit = seedLimit;
        // 重複複測次數：留空＝不重複（預設）。大於 1 才量得到穩定度。
        const repeat = parseInt((($('redirect-verify-repeat') || {}).value) || '', 10);
        if (repeat > 1) body.repeat = Math.min(repeat, 5);
        // 巡站上限沿用「巡站發掘跳轉參數」那張卡的值，兩處是同一組設定。
        const crawlPages = parseInt((($('redirect-verify-crawl-pages') || {}).value) || '', 10);
        if (crawlPages > 0) body.crawl_max_pages = crawlPages;
        const crawlDepth = parseInt((($('redirect-verify-crawl-depth') || {}).value) || '', 10);
        if (crawlDepth >= 0) body.crawl_max_depth = crawlDepth;

        setStatus(tr('redirectVerifyPage.starting', '正在建立批次…'));
        try {
            const response = await apiFetch('/api/redirect-verify/runs', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body)
            });
            const result = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(result.error || ('HTTP ' + response.status));
            }
            currentRunId = (result.run && result.run.id) || '';
            lastReportId = currentRunId;
            setStatus(tr('redirectVerifyPage.running', '批次执行中…'));
            pollRun();
            loadRuns();
        } catch (error) {
            console.error('failed to create redirect verification run:', error);
            setStatus(tr('redirectVerifyPage.failed', '批次建立失败'));
            toast(tr('redirectVerifyPage.failed', '批次建立失败') + ': ' + (error && error.message ? error.message : String(error)), 'error');
        }
    }

    // buildImplant 產生帶著受控端點的植入片段（可用編碼形式）。
    // loadImplantCapabilities 取回「型態 × 編碼」相容矩陣。
    //
    // 為什麼要這張矩陣：meta refresh 的網址是瀏覽器直接解析的 URL，瀏覽器不會解
    // base64、不會解 \u0068 跳脫；query 參數也沒有人會解跳脫。硬送出這些組合
    // 只會得到一個不生效的載荷，所以前端直接把不相容的編碼停用。
    async function loadImplantCapabilities() {
        try {
            const response = await apiFetch('/api/redirect-verify/implant');
            const result = await response.json().catch(() => ({}));
            if (!response.ok) return;
            if (result && result.encodings_by_kind) {
                implantEncodingsByKind = result.encodings_by_kind;
            }
            applyImplantEncodingOptions();
        } catch (error) {
            console.error('failed to load implant capabilities:', error);
        }
    }

    // applyImplantEncodingOptions 依目前選的型態，停用不相容的編碼選項。
    function applyImplantEncodingOptions() {
        const kindSelect = $('redirect-verify-implant-kind');
        const encodingSelect = $('redirect-verify-implant-encoding');
        const hint = $('redirect-verify-implant-encoding-hint');
        if (!kindSelect || !encodingSelect) return;
        const kind = String(kindSelect.value || 'js_redirect').trim();
        const allowed = implantEncodingsByKind && implantEncodingsByKind[kind];
        if (!Array.isArray(allowed)) {
            if (hint) hint.textContent = '';
            return;
        }
        let blocked = 0;
        Array.prototype.forEach.call(encodingSelect.options, function (option) {
            const ok = allowed.indexOf(option.value) >= 0;
            option.disabled = !ok;
            option.hidden = !ok;
            if (!ok) blocked += 1;
        });
        if (encodingSelect.selectedOptions && encodingSelect.selectedOptions[0]) {
            if (encodingSelect.selectedOptions[0].disabled) {
                encodingSelect.value = allowed[0] || 'none';
            }
        }
        if (hint) {
            hint.textContent = blocked
                ? tr('redirectVerifyPage.implantEncodingLimited',
                    '此載荷型態不支援部分編碼（目標不會解碼），已停用。')
                : '';
        }
    }

    async function buildImplant() {
        const out = $('redirect-verify-implant-out');
        const endpoint = String((($('redirect-verify-endpoint') || {}).value) || '').trim();
        const kind = String((($('redirect-verify-implant-kind') || {}).value) || 'js_redirect').trim();
        const encoding = String((($('redirect-verify-implant-encoding') || {}).value) || 'none').trim();
        const param = String((($('redirect-verify-implant-param') || {}).value) || '').trim();
        try {
            const response = await apiFetch('/api/redirect-verify/implant', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ endpoint: endpoint, kind: kind, encoding: encoding, param: param })
            });
            const result = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(result.error || ('HTTP ' + response.status));
            }
            const implant = result.implant || {};
            if (out) {
                out.textContent = implant.fragment || '';
            }
            toast(tr('redirectVerifyPage.implantDone', '載荷已產生'), 'success');
        } catch (error) {
            console.error('failed to build implant:', error);
            if (out) out.textContent = '';
            toast(tr('redirectVerifyPage.implantFailed', '載荷產生失敗') + ': ' +
                (error && error.message ? error.message : String(error)), 'error');
        }
    }

    // scanInjections 掃描頁面裡「他們塞的」外部網址，並可一併產生替換片段。
    //
    // withImplant = true 時會順帶把每個注入點換成我們的受控端點，產生可直接貼用的片段。
    // 平台只讀不改：實際寫進受控站頁面是操作者自己的動作。
    async function scanInjections(withImplant) {
        const pageUrl = String((($('redirect-verify-injection-url') || {}).value) || '').trim();
        if (!pageUrl) {
            toast(tr('redirectVerifyPage.injectionNeedUrl', '请填写要扫描的页面 URL'), 'error');
            return;
        }
        const endpoint = String((($('redirect-verify-endpoint') || {}).value) || '').trim();
        const encoding = String((($('redirect-verify-injection-encoding') || {}).value) || 'none').trim();
        const meta = $('redirect-verify-injection-meta');
        if (meta) meta.textContent = tr('redirectVerifyPage.injectionScanning', '扫描中…');
        try {
            const response = await apiFetch('/api/redirect-verify/injections', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: pageUrl,
                    endpoint: endpoint,
                    encoding: encoding,
                    proxy: proxyURLValue(),
                    proxy_group: proxyGroupValue(),
                    with_implant: !!withImplant,
                    verify_endpoint: !!withImplant
                })
            });
            const result = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(result.error || ('HTTP ' + response.status));
            }
            renderInjections(result);
            const count = result.injection_count || 0;
            if (meta) {
                meta.textContent = tr('redirectVerifyPage.injectionScanDone', '扫描完成') + ' · ' +
                    tr('redirectVerifyPage.injectionCount', '注入点') + ' ' + count + ' · ' +
                    tr('redirectVerifyPage.injectionThirdParty', '第三方') + ' ' +
                    (result.third_party_injections || 0);
            }
            toast(tr('redirectVerifyPage.injectionScanDone', '扫描完成') + ': ' + count, 'success');
        } catch (error) {
            console.error('failed to scan injections:', error);
            if (meta) meta.textContent = tr('redirectVerifyPage.injectionScanFailed', '扫描失败');
            toast(tr('redirectVerifyPage.injectionScanFailed', '扫描失败') + ': ' +
                (error && error.message ? error.message : String(error)), 'error');
        }
    }

    // renderInjections 畫出注入點清單與對應的替換片段。
    function renderInjections(payload) {
        const box = $('redirect-verify-injections');
        if (!box) return;
        const points = Array.isArray(payload.injections) ? payload.injections : [];
        const implants = Array.isArray(payload.implants) ? payload.implants : [];
        if (!points.length) {
            box.innerHTML = '<div class="redirect-verify-empty">' +
                esc(tr('redirectVerifyPage.injectionEmpty', '没有找到注入点')) + '</div>';
            return;
        }
        // 片段依「原始網址」對回注入點（後端回傳順序一致，但用 URL 對應比較穩）。
        const implantByURL = {};
        implants.forEach((item) => {
            const key = item && item.original ? String(item.original) : '';
            if (key) implantByURL[key] = item;
        });
        const check = payload.endpoint_check || null;
        const blocks = points.map((point) => {
            const implant = implantByURL[point.url] || null;
            const fragment = implant && implant.fragment ? implant.fragment : '';
            const note = implant && implant.note ? implant.note : '';
            return '<div class="redirect-verify-injection">' +
                '<div class="redirect-verify-injection-head">' +
                '<span class="redirect-verify-badge redirect-verify-badge--kind">' + esc(point.kind || '') + '</span>' +
                (point.self_host
                    ? '<span class="redirect-verify-badge">' + esc(tr('redirectVerifyPage.injectionSelfHost', '站方自有')) + '</span>'
                    : '<span class="redirect-verify-badge redirect-verify-badge--warn">' +
                      esc(tr('redirectVerifyPage.injectionThirdPartyBadge', '第三方注入')) + '</span>') +
                '</div>' +
                '<div class="redirect-verify-injection-url">' + esc(point.url || '') + '</div>' +
                (point.context ? '<div class="redirect-verify-injection-context">' + esc(point.context) + '</div>' : '') +
                (fragment ? '<pre class="redirect-verify-implant-out">' + esc(fragment) + '</pre>' : '') +
                (note ? '<div class="redirect-verify-hint">' + esc(note) + '</div>' : '') +
                '</div>';
        });
        const checkBlock = check
            ? '<div class="redirect-verify-injection-check' + (check.suitable ? '' : ' redirect-verify-injection-check--bad') + '">' +
              '<strong>' + esc(tr('redirectVerifyPage.endpointCheck', '受控端点检查')) + ':</strong> ' +
              esc(check.reachable
                  ? tr('redirectVerifyPage.endpointReachable', '可达') + ' HTTP ' + (check.status || '')
                  : tr('redirectVerifyPage.endpointUnreachable', '不可达')) +
              (check.note ? ' · ' + esc(check.note) : '') +
              '</div>'
            : '';
        box.innerHTML = checkBlock + blocks.join('');
    }

    async function cancelRun() {        if (!currentRunId) {
            toast(tr('redirectVerifyPage.noRun', '没有进行中的批次'), 'error');
            return;
        }
        try {
            const response = await apiFetch('/api/redirect-verify/runs/' + encodeURIComponent(currentRunId) + '/cancel', {
                method: 'POST'
            });
            const result = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(result.error || ('HTTP ' + response.status));
            }
            setStatus(tr('redirectVerifyPage.cancelling', '正在取消…'));
        } catch (error) {
            console.error('failed to cancel run:', error);
            toast(tr('redirectVerifyPage.cancelFailed', '取消失败') + ': ' + (error && error.message ? error.message : String(error)), 'error');
        }
    }

    function pollRun() {
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(async () => {
            if (!currentRunId) {
                if (pollTimer) clearInterval(pollTimer);
                pollTimer = null;
                return;
            }
            try {
                const response = await apiFetch('/api/redirect-verify/runs/' + encodeURIComponent(currentRunId));
                const result = await response.json().catch(() => ({}));
                if (!response.ok) return;
                renderRun(result);
                const status = (result.run && result.run.status) || '';
                if (status === 'completed' || status === 'cancelled' || status === 'failed') {
                    if (pollTimer) clearInterval(pollTimer);
                    pollTimer = null;
                    loadRuns();
                }
            } catch (error) {
                console.error('failed to poll run progress:', error);
            }
        }, 1500);
    }

    function renderRun(payload) {
        const run = payload.run || {};
        const results = Array.isArray(payload.results) ? payload.results : [];
        renderProgress(run, results);
        renderResults(results);
        renderAccuracy(payload.accuracy);
    }

    // renderAccuracy 畫出「實不實、精不精準」的摘要。
    //
    // 三個數字要分開看：
    //   - 真跳轉 vs 本文回顯：回顯是偽陽性來源，不算確認。
    //   - 命中原有參數 vs 猜參數：命中原有參數才是抓到站上真的跳轉路徑。
    //   - 穩定率：只算真的有重複探測的目標。
    function renderAccuracy(accuracy) {
        const box = $('redirect-verify-accuracy');
        if (!box) return;
        if (!accuracy) {
            box.innerHTML = '<div class="redirect-verify-empty">' +
                esc(tr('redirectVerifyPage.accuracyEmpty', '尚未开始')) + '</div>';
            return;
        }
        const tiles = [
            {
                label: tr('redirectVerifyPage.accuracyLocation', '真跳轉'),
                value: String(accuracy.location_evidence || 0),
                note: tr('redirectVerifyPage.accuracyLocationNote', '3xx Location 指向受控端點')
            },
            {
                label: tr('redirectVerifyPage.accuracyBodyEcho', '本文回顯'),
                value: String(accuracy.body_echo || 0),
                note: tr('redirectVerifyPage.accuracyBodyEchoNote', '偽陽性來源，不計入確認')
            },
            {
                label: tr('redirectVerifyPage.accuracyFalsePositive', '偽陽性率'),
                value: formatPercent(accuracy.false_positive_rate),
                note: tr('redirectVerifyPage.accuracyFalsePositiveNote', '看起來像跳轉其實不是')
            },
            {
                label: tr('redirectVerifyPage.accuracyOwnParam', '命中原有參數'),
                value: String(accuracy.own_param_hit || 0) + ' / ' + formatPercent(accuracy.own_param_hit_rate),
                note: tr('redirectVerifyPage.accuracyOwnParamNote', '抓到站上真的跳轉路徑')
            },
            {
                label: tr('redirectVerifyPage.accuracyGuessParam', '靠猜參數命中'),
                value: String(accuracy.guess_param_hit || 0) + ' / ' + formatPercent(accuracy.guess_param_hit_rate),
                note: tr('redirectVerifyPage.accuracyGuessParamNote', '站上接受任意參數名')
            },
            {
                label: tr('redirectVerifyPage.accuracyStability', '穩定率'),
                value: (accuracy.repeated || 0) > 0
                    ? formatPercent(accuracy.stability_rate)
                    : tr('redirectVerifyPage.accuracyStabilityOff', '未啟用'),
                note: (accuracy.repeated || 0) > 0
                    ? tr('redirectVerifyPage.accuracyStabilityNote', '重複複測') + ' ' + accuracy.repeated + ' ' +
                      tr('redirectVerifyPage.accuracyStabilityNoteUnit', '個目標')
                    : tr('redirectVerifyPage.accuracyStabilityOffNote', '單次命中可能是巧合')
            }
        ];
        box.innerHTML = tiles.map((tile) =>
            '<div class="redirect-verify-tile">' +
            '<span class="redirect-verify-tile-label">' + esc(tile.label) + '</span>' +
            '<span class="redirect-verify-tile-value">' + esc(tile.value) + '</span>' +
            '<span class="redirect-verify-tile-note">' + esc(tile.note) + '</span>' +
            '</div>').join('');
    }

    // formatPercent 把比率格式化成百分比字串。
    function formatPercent(value) {
        const num = Number(value);
        if (!isFinite(num)) return '0%';
        return num.toFixed(1) + '%';
    }

    function renderProgress(run, results) {
        const total = run.total || 0;
        const completed = run.completed || 0;
        const confirmed = run.confirmed || 0;
        const bar = $('redirect-verify-progress-bar');
        if (bar) {
            const percent = total > 0 ? Math.min(100, Math.round((completed / total) * 100)) : 0;
            bar.style.width = percent + '%';
        }
        const text = $('redirect-verify-progress-text');
        if (text) {
            text.textContent = tr('redirectVerifyPage.progress', '进度') + ' ' + completed + '/' + total +
                ' · ' + tr('redirectVerifyPage.confirmedCount', '确认') + ' ' + confirmed;
        }
        const statusEl = $('redirect-verify-status');
        if (statusEl) {
            const status = run.status || '';
            const label = {
                pending: tr('redirectVerifyPage.statusPending', '等待中'),
                running: tr('redirectVerifyPage.statusRunning', '执行中'),
                completed: tr('redirectVerifyPage.statusCompleted', '已完成'),
                cancelled: tr('redirectVerifyPage.statusCancelled', '已取消'),
                failed: tr('redirectVerifyPage.statusFailed', '失败')
            }[status] || status;
            statusEl.textContent = label + ' · ' + completed + '/' + total +
                ' · ' + tr('redirectVerifyPage.confirmedCount', '确认') + ' ' + confirmed;
        }
        const reportLink = $('redirect-verify-report-link');
        if (reportLink && run.id) {
            reportLink.href = '/api/redirect-verify/runs/' + encodeURIComponent(run.id) + '/report?format=markdown';
            reportLink.hidden = false;
        }
    }

    function renderResults(results) {
        const body = $('redirect-verify-results');
        if (!body) return;
        if (!results.length) {
            body.innerHTML = '<tr><td colspan="10" class="redirect-verify-empty">' +
                esc(tr('redirectVerifyPage.noResults', '暂无结果')) + '</td></tr>';
            return;
        }
        const rows = results.map((item) => {
            const verdict = item.confirmed
                ? '<span class="redirect-verify-badge redirect-verify-badge--hit">' + esc(tr('redirectVerifyPage.confirmed', '已确认')) + '</span>'
                : '<span class="redirect-verify-badge">' + esc(tr('redirectVerifyPage.notConfirmed', '未确认')) + '</span>';
            const vuln = item.vulnerability_id
                ? '<a href="/vulnerabilities/' + encodeURIComponent(item.vulnerability_id) + '">' + esc(item.vulnerability_id) + '</a>'
                : '—';
            // 「站上原有跳轉參數」為空代表這個目標網址本身沒有跳轉參數，
            // 這筆是用猜的參數名盲試的 —— 兩者成敗意義完全不同，必須分開顯示。
            const own = item.own_param
                ? '<code>' + esc(item.own_param) + '</code>' +
                  (item.own_param_hit
                      ? ' <span class="redirect-verify-badge redirect-verify-badge--hit">' +
                        esc(tr('redirectVerifyPage.ownParamHit', '命中')) + '</span>'
                      : '')
                : '<span class="redirect-verify-muted">—</span>';
            const tried = Array.isArray(item.params_tried) ? item.params_tried.length : 0;
            const triedCell = tried > 0
                ? String(tried) + ' <span class="redirect-verify-muted">' +
                  esc(tr('redirectVerifyPage.paramsTriedUnit', '次')) + '</span>'
                : '—';
            const evidenceCell = renderEvidence(item);
            const stableCell = (item.attempts || 0) > 1
                ? (item.stable
                    ? '<span class="redirect-verify-badge redirect-verify-badge--hit">' +
                      esc(tr('redirectVerifyPage.stableYes', '一致')) + '</span>'
                    : '<span class="redirect-verify-badge redirect-verify-badge--warn">' +
                      esc(tr('redirectVerifyPage.stableNo', '不一致')) + '</span>')
                : '<span class="redirect-verify-muted">—</span>';
            return '<tr>' +
                '<td class="redirect-verify-cell-url">' + esc(item.url) + '</td>' +
                '<td>' + verdict + '</td>' +
                '<td>' + evidenceCell + '</td>' +
                '<td>' + own + '</td>' +
                '<td>' + esc(item.param || '—') + '</td>' +
                '<td>' + triedCell + '</td>' +
                '<td>' + esc(item.status || '') + '</td>' +
                '<td>' + stableCell + '</td>' +
                '<td class="redirect-verify-cell-loc">' + esc(item.location || '') + '</td>' +
                '<td>' + vuln + '</td>' +
                '</tr>';
        });
        body.innerHTML = rows.join('');
    }

    // renderEvidence 把證據等級翻成看得懂的標籤。
    //
    // location = 伺服器真的 3xx 跳轉；body_echo = 只是本文回顯（偽陽性來源）。
    // 沒有分級的時候，「本文有受控端點字串」會被誤認成跳轉 —— 這裡要把兩者分開。
    function renderEvidence(item) {
        const level = String(item.evidence || '').trim();
        if (level === 'location') {
            return '<span class="redirect-verify-badge redirect-verify-badge--hit">' +
                esc(tr('redirectVerifyPage.evidenceLocation', '真跳轉')) + '</span>';
        }
        if (level === 'body_echo' || item.body_echo) {
            return '<span class="redirect-verify-badge redirect-verify-badge--warn">' +
                esc(tr('redirectVerifyPage.evidenceBodyEcho', '僅回顯')) + '</span>';
        }
        return '<span class="redirect-verify-muted">—</span>';
    }

    async function loadRuns() {
        const list = $('redirect-verify-runs');
        if (!list) return;
        try {
            const response = await apiFetch('/api/redirect-verify/runs?limit=20');
            const result = await response.json().catch(() => ({}));
            if (!response.ok) return;
            const runs = Array.isArray(result.runs) ? result.runs : [];
            if (!runs.length) {
                list.innerHTML = '<div class="redirect-verify-empty">' + esc(tr('redirectVerifyPage.noRuns', '暂无批次')) + '</div>';
                return;
            }
            list.innerHTML = runs.map((run) => {
                const id = esc(run.id);
                const time = run.created_at ? String(run.created_at).replace('T', ' ').slice(0, 19) : '';
                return '<button type="button" class="redirect-verify-run" data-run-id="' + id + '">' +
                    '<span class="redirect-verify-run-time">' + esc(time) + '</span>' +
                    '<span class="redirect-verify-run-count">' + esc(run.confirmed || 0) + '/' + esc(run.total || 0) + '</span>' +
                    '<span class="redirect-verify-run-status">' + esc(run.status || '') + '</span>' +
                    '</button>';
            }).join('');
            list.querySelectorAll('.redirect-verify-run').forEach((button) => {
                button.addEventListener('click', () => {
                    currentRunId = button.getAttribute('data-run-id') || '';
                    lastReportId = currentRunId;
                    pollRun();
                });
            });
        } catch (error) {
            console.error('failed to load verification runs:', error);
        }
    }

    // extractHosts 從情蒐結果取出主機名。
    // 對外暴露一份，方便測試直接驗證這段解析（匯入的目標清單全靠它）。
    function extractHosts(results) {
        const hosts = [];
        const seen = new Set();
        (results || []).forEach((item) => {
            const candidates = [item.host, item.hostname, item.domain, item.hostnames, item.domains, item.ip, item.ip_str];
            candidates.forEach((value) => {
                const list = Array.isArray(value) ? value : [value];
                list.forEach((entry) => {
                    const host = String(entry == null ? '' : entry).split(',')[0].trim();
                    if (!host || seen.has(host)) return;
                    seen.add(host);
                    hosts.push(host);
                });
            });
        });
        return hosts;
    }

    async function searchSeeds() {
        const provider = (($('redirect-verify-provider') || {}).value || 'fofa').trim();
        const query = (($('redirect-verify-query') || {}).value || '').trim();
        if (!query) {
            toast(tr('redirectVerifyPage.needQuery', '请输入搜索表达式'), 'error');
            return;
        }
        const size = parseInt((($('redirect-verify-size') || {}).value) || '', 10) || 100;
        const meta = $('redirect-verify-search-meta');
        if (meta) meta.textContent = tr('redirectVerifyPage.searching', '搜索中…');
        try {
            const response = await apiFetch('/api/fofa/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ provider: provider, query: query, size: size, page: 1 })
            });
            const result = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(result.error || ('HTTP ' + response.status));
            }
            const hosts = extractHosts(result.results);
            writeTargets(hosts);
            if (meta) {
                meta.textContent = tr('redirectVerifyPage.searchDone', '已汇入') + ' ' + hosts.length + ' ' +
                    tr('redirectVerifyPage.hosts', '个主機');
            }
            toast(tr('redirectVerifyPage.imported', '已汇入目标清单') + ': ' + hosts.length, 'success');
        } catch (error) {
            console.error('failed to run recon search:', error);
            if (meta) meta.textContent = tr('redirectVerifyPage.searchFailed', '搜索失败');
            toast(tr('redirectVerifyPage.searchFailed', '搜索失败') + ': ' + (error && error.message ? error.message : String(error)), 'error');
        }
    }

    async function runCrawl() {
        const seeds = readTargets();
        if (!seeds.length) {
            toast(tr('redirectVerifyPage.needTargets', '请先提供至少一个目标 URL'), 'error');
            return;
        }
        const maxPages = parseInt((($('redirect-verify-crawl-pages') || {}).value) || '', 10) || 10;
        const maxDepth = parseInt((($('redirect-verify-crawl-depth') || {}).value) || '', 10) || 1;
        const meta = $('redirect-verify-crawl-meta');
        if (meta) meta.textContent = tr('redirectVerifyPage.crawling', '巡站中…');
        try {
            const response = await apiFetch('/api/redirect-verify/crawl', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    seeds: seeds,
                    max_pages: maxPages,
                    max_depth: maxDepth,
                    same_host_only: true,
                    proxy: proxyURLValue(),
                    proxy_group: proxyGroupValue()
                })
            });
            const result = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(result.error || ('HTTP ' + response.status));
            }
            const candidates = Array.isArray(result.candidates) ? result.candidates : [];
            writeTargets(candidates);
            if (meta) {
                meta.textContent = tr('redirectVerifyPage.crawlDone', '巡站完成') + ' ' +
                    (result.pages_visited || 0) + ' ' + tr('redirectVerifyPage.pages', '頁') +
                    ' · ' + tr('redirectVerifyPage.candidates', '候选') + ' ' + candidates.length;
            }
            toast(tr('redirectVerifyPage.imported', '已汇入目标清单') + ': ' + candidates.length, 'success');
        } catch (error) {
            console.error('failed to crawl targets:', error);
            if (meta) meta.textContent = tr('redirectVerifyPage.crawlFailed', '巡站失败');
            toast(tr('redirectVerifyPage.crawlFailed', '巡站失败') + ': ' + (error && error.message ? error.message : String(error)), 'error');
        }
    }

    window.extractRedirectVerifyHosts = extractHosts;
    window.extractRedirectVerifyURLs = normalizeImportedURLs;
    // 證據分級與比率格式化也對外暴露一份，方便測試直接驗證這段判定
    // （真跳轉與僅回顯的差別是整條流水線最容易出錯的地方）。
    window.renderRedirectVerifyEvidence = renderEvidence;
    window.formatRedirectVerifyPercent = formatPercent;

    // rewriteVulnerabilityEndpoints 把既有漏洞記錄裡 payload 位置的回連網址
    // 換成受控端點，讓整批紀錄可以用同一組端點重跑。
    async function rewriteVulnerabilityEndpoints() {
        const endpoint = String((($('redirect-verify-endpoint') || {}).value) || '').trim();
        if (!endpoint) {
            toast(tr('redirectVerifyPage.rewriteNeedEndpoint', '請先填寫跳轉目標（受控端點）'), 'error');
            return;
        }
        const confirmText = tr('redirectVerifyPage.rewriteConfirm', '將把漏洞記錄中 payload 位置的回連網址換成 {endpoint}，確定執行？')
            .replace('{endpoint}', endpoint);
        if (!window.confirm(confirmText)) return;
        const btn = $('redirect-verify-rewrite-endpoints');
        if (btn) btn.disabled = true;
        try {
            const response = await apiFetch('/api/vulnerabilities/rewrite-controlled-endpoints', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    endpoint: endpoint,
                    dry_run: false,
                    project_id: (($('redirect-verify-project') || {}).value || '').trim()
                })
            });
            const result = await response.json().catch(() => ({}));
            if (!response.ok) {
                throw new Error(result.error || ('HTTP ' + response.status));
            }
            const summary = tr('redirectVerifyPage.rewriteDone', '已改寫 {changed} 筆（掃描 {scanned} 筆，替換 {replaced} 個網址）')
                .replace('{changed}', String(result.changed || 0))
                .replace('{scanned}', String(result.scanned || 0))
                .replace('{replaced}', String(result.replaced_total || 0));
            toast(summary, 'success');
            setStatus(summary);
        } catch (error) {
            console.error('failed to rewrite vulnerability endpoints:', error);
            toast(tr('redirectVerifyPage.rewriteFailed', '批次改寫失敗') + ': ' +
                (error && error.message ? error.message : String(error)), 'error');
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    window.downloadRedirectVerifyReport = function downloadRedirectVerifyReport(format) {
        const runId = currentRunId || lastReportId;
        if (!runId) {
            toast(tr('redirectVerifyPage.noRun', '没有进行中的批次'), 'error');
            return;
        }
        const target = format === 'csv' ? 'csv' : 'markdown';
        window.location.href = '/api/redirect-verify/runs/' + encodeURIComponent(runId) + '/report?format=' + target;
    };
})();
