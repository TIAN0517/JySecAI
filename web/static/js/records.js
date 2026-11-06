/* ==========================================================================
   records.js — 提取記錄管理主控台（真實資料，分類 + 分頁 + 去重後的欄位化表格）
   --------------------------------------------------------------------------
   這一頁是「掃描器抽到的東西」的統一落點：貸款案件、快遞訂單、帳號憑證、
   資產指紋、風險漏洞、聯絡資料各佔一個分類頁籤，每個頁籤的欄位由型別定義
   決定（/api/records/types），資料裡有、但定義沒列出的欄位也會補在表格後段
   —— 表格不會漏欄位。

   原則：畫面上每一格都來自 API 的真實回應。沒有資料就顯示空狀態，
        絕不顯示示範列或 0 值假象。
   ========================================================================== */

(function () {
    'use strict';

    const state = {
        type: '',
        dataset: '',
        facet: '',
        q: '',
        page: 1,
        pageSize: 50,
        total: 0,
        types: [],
        datasets: [],
        columns: [],
        hidden: {},          // columnKey -> true 表示使用者收合（目前型別）
        hiddenByType: {},    // typeId -> {columnKey: true}，切換型別時各自記住
        sortBy: '',          // 排序欄位 key（型別宣告過的欄位）
        sortDir: 'desc',
        loaded: false
    };

    const $ = (id) => document.getElementById(id);

    function esc(v) {
        if (v === null || v === undefined) return '';
        return String(v)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function t(key, fallback) {
        // i18n 的正確用法：window.uiT(key, fallback)。
        // window.t 在語言包沒載入或查不到時會「回傳 key 本身」，
        // 畫面就會出現 records.rowNo 這種原始鍵 —— 所以優先走 uiT。
        if (typeof window !== 'undefined') {
            if (typeof window.uiT === 'function') {
                const v = window.uiT(key, fallback);
                if (v) return v;
            }
            if (typeof window.t === 'function') {
                const v = window.t(key);
                if (v && v !== key) return v;
            }
        }
        return fallback;
    }

    function fmtNum(v) {
        if (v === null || v === undefined || v === '') return '-';
        const n = Number(v);
        if (!isFinite(n)) return esc(v);
        // 四位數落在年份區間 → 不加千分位（2014 不該變成 2,014）
        if (Number.isInteger(n) && n >= 1900 && n <= 2100 && String(Math.abs(n)).length === 4) {
            return esc(String(n));
        }
        return n.toLocaleString('zh-TW');
    }

    function fmtMoney(v) {
        if (v === null || v === undefined || v === '') return '-';
        const n = Number(v);
        if (!isFinite(n)) return esc(v);
        return n.toLocaleString('zh-TW');
    }

    function fmtCell(v, kind) {
        // 空值顯示「-」而不是空白：空白看起來像壞掉，「-」看起來像「此筆沒有這個欄位」
        if (v === null || v === undefined || v === '') return '<span class="muted">-</span>';
        if (kind === 'money') return esc(fmtMoney(v));
        if (kind === 'int') return esc(fmtNum(v));
        return esc(v);
    }

    async function getJSON(url) {
        const res = await window.apiFetch(url);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
    }

    // ------------------------------------------------------------ 型別頁籤
    function renderTypeTabs() {
        const box = $('records-types');
        if (!box) return;
        if (!state.types.length) {
            box.innerHTML = '<div class="loan-empty">' + esc(t('records.noTypes', '（尚未定義任何記錄型別）')) + '</div>';
            return;
        }
        box.innerHTML = state.types.map(function (ty) {
            const active = ty.id === state.type ? ' active' : '';
            const count = ty.count || 0;
            const badge = count > 0
                ? '<span class="loan-total">' + fmtNum(count) + '</span>'
                : '<span class="loan-total muted">' + esc(t('records.noData', '無資料')) + '</span>';
            return '<button type="button" class="records-type-tab' + active + '" data-type="' + esc(ty.id) + '" ' +
                'title="' + esc(ty.description || '') + '">' +
                (ty.icon ? '<span class="records-type-icon">' + esc(ty.icon) + '</span>' : '') +
                '<span class="records-type-label">' + esc(ty.label) + '</span>' + badge +
                '</button>';
        }).join('');
        box.querySelectorAll('[data-type]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                state.type = btn.getAttribute('data-type');
                state.facet = '';
                state.page = 1;
                const ds = defaultSort();
                state.sortBy = ds.by;
                state.sortDir = ds.dir;
                loadRecords();
            });
        });
    }

    // ------------------------------------------------------------ 欄位定義
    function currentColumns() {
        const def = state.types.find(function (ty) { return ty.id === state.type; });
        if (!def) return [];
        return def.columns || [];
    }

    function currentDef() {
        return state.types.find(function (ty) { return ty.id === state.type; });
    }

    // 欄位有值率（後端 /api/records/types 回傳的 fill）
    function fillOf(key) {
        const def = currentDef();
        const fill = (def && def.fill) || {};
        return typeof fill[key] === 'number' ? fill[key] : null;
    }

    function typeTotal() {
        const def = currentDef();
        return (def && def.count) || 0;
    }

    // 預設隱藏「整個型別都沒有值」的欄位：那些欄位一定是空白，只會讓畫面看起來像沒資料。
    //
    // 注意：後端的 fill 只列出「資料裡真的出現過的欄位」，
    // 所以「沒有出現在 fill 裡」＝有值 0 筆，要跟 0 筆同樣處理。
    function defaultHidden() {
        const hidden = {};
        const total = typeTotal();
        if (!total) return hidden;
        currentColumns().forEach(function (c) {
            const f = fillOf(c.key);
            if (f === null || f === 0) hidden[c.key] = true;
        });
        return hidden;
    }

    function ensureHidden() {
        const store = state.hiddenByType || (state.hiddenByType = {});
        if (!store[state.type]) {
            store[state.type] = defaultHidden();
        }
        state.hidden = store[state.type];
    }

    // 可排序欄位：日期類欄位優先（最新在前），其餘用 key 排序
    function sortOptions() {
        const def = currentDef();
        if (!def) return [];
        const total = typeTotal();
        const opts = (def.columns || []).map(function (c) {
            const f = fillOf(c.key);
            return {
                key: c.key,
                label: c.label,
                kind: c.kind,
                fill: f === null ? 0 : f,
                pct: total ? Math.round(100 * f / total) : 0
            };
        }).filter(function (o) {
            return o.fill > 0;
        });
        // 日期欄位排前面
        opts.sort(function (a, b) {
            const ad = (a.kind === 'date' || /日期|時間|date|time|_at$/.test(a.key)) ? 0 : 1;
            const bd = (b.kind === 'date' || /日期|時間|date|time|_at$/.test(b.key)) ? 0 : 1;
            if (ad !== bd) return ad - bd;
            return b.fill - a.fill;
        });
        return opts;
    }

    function defaultSort() {
        const opts = sortOptions();
        if (!opts.length) return { by: '', dir: 'desc' };
        const dated = opts.find(function (o) {
            return o.kind === 'date' || /日期|時間|date|time|_at$/.test(o.key);
        });
        const pick = dated || opts[0];
        return { by: pick.key, dir: 'desc' };
    }

    function renderColumnControls() {
        const box = $('records-columns');
        if (!box) return;
        const cols = currentColumns();
        if (!cols.length) {
            box.innerHTML = '<span class="muted">' + esc(t('records.noColumns', '（請先選擇一個分類）')) + '</span>';
            return;
        }
        ensureHidden();
        const total = typeTotal();
        const pct = function (key) {
            const f = fillOf(key);
            if (!total) return '';
            return Math.round(100 * (f === null ? 0 : f) / total);
        };
        let h = '<span class="records-columns-title">' + esc(t('records.columns', '顯示欄位')) + '</span>';
        cols.forEach(function (c) {
            const off = state.hidden[c.key] ? ' off' : '';
            const p = pct(c.key);
            const title = p === '' ? '' : (' · ' + p + '% 有值（' + (fillOf(c.key)) + '/' + total + '）');
            h += '<button type="button" class="records-col-toggle' + off + '" data-col="' + esc(c.key) + '"' +
                (title ? ' title="' + esc(c.label + title) + '"' : '') + '>' +
                esc(c.label) + (p === '' ? '' : '<small class="records-col-pct">' + p + '%</small>') +
                '</button>';
        });
        h += '<button type="button" class="records-col-toggle reset" data-col="__all__">' +
            esc(t('records.showAll', '全部顯示')) + '</button>';

        // 排序選單：資料是依匯入順序寫入的，固定排序會讓第一頁落在最舊的一批
        const sopts = sortOptions();
        if (sopts.length) {
            h += '<select id="records-sort" class="records-facet-select" title="' +
                esc(t('records.sort', '排序')) + '">';
            sopts.forEach(function (o) {
                const sel = (state.sortBy === o.key) ? ' selected' : '';
                h += '<option value="' + esc(o.key) + '|' + esc(state.sortDir || 'desc') + '"' + sel + '>' +
                    esc(o.label) + '（' + o.pct + '%）</option>';
            });
            h += '</select>';
        }
        box.innerHTML = h;

        box.querySelectorAll('[data-col]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const key = btn.getAttribute('data-col');
                if (key === '__all__') {
                    state.hidden = {};
                    (state.hiddenByType || (state.hiddenByType = {}))[state.type] = {};
                } else {
                    state.hidden[key] = !state.hidden[key];
                    (state.hiddenByType || (state.hiddenByType = {}))[state.type] = state.hidden;
                }
                renderColumnControls();
                renderTable(state.lastItems || []);
            });
        });
        const sortSel = $('records-sort');
        if (sortSel) {
            sortSel.addEventListener('change', function () {
                const parts = sortSel.value.split('|');
                state.sortBy = parts[0] || '';
                state.sortDir = parts[1] || 'desc';
                state.page = 1;
                loadRecords();
            });
        }
    }

    // ------------------------------------------------------------ 表格
    function renderTable(items) {
        const box = $('records-table');
        if (!box) return;
        const def = state.types.find(function (ty) { return ty.id === state.type; });
        if (!def) {
            box.innerHTML = '<div class="loan-empty">' + esc(t('records.pickType', '請選擇一個分類')) + '</div>';
            return;
        }
        const declared = def.columns || [];
        // 資料裡出現、但型別定義沒列出的欄位也補上去 —— 表格不漏欄位。
        const extra = [];
        const seen = {};
        declared.forEach(function (c) { seen[c.key] = true; });
        (items || []).forEach(function (it) {
            Object.keys(it.fields || {}).forEach(function (k) {
                if (!seen[k]) { seen[k] = true; extra.push(k); }
            });
        });
        const extraCols = extra.map(function (k) {
            return { key: k, label: k, kind: 'text' };
        });
        const allCols = declared.concat(extraCols).filter(function (c) { return !state.hidden[c.key]; });

        if (!items || !items.length) {
            box.innerHTML = '<div class="loan-empty">' + esc(t('records.noRows', '（查無資料）')) + '</div>';
            return;
        }
        let h = '<div class="records-table-scroll"><table class="loan-table records-table"><thead><tr>';
        h += '<th>' + esc(t('records.rowNo', '#')) + '</th>';
        allCols.forEach(function (c) { h += '<th>' + esc(c.label) + '</th>'; });
        h += '<th>' + esc(t('records.hitCount', '命中')) + '</th>';
        h += '</tr></thead><tbody>';
        items.forEach(function (it, idx) {
            h += '<tr>';
            h += '<td class="muted">' + ((state.page - 1) * state.pageSize + idx + 1) + '</td>';
            allCols.forEach(function (c) {
                h += '<td>' + fmtCell((it.fields || {})[c.key], c.kind) + '</td>';
            });
            h += '<td class="muted">' + fmtNum(it.hit_count) + '</td>';
            h += '</tr>';
        });
        h += '</tbody></table></div>';
        box.innerHTML = h;
    }

    // ------------------------------------------------------------ 分頁
    function renderPagination() {
        const box = $('records-pagination');
        if (!box) return;
        const total = state.total || 0;
        const pages = Math.max(1, Math.ceil(total / state.pageSize));
        $('records-total').textContent = t('records.totalPrefix', '共 ') + fmtNum(total) +
            t('records.unitRecordsPage', ' 筆（第 ') + state.page + t('records.unitPageClose', ' 頁／共 ') + pages +
            t('records.unitPageEnd', ' 頁）');
        if (pages <= 1) {
            box.innerHTML = '';
            return;
        }
        const cur = state.page;
        let h = '<div class="pagination">';
        h += '<button type="button" class="btn-secondary" data-go="1"' + (cur <= 1 ? ' disabled' : '') + '>' + esc(t('common.first', '首頁')) + '</button>';
        h += '<button type="button" class="btn-secondary" data-go="' + (cur - 1) + '"' + (cur <= 1 ? ' disabled' : '') + '>' + esc(t('common.prev', '上一頁')) + '</button>';
        const start = Math.max(1, cur - 2);
        const end = Math.min(pages, start + 4);
        for (let i = start; i <= end; i++) {
            h += '<button type="button" class="btn-secondary' + (i === cur ? ' active' : '') + '" data-go="' + i + '">' + i + '</button>';
        }
        h += '<button type="button" class="btn-secondary" data-go="' + (cur + 1) + '"' + (cur >= pages ? ' disabled' : '') + '>' + esc(t('common.next', '下一頁')) + '</button>';
        h += '<button type="button" class="btn-secondary" data-go="' + pages + '"' + (cur >= pages ? ' disabled' : '') + '>' + esc(t('common.last', '末頁')) + '</button>';
        h += '</div>';
        box.innerHTML = h;
        box.querySelectorAll('[data-go]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                const go = parseInt(btn.getAttribute('data-go'), 10);
                if (go >= 1 && go <= pages && go !== state.page) {
                    state.page = go;
                    loadRecords();
                }
            });
        });
    }

    // ------------------------------------------------------------ 載入
    async function loadRecords() {
        const box = $('records-banner');
        try {
            const meta = await getJSON('/api/records/types');
            state.types = meta.types || [];
            state.datasets = meta.datasets || [];
            if (!state.type && state.types.length) {
                const withData = state.types.find(function (t2) { return t2.has_data; });
                state.type = (withData || state.types[0]).id;
            }
            // 每個型別第一次載入時：排序預設用「有值率最高的日期欄位」，
            // 欄位預設只顯示真的有值的。
            if (!state.sortBy) {
                const ds = defaultSort();
                state.sortBy = ds.by;
                state.sortDir = ds.dir;
            }
            ensureHidden();
            renderTypeTabs();
            renderDatasetSelect();
            renderColumnControls();

            const q = new URLSearchParams();
            q.set('page', state.page);
            q.set('page_size', state.pageSize);
            if (state.type) q.set('type', state.type);
            if (state.dataset) q.set('dataset', state.dataset);
            if (state.facet) q.set('facet', state.facet);
            if (state.q) q.set('q', state.q);
            if (state.sortBy) {
                q.set('sort_by', state.sortBy);
                q.set('sort_dir', state.sortDir || 'desc');
            }

            const data = await getJSON('/api/records/list?' + q.toString());
            if (data.db_missing) {
                if (box) {
                    box.className = 'loan-source-banner warn';
                    box.textContent = data.message || '';
                }
                $('records-table').innerHTML = '<div class="loan-empty">' + esc(t('records.dbMissing', '提取記錄庫尚未建立。')) + '</div>';
                return;
            }
            state.total = data.total || 0;
            state.lastItems = data.items || [];
            if (box) {
                box.className = 'loan-source-banner';
                const dbPath = meta.db_path || '';
                box.innerHTML = '<b>' + esc(t('records.console', '提取記錄管理主控台')) + '</b>' +
                    esc(t('records.sepDb', ' ｜ 資料庫 ')) + '<code>' + esc(dbPath) + '</code>' +
                    esc(t('records.sepTotal', ' ｜ 總筆數 ')) + '<b>' + fmtNum(meta.total || 0) + '</b>' +
                    '<div class="loan-banner-note">' + esc(t('records.note', '所有資料來自掃描器實際提取並經去重入庫；沒有資料就是沒有資料。')) + '</div>';
            }
            renderFacet(data.facet || [], data.facet_column || '');
            renderTable(state.lastItems);
            renderPagination();
        } catch (e) {
            if (box) {
                box.className = 'loan-source-banner warn';
                box.innerHTML = esc(t('records.loadFailed', '載入失敗：')) + esc(e.message || e);
            }
        }
    }

    function renderDatasetSelect() {
        const sel = $('records-dataset');
        if (!sel) return;
        const cur = state.dataset;
        sel.innerHTML = '<option value="">' + esc(t('records.allDatasets', '全部資料集')) + '</option>' +
            state.datasets.map(function (d) {
                return '<option value="' + esc(d.value) + '">' + esc(d.value) + '（' + fmtNum(d.count) + '）</option>';
            }).join('');
        sel.value = cur;
    }

    function renderFacet(buckets, column) {
        const box = $('records-facet');
        if (!box) return;
        const def = state.types.find(function (ty) { return ty.id === state.type; });
        if (!def) { box.innerHTML = ''; return; }
        const facetCol = column || def.facet_column || '';
        const facetDef = (def.columns || []).find(function (c) { return c.key === facetCol; });
        let h = '<span class="records-facet-title">' + esc(t('records.classify', '分類維度')) + '</span>';
        if (!facetDef) {
            h += '<span class="muted">' + esc(t('records.noFacet', '（此分類未設定維度）')) + '</span>';
        } else {
            h += '<select id="records-facet-select" class="records-facet-select">';
            (def.columns || []).filter(function (c) { return c.facet; }).forEach(function (c) {
                h += '<option value="' + esc(c.key) + '"' + (c.key === facetCol ? ' selected' : '') + '>' + esc(c.label) + '</option>';
            });
            h += '</select>';
            h += '<div class="records-facet-chips">';
            h += '<button type="button" class="records-facet-chip' + (!state.facet ? ' active' : '') + '" data-facet="">' +
                esc(t('records.all', '全部')) + '（' + fmtNum(state.total) + '）</button>';
            buckets.forEach(function (b) {
                h += '<button type="button" class="records-facet-chip' + (state.facet === b.value ? ' active' : '') +
                    '" data-facet="' + esc(b.value) + '">' + esc(b.value) + '（' + fmtNum(b.count) + '）</button>';
            });
            h += '</div>';
        }
        box.innerHTML = h;
        const sel = $('records-facet-select');
        if (sel) {
            sel.addEventListener('change', function () {
                state.facet = sel.value;
                state.page = 1;
                loadRecords();
            });
        }
        box.querySelectorAll('[data-facet]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                state.facet = btn.getAttribute('data-facet');
                state.page = 1;
                loadRecords();
            });
        });
    }

    // ------------------------------------------------------------ 下載
    async function downloadRecords(format) {
        const btn = $('records-download');
        try {
            const q = new URLSearchParams();
            if (state.type) q.set('type', state.type);
            if (state.dataset) q.set('dataset', state.dataset);
            if (state.q) q.set('q', state.q);
            if (btn) btn.disabled = true;
            await downloadAuthenticated('/api/records/export?' + q.toString(), 'records.csv');
            if (typeof toast === 'function') toast(t('records.downloaded', '已下載'), 'success');
        } catch (e) {
            if (typeof toast === 'function') {
                toast((e && e.message) ? e.message : t('records.downloadFailed', '下載失敗'), 'error');
            }
        } finally {
            if (btn) btn.disabled = false;
        }
    }

    // ------------------------------------------------------------ 對外
    async function recordsReload() {
        state.page = 1;
        await loadRecords();
    }

    function recordsSearch(page) {
        state.page = page || 1;
        const input = $('records-q');
        state.q = input ? input.value.trim() : '';
        const ds = $('records-dataset');
        state.dataset = ds ? ds.value : '';
        loadRecords();
    }

    function recordsTypeChanged() {
        state.page = 1;
        state.facet = '';
        loadRecords();
    }

    window.recordsReload = recordsReload;
    window.recordsSearch = recordsSearch;
    window.recordsTypeChanged = recordsTypeChanged;
    window.recordsDownload = downloadRecords;
    window.loadRecordsConsole = loadRecords;
})();
