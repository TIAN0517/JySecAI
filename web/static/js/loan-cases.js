/* ==========================================================================
   loan-cases.js — 貸款案件主檔（真實資料，唯讀）
   --------------------------------------------------------------------------
   資料來源：中租（chailease）mid-sign 靶站 2023–2026 完整批次匯出（57 表），
   經 scripts/import_loan_cases.py 整理後由 /api/loan/* 提供。

   原則：畫面上每一個數字都來自 API 的真實回應；沒有資料就顯示空狀態，
        絕不顯示示範列或 0 值假象。
   ========================================================================== */

(function () {
    'use strict';

    const state = {
        page: 1,
        pageSize: 50,
        q: '',
        year: '',
        table: '',
        total: 0,
        loaded: false
    };

    const $ = (id) => document.getElementById(id);

    function esc(v) {
        if (v === null || v === undefined) return '';
        return String(v)
            .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    function fmtNum(v) {
        if (v === null || v === undefined || v === '') return '-';
        const n = Number(v);
        if (!isFinite(n)) return esc(v);
        return n.toLocaleString('zh-TW');
    }

    function fmtMoney(v) {
        if (v === null || v === undefined || v === '') return '-';
        const n = Number(v);
        if (!isFinite(n)) return esc(v);
        return n.toLocaleString('zh-TW');
    }

    async function getJSON(url) {
        const res = await window.apiFetch(url);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        return res.json();
    }

    // ------------------------------------------------------------ 總覽
    async function loanLoadSummary() {
        const box = $('loan-source-banner');
        const sum = $('loan-summary');
        try {
            const data = await getJSON('/api/loan/summary');
            if (data.db_missing) {
                box.className = 'loan-source-banner warn';
                box.innerHTML = uiT('loanCases.warnDbNotImported', '⚠ 貸款資料庫尚未匯入（') + esc(data.db_path || '') +
                    uiT('loanCases.runImport', '）。請執行 <code>scripts/import_loan_cases.py</code> 後重新載入。');
                sum.innerHTML = '';
                return;
            }
            const meta = data.meta || {};
            const c = data.counts || {};
            box.className = 'loan-source-banner';
            box.innerHTML =
                '<b>' + esc(meta.dataset_label || uiT('loanCases.loanCaseMaster', '貸款案件主檔')) + '</b>' +
                uiT('loanCases.sepTarget', ' ｜ 靶站 <code>') + esc(meta.source_host || '-') + '</code>' +
                uiT('loanCases.sepImportedAt', ' ｜ 匯入時間 ') + esc(meta.imported_at || '-') +
                uiT('loanCases.sepShaVerify', ' ｜ <b>來源檔 sha256 覆核：') + esc(meta.source_sha256_verified || uiT('loanCases.unverified', '未覆核')) + '</b>' +
                uiT('loanCases.sepSourceTables', ' ｜ 來源表 ') + esc(meta.table_count || '-') + uiT('loanCases.unitRows', ' 張') +
                '<div class="loan-banner-note">' + esc(meta.manifest_scope_note || '') + '</div>';

            sum.innerHTML = [
                kpi(uiT('loanCases.caseCount', '案件數'), fmtNum(c.loan_cases)),
                kpi(uiT('loanCases.applicationCount', '申請單數'), fmtNum(c.loan_applications)),
                kpi(uiT('loanCases.amountSourceTrace', '金額來源追蹤'), fmtNum(c.loan_amount_sources)),
                kpi(uiT('loanCases.contractDetail', '契約明細'), fmtNum(c.loan_contract_details)),
                kpi(uiT('loanCases.repaymentPlan', '還元計畫'), fmtNum(c.loan_repay_plans)),
                kpi(uiT('loanCases.monthlyPayment', '擔保月款'), fmtNum(c.loan_collateral_monthly)),
                kpi(uiT('loanCases.approvedAmountTotal', '核准金額合計'), fmtMoney(data.sum_approved)),
                kpi(uiT('loanCases.sourceTable', '來源表'), fmtNum(c.loan_table_manifest))
            ].join('');

            // 年度分布
            const years = data.years || [];
            $('loan-years').innerHTML = table(
                [uiT('loanCases.year', '年份'), uiT('loanCases.applicationCount', '申請單數'), uiT('loanCases.mergedApprovedAmount', '合併核准金額')],
                years.map(y => [esc(y.year), fmtNum(y.app_count), fmtMoney(y.total_approved)]),
                uiT('loanCases.noYearStats', '（尚無年度統計）'));

            // 金額來源分布
            const src = data.source_distribution || [];
            $('loan-sources').innerHTML = table(
                [uiT('loanCases.amountSourceField', '金額來源欄'), uiT('loanCases.caseCount', '案件數'), uiT('loanCases.amountTotal', '金額合計')],
                src.map(s => [esc(s.source_field), fmtNum(s.cases), fmtMoney(s.total)]),
                uiT('loanCases.noAmountSource', '（尚無金額來源資料）'));

            // 年度篩選選單
            const sel = $('loan-year');
            if (sel && sel.options.length <= 1) {
                years.forEach(y => {
                    const o = document.createElement('option');
                    o.value = y.year; o.textContent = y.year;
                    sel.appendChild(o);
                });
            }
        } catch (e) {
            box.className = 'loan-source-banner warn';
            box.innerHTML = uiT('loanCases.warnOverviewFailed', '⚠ 載入總覽失敗：') + esc(e.message || e);
        }
    }

    function kpi(label, value) {
        return '<div class="loan-kpi"><div class="loan-kpi-label">' + esc(label) +
            '</div><div class="loan-kpi-value">' + esc(value) + '</div></div>';
    }

    function table(head, rows, emptyText) {
        let h = '<table class="loan-table"><thead><tr>';
        head.forEach(x => { h += '<th>' + esc(x) + '</th>'; });
        h += '</tr></thead><tbody>';
        if (!rows || !rows.length) {
            h += '<tr><td colspan="' + head.length + '" class="loan-empty">' + esc(emptyText) + '</td></tr>';
        } else {
            rows.forEach(r => {
                h += '<tr>';
                r.forEach(c => { h += '<td>' + c + '</td>'; });
                h += '</tr>';
            });
        }
        return h + '</tbody></table>';
    }

    // ------------------------------------------------------------ 案件清單
    async function loanSearch(page) {
        state.page = page || 1;
        const q = new URLSearchParams();
        q.set('page', state.page);
        q.set('page_size', state.pageSize);
        if (state.q) q.set('q', state.q);
        if (state.year) q.set('year', state.year);
        if (state.table) q.set('source_table', state.table);
        const box = $('loan-cases');
        try {
            const data = await getJSON('/api/loan/cases?' + q.toString());
            if (data.db_missing) {
                box.innerHTML = uiT('loanCases.dbNotImported', '<div class="loan-empty">貸款資料庫尚未匯入。</div>');
                $('loan-total').textContent = '';
                return;
            }
            state.total = data.total || 0;
            const rows = (data.items || []).map(it => [
                '<a href="#" onclick="loanCaseDetail(\'' + esc(it.case_no) + '\');return false;" class="loan-link">' +
                esc(it.case_no) + '</a>',
                fmtNum(it.app_count),
                esc(it.code_year),
                esc(it.first_apply_at),
                esc(it.last_apply_at),
                esc(it.amount_source_flag),
                esc(it.source_tables)
            ]);
            box.innerHTML = table(
                [uiT('loanCases.caseNo', '案件編號'), uiT('loanCases.applicationCount', '申請單數'), uiT('loanCases.encodeYear', '編碼年'), uiT('loanCases.applyDateEarliest', '申請日最早'), uiT('loanCases.applyDateLatest', '申請日最晚'), uiT('loanCases.amountSourceFlag', '金額來源標記'), uiT('loanCases.sourceTable', '來源表')],
                rows, uiT('loanCases.noRows', '（查無資料）'));
            $('loan-total').textContent = uiT('loanCases.totalPrefix', '共 ') + fmtNum(state.total) + uiT('loanCases.unitCasesPage', ' 件（第 ') +
                state.page + uiT('loanCases.unitPageClose', ' 頁）');
            renderPagination();
        } catch (e) {
            box.innerHTML = uiT('loanCases.loadFailed', '<div class="loan-empty">載入失敗：') + esc(e.message || e) + '</div>';
        }
    }

    function renderPagination() {
        const pages = Math.ceil((state.total || 0) / state.pageSize);
        const el = $('loan-pagination');
        if (!el) return;
        if (pages <= 1) { el.innerHTML = ''; return; }
        let h = '<button class="btn-secondary" onclick="loanSearch(' + Math.max(1, state.page - 1) +
            ')" ' + (state.page <= 1 ? 'disabled' : '') + uiT('loanCases.prevPage', '>上一頁</button>');
        h += uiT('loanCases.pageInfo', '<span class="loan-pageinfo">第 ') + state.page + ' / ' + pages + uiT('loanCases.unitPage', ' 頁</span>');
        h += '<button class="btn-secondary" onclick="loanSearch(' + Math.min(pages, state.page + 1) +
            ')" ' + (state.page >= pages ? 'disabled' : '') + uiT('loanCases.nextPage', '>下一頁</button>');
        el.innerHTML = h;
    }

    // ------------------------------------------------------------ 案件詳情
    async function loanCaseDetail(caseNo) {
        try {
            const d = await getJSON('/api/loan/case/' + encodeURIComponent(caseNo));
            const c = d.case || {};
            const srcs = (d.amount_sources || []).map(s =>
                '<tr><td>' + esc(s.source_field) + '</td><td>' + fmtMoney(s.amount) +
                '</td><td>' + esc(s.level) + '</td></tr>');
            const apps = (d.applications || []).map(a =>
                '<tr><td>' + esc(a.app_no) + '</td><td>' + esc(a.apply_at) + '</td><td>' +
                esc(a.case_status) + '</td><td>' + fmtMoney(a.approved_amount) + '</td><td>' +
                fmtNum(a.periods) + '</td><td>' + esc(a.first_due) + '</td></tr>');
            const html =
                uiT('loanCases.modalTitle', '<div class="loan-modal-title">案件 ') + esc(caseNo) + '</div>' +
                table([uiT('loanCases.caseNo', '案件編號'), uiT('loanCases.applicationCount', '申請單數'), uiT('loanCases.encodeYear', '編碼年'), uiT('loanCases.amountSourceFlag', '金額來源標記'), uiT('loanCases.sourceTable', '來源表')],
                    [[esc(c.case_no), fmtNum(c.app_count), esc(c.code_year),
                        esc(c.amount_source_flag), esc(c.source_tables)]], uiT('loanCases.noData', '（無資料）')) +
                uiT('loanCases.amountProvenance', '<h4>金額來源追蹤</h4>') +
                table([uiT('loanCases.amountSourceField', '金額來源欄'), uiT('loanCases.amount', '金額'), uiT('loanCases.tier', '層級')], srcs, uiT('loanCases.noAmountSourceShort', '（無金額來源）')) +
                uiT('loanCases.applications', '<h4>申請單</h4>') +
                table([uiT('loanCases.applicationNo', '申請單編號'), uiT('loanCases.applyDate', '申請日'), uiT('loanCases.caseStatus', '案件狀態'), uiT('loanCases.approvedAmount', '核准金額'), uiT('loanCases.terms', '期數'), uiT('loanCases.firstDue', '最早應繳')],
                    apps, uiT('loanCases.noApplications', '（無申請單）'));
            showLoanModal(html);
        } catch (e) {
            showLoanModal(uiT('loanCases.loadFailed', '<div class="loan-empty">載入失敗：') + esc(e.message || e) + '</div>');
        }
    }

    function showLoanModal(html) {
        let m = document.getElementById('loan-modal');
        if (!m) {
            m = document.createElement('div');
            m.id = 'loan-modal';
            m.className = 'loan-modal';
            m.innerHTML = '<div class="loan-modal-box"><div class="loan-modal-close" onclick="closeLoanModal()">×</div>' +
                '<div id="loan-modal-body"></div></div>';
            document.body.appendChild(m);
        }
        document.getElementById('loan-modal-body').innerHTML = html;
        m.style.display = 'flex';
    }

    function closeLoanModal() {
        const m = document.getElementById('loan-modal');
        if (m) m.style.display = 'none';
    }

    // ------------------------------------------------------------ manifest
    async function loanLoadTables() {
        const box = $('loan-tables');
        try {
            const data = await getJSON('/api/loan/tables');
            if (data.db_missing) { box.innerHTML = uiT('loanCases.notImported', '<div class="loan-empty">尚未匯入。</div>'); return; }
            const rows = (data.items || []).map(it => [
                esc(it.table_name),
                fmtNum(it.rows),
                '<code class="loan-sha">' + esc(it.sha256) + '</code>'
            ]);
            box.innerHTML = table([uiT('loanCases.sourceTable', '來源表'), uiT('loanCases.rowCount', '行數'), 'SHA256'], rows, uiT('loanCases.noManifest', '（尚無 manifest）'));
        } catch (e) {
            box.innerHTML = uiT('loanCases.loadFailed', '<div class="loan-empty">載入失敗：') + esc(e.message || e) + '</div>';
        }
    }

    async function loanVerify() {
        const box = $('loan-tables');
        box.innerHTML = uiT('loanCases.recomputing', '<div class="loan-empty">正在重新計算來源檔 sha256…</div>');
        try {
            const data = await getJSON('/api/loan/verify');
            if (!data.checked) {
                box.innerHTML = uiT('loanCases.sourceMissing', '<div class="loan-empty warn">來源檔不在本機，無法覆核（') +
                    esc(data.source_dir || '') + '）。</div>';
                return;
            }
            const rows = (data.items || []).map(it => [
                esc(it.table_name),
                it.verified === true ? uiT('loanCases.passed', '<span class="loan-ok">通過</span>')
                    : (it.verified === false ? uiT('loanCases.mismatch', '<span class="loan-bad">不符</span>') : uiT('loanCases.unverified', '未覆核')),
                '<code class="loan-sha">' + esc(it.sha256) + '</code>'
            ]);
            box.innerHTML = uiT('loanCases.verifyResult', '<div class="loan-banner-note">覆核結果：') + data.passed + ' / ' +
                data.checked + uiT('loanCases.sourceRowsMatch', ' 張來源檔 sha256 相符</div>') +
                table([uiT('loanCases.sourceTable', '來源表'), uiT('loanCases.verify', '覆核'), 'manifest SHA256'], rows, uiT('loanCases.noData', '（無資料）'));
        } catch (e) {
            box.innerHTML = uiT('loanCases.verifyFailed', '<div class="loan-empty">覆核失敗：') + esc(e.message || e) + '</div>';
        }
    }

    // ------------------------------------------------------------ 入口
    // ------------------------------------------------------------ 分類字典
    // 狀態／類型／客群代碼的中文名稱在中租同站點離線資料中不存在，
    // API 端只回傳可推得特徵與統計、中文名稱標 pending → 畫面如實顯示。
    async function loanLoadClassification() {
        const box = $('loan-classification');
        if (!box) return;
        const note = $('loan-class-note');
        let data;
        try {
            data = await getJSON('/api/loan/classification');
        } catch (e) {
            box.innerHTML = uiT('loanCases.dictLoadFailed', '<div class="empty-state">分類字典載入失敗：') + esc(e.message) + '</div>';
            return;
        }
        if (!data || !data.ok) {
            box.innerHTML = uiT('loanCases.dbMissing', '<div class="empty-state">（尚未匯入貸款案件資料，DB 缺失）</div>');
            return;
        }
        if (note) {
            note.textContent = uiT('loanCases.rowApplications', '　申請單 ') + fmtNum(data.total_applications) + uiT('loanCases.unitItemsDot', ' 筆 · ') +
                (data.dictionary_gap || '');
        }

        const st = (data.statuses || []).map(s => [
            esc(s.code), fmtNum(s.n), (Number(s.pct || 0)).toFixed(2) + '%',
            fmtMoney(s.amt), fmtNum(s.with_plan),
            (s.avg_periods ? Number(s.avg_periods).toFixed(1) : '-'),
            esc((s.year_from || '-') + '–' + (s.year_to || '-')),
            esc(s.cn_label || '')
        ]);

        const dictRows = [];
        for (const key of ['case_type', 'customer_group']) {
            for (const d of ((data.dicts || {})[key] || [])) {
                dictRows.push([key === 'case_type' ? uiT('loanCases.type', '類型') : uiT('loanCases.segment', '客群'), esc(d.code),
                    fmtNum(d.n), fmtMoney(d.amt), esc(d.cn_label || '')]);
            }
        }

        const cross = (data.cross || {});
        const crossRows = [];
        for (const k of Object.keys(cross).sort()) {
            for (const r of (cross[k] || [])) {
                crossRows.push([esc(k), esc(r.a), esc(r.b), fmtNum(r.n), fmtMoney(r.amt)]);
            }
        }

        box.innerHTML =
            uiT('loanCases.statusCodes', '<h4>狀態代碼</h4>') +
            table([uiT('loanCases.code', '代碼'), uiT('loanCases.itemCount', '筆數'), uiT('loanCases.share', '佔比'), uiT('loanCases.approvedSum', '核准額合計'), uiT('loanCases.hasRepaymentPlan', '有還款計畫'), uiT('loanCases.avgTerms', '平均期數'),
                uiT('loanCases.yearRange', '年度區間'), uiT('loanCases.chineseName', '中文名稱')], st, uiT('loanCases.noData', '（無資料）')) +
            uiT('loanCases.typeSegment', '<h4 style="margin-top:16px;">類型 / 客群</h4>') +
            table([uiT('loanCases.dimension', '維度'), uiT('loanCases.code', '代碼'), uiT('loanCases.itemCount', '筆數'), uiT('loanCases.approvedSum', '核准額合計'), uiT('loanCases.chineseName', '中文名稱')], dictRows, uiT('loanCases.noData', '（無資料）')) +
            uiT('loanCases.crossStats', '<h4 style="margin-top:16px;">交叉統計</h4>') +
            table([uiT('loanCases.crossTab', '交叉表'), uiT('loanCases.dimensionA', '維度 A'), uiT('loanCases.dimensionB', '維度 B'), uiT('loanCases.itemCount', '筆數'), uiT('loanCases.approvedSum', '核准額合計')], crossRows, uiT('loanCases.noData', '（無資料）'));
    }

    async function loanReload() {
        state.q = $('loan-q') ? $('loan-q').value.trim() : '';
        state.year = $('loan-year') ? $('loan-year').value : '';
        state.table = $('loan-table') ? $('loan-table').value.trim() : '';
        await loanLoadSummary();
        await loanSearch(1);
        await loanLoadTables();
        await loanLoadClassification();
    }

    // 頁面切換時載入（switchPage 會呼叫 onPageShown 之類的 hook；沒有就直接載入）
    function loanEnsureLoaded() {
        if (state.loaded) return;
        state.loaded = true;
        loanReload();
    }

    window.loanReload = loanReload;
    window.loanSearch = loanSearch;
    window.loanVerify = loanVerify;
    window.loanCaseDetail = loanCaseDetail;
    window.closeLoanModal = closeLoanModal;
    window.loanEnsureLoaded = loanEnsureLoaded;

    document.addEventListener('DOMContentLoaded', () => {
        const btn = $('btn-loan-cases');
        if (btn) btn.addEventListener('click', () => setTimeout(loanEnsureLoaded, 120));
        const q = $('loan-q');
        if (q) q.addEventListener('keydown', (e) => { if (e.key === 'Enter') loanSearch(1); });
    });
})();
