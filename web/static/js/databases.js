/* 数据库管理：平台本地 SQLite 目录 + 新增功能（跳转验证 / 贷款主档） */
(function () {
    'use strict';

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
        return n.toLocaleString();
    }

    function fmtBytes(v) {
        const n = Number(v);
        if (!isFinite(n) || n < 0) return '-';
        if (n < 1024) return n + ' B';
        if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB';
        return (n / (1024 * 1024)).toFixed(1) + ' MB';
    }

    function fmtTime(v) {
        if (!v) return '-';
        const d = new Date(v);
        if (isNaN(d.getTime())) return esc(v);
        return d.toLocaleString();
    }

    function statusBadge(ok, okText, badText) {
        if (ok) return '<span class="dbadmin-badge ok">' + esc(okText) + '</span>';
        return '<span class="dbadmin-badge warn">' + esc(badText) + '</span>';
    }

    function tableChips(tables) {
        const entries = Object.entries(tables || {});
        if (!entries.length) return '<div class="dbadmin-muted">暂无已识别表</div>';
        return entries.map(function (pair) {
            return '<div class="dbadmin-chip"><span>' + esc(pair[0]) + '</span><b>' + fmtNum(pair[1]) + '</b></div>';
        }).join('');
    }

    function renderDatabases(list) {
        const box = document.getElementById('dbadmin-databases');
        if (!box) return;
        if (!list || !list.length) {
            box.innerHTML = '<div class="dbadmin-empty">暂无数据库</div>';
            return;
        }
        box.innerHTML = list.map(function (db) {
            const jump = db.page ? '<button type="button" class="btn-secondary" data-jump="' + esc(db.page) + '">打开</button>' : '';
            return '<article class="dbadmin-card">' +
                '<div class="dbadmin-card-head">' +
                    '<div><h3>' + esc(db.name || db.id) + '</h3><p>' + esc(db.role || '') + '</p></div>' +
                    statusBadge(!!db.exists, '已就绪', '未导入') +
                '</div>' +
                '<div class="dbadmin-path">' + esc(db.path || '-') + '</div>' +
                '<div class="dbadmin-meta">' +
                    '<span>大小 ' + fmtBytes(db.size_bytes) + '</span>' +
                    '<span>表 ' + fmtNum(db.table_count) + '</span>' +
                    '<span>更新 ' + fmtTime(db.modified_at) + '</span>' +
                '</div>' +
                '<div class="dbadmin-chips">' + tableChips(db.tables) + '</div>' +
                '<div class="dbadmin-card-actions">' + jump + '</div>' +
                (db.error ? '<div class="dbadmin-error">' + esc(db.error) + '</div>' : '') +
            '</article>';
        }).join('');
        box.querySelectorAll('[data-jump]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                if (typeof switchPage === 'function') switchPage(btn.getAttribute('data-jump'));
            });
        });
    }

    function featureCounts(feat) {
        const counts = feat.counts || {};
        return Object.keys(counts).map(function (k) {
            return '<span>' + esc(k) + ' ' + fmtNum(counts[k]) + '</span>';
        }).join('');
    }

    function renderFeatures(list) {
        const box = document.getElementById('dbadmin-features');
        if (!box) return;
        if (!list || !list.length) {
            box.innerHTML = '<div class="dbadmin-empty">暂无功能记录</div>';
            return;
        }
        box.innerHTML = list.map(function (feat) {
            const ready = feat.imported === true || feat.enabled === true || (feat.counts && Object.values(feat.counts).some(function (n) { return Number(n) > 0; }));
            const extra = [];
            if (feat.attach_scan === true) extra.push('扫描同步植入');
            if (Array.isArray(feat.endpoints) && feat.endpoints.length) extra.push(feat.endpoints.join(' · '));
            const jump = feat.page ? '<button type="button" class="btn-secondary" data-jump="' + esc(feat.page) + '">打开</button>' : '';
            return '<article class="dbadmin-card dbadmin-feature">' +
                '<div class="dbadmin-card-head">' +
                    '<div><h3>' + esc(feat.name || feat.id) + '</h3><p>' + esc((feat.tables || []).join(' / ')) + '</p></div>' +
                    statusBadge(ready, '已写入', '待导入') +
                '</div>' +
                (extra.length ? '<div class="dbadmin-path">' + esc(extra.join(' ｜ ')) + '</div>' : '') +
                '<div class="dbadmin-meta">' + featureCounts(feat) + '</div>' +
                '<div class="dbadmin-card-actions">' + jump + '</div>' +
            '</article>';
        }).join('');
        box.querySelectorAll('[data-jump]').forEach(function (btn) {
            btn.addEventListener('click', function () {
                if (typeof switchPage === 'function') switchPage(btn.getAttribute('data-jump'));
            });
        });
    }

    async function loadDatabaseAdmin() {
        const banner = document.getElementById('dbadmin-banner');
        try {
            const res = await window.apiFetch('/api/databases');
            if (!res.ok) throw new Error('HTTP ' + res.status);
            const data = await res.json();
            renderDatabases(data.databases || []);
            renderFeatures(data.features || []);
            if (banner) {
                banner.className = 'dbadmin-banner';
                banner.textContent = '本地 SQLite 目录。批次跳转验证、贷款主档、XSS、C2、扫描任务都写在这里。';
            }
        } catch (err) {
            if (banner) {
                banner.className = 'dbadmin-banner warn';
                banner.textContent = '加载失败：' + (err && err.message ? err.message : err);
            }
        }
    }

    window.loadDatabaseAdmin = loadDatabaseAdmin;
})();
