const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

// scope_extension（授權範圍擴充）審批卡的行為測試。
//
// 這支測試釘死四件事：
//   1. 模式與決策詞彙的辨識不會誤傷既有的 approval / review_edit。
//   2. 卡片必須把「未覆蓋目標／相鄰已授權／四種決策」都畫出來。
//   3. 任意執行類工具沒宣告目標時，**不准**送出批准（fail closed）。
//   4. JS 裡用到的每個 hitl.scope.* 鍵，兩份語系包都必須真的有。
//
// 為什麼 mock 真實的 zh-CN.json 而不是自己塞字典
// --------------------------------------------
// scope-extension.js 的備援值一律英文（中文由語系包提供，這是 i18n 守門測試
// internal/app/web_i18n_test.go 的要求）。所以若測試只 mock 一個假的 t()，
// 卡片在測試裡會呈現英文，卻無法證明「實際載入語系包後中文是對的」。
// 直接吃真的 zh-CN.json 才能同時驗到兩件事：
//   - 語系包裡的鍵真的被 JS 用到且拼對
//   - 兩份語系包的鍵集一致（缺一邊就是半中半英）
const source = fs.readFileSync('web/static/js/scope-extension.js', 'utf8');
const zhCN = JSON.parse(fs.readFileSync('web/static/i18n/zh-CN.json', 'utf8'));
const enUS = JSON.parse(fs.readFileSync('web/static/i18n/en-US.json', 'utf8'));

function flatten(prefix, node, into) {
    Object.keys(node || {}).forEach((key) => {
        const next = prefix ? prefix + '.' + key : key;
        const child = node[key];
        if (child && typeof child === 'object' && !Array.isArray(child)) {
            flatten(next, child, into);
        } else {
            into[next] = child;
        }
    });
    return into;
}

const zhFlat = flatten('', zhCN, {});
const enFlat = flatten('', enUS, {});

function escapeHtml(value) {
    return String(value === null || value === undefined ? '' : value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

function load() {
    const submitted = [];
    const sandbox = {
        console,
        setTimeout: (fn) => { fn(); return 0; },
        clearTimeout: () => {},
        escapeHtml,
        document: {
            getElementById: () => null,
            querySelector: () => null,
            querySelectorAll: () => [],
        },
        // 真實語系包譯者：查不到就回傳鍵名，跟前端 window.t 的行為一致。
        t: (key) => (Object.prototype.hasOwnProperty.call(zhFlat, key) ? zhFlat[key] : key),
        // 送出紀錄：測試用來檢查「送了什麼決策、帶了什麼條件」
        submitHitlDecisionWithPayload: async (...args) => {
            submitted.push(args);
            return true;
        },
    };
    sandbox.window = sandbox;
    vm.createContext(sandbox);
    vm.runInContext(source, sandbox);
    return { sandbox, submitted };
}

function samplePayload(overrides) {
    return Object.assign({
        toolName: 'httpx',
        arguments: '{"targets":"new.api.example.com"}',
        argumentsObj: { targets: 'new.api.example.com' },
        scopeExtension: {
            actionClass: 'harmless_request',
            reason: 'not_covered_by_any_scope',
            arbitrary: false,
            uncovered: [
                { raw: 'new.api.example.com', host: 'new.api.example.com', port: '', kind: 'host', key: 'new.api.example.com' },
            ],
            adjacent: [
                {
                    host: 'api.example.com',
                    owner: 'example-client',
                    grantId: 'scope_1',
                    source: 'scope_target',
                    actionClasses: ['harmless_request'],
                    validUntil: '2026-12-01T00:00:00Z',
                },
            ],
            denied: [],
        },
    }, overrides || {});
}

// 最小可用的 panel 替身：只支援 querySelector / querySelectorAll。
function makePanel(spec) {
    const elements = {};
    Object.keys(spec || {}).forEach((sel) => {
        elements[sel] = {
            __sel: sel,
            value: spec[sel] === null ? '' : String(spec[sel] === undefined ? '' : spec[sel]),
            textContent: '',
            disabled: false,
            handlers: [],
            addEventListener(type, fn) { if (type === 'click') this.handlers.push(fn); },
            click() { this.handlers.forEach((fn) => fn({})); },
            querySelector(sel) { return elements[sel] || null; },
            querySelectorAll(sel) {
                return Object.values(elements).filter((el) => el.__sel === sel);
            },
        };
    });
    return {
        __elements: elements,
        classList: { add() {}, remove() {}, contains() { return false; } },
        innerHTML: '',
        querySelector(sel) { return elements[sel] || null; },
        querySelectorAll(sel) { return Object.values(elements).filter((el) => el.__sel === sel); },
    };
}

test('模式辨識：scope_extension 不會被誤判成既有模式', () => {
    const { sandbox } = load();
    assert.equal(sandbox.scopeExtIsMode('scope_extension'), true);
    assert.equal(sandbox.scopeExtIsMode('SCOPE_EXTENSION'), true);
    assert.equal(sandbox.scopeExtIsMode('approval'), false);
    assert.equal(sandbox.scopeExtIsMode('review_edit'), false);
    assert.equal(sandbox.scopeExtIsMode(''), false);
});

test('決策詞彙：只有 scope 專屬的四個算數，approve 不算', () => {
    const { sandbox } = load();
    ['approve_permanent', 'approve_once', 'approve_conditional', 'reject'].forEach((d) => {
        assert.equal(sandbox.scopeExtIsDecision(d), true, d);
    });
    assert.equal(sandbox.scopeExtIsDecision('approve'), false);
    assert.equal(sandbox.scopeExtIsDecision(''), false);
    // approve 仍算「批准」，只是不是 scope 的決策詞彙。
    assert.equal(sandbox.scopeExtIsApproval('approve'), true);
    assert.equal(sandbox.scopeExtIsApproval('approve_permanent'), true);
    assert.equal(sandbox.scopeExtIsApproval('reject'), false);
});

test('待裁決卡片：未覆蓋目標、相鄰已授權與四種決策都要畫出來', () => {
    const { sandbox } = load();
    const html = sandbox.buildScopeExtensionApprovalHtml(
        { interruptId: 'hitl_1', status: 'pending', payload: samplePayload() },
        { toolName: 'httpx' }
    );
    assert.ok(html.includes('new.api.example.com'), '未覆蓋目標要出現');
    assert.ok(html.includes('api.example.com'), '相鄰已授權要出現');
    assert.ok(html.includes('example-client'), '相鄰的擁有者要出現');
    assert.ok(html.includes('harmless_request'), '動作類別要出現');
    assert.ok(html.includes('hitl-scope-permanent'), '要有批准為常駐');
    assert.ok(html.includes('hitl-scope-once'), '要有只准這次');
    assert.ok(html.includes('hitl-scope-conditional'), '要有附條件批准');
    assert.ok(html.includes('hitl-scope-reject'), '要有拒絕');
});

test('任意執行類：必須出現目標宣告欄位；非任意執行類則不出現', () => {
    const { sandbox } = load();
    const arbitraryHtml = sandbox.buildScopeExtensionApprovalHtml(
        {
            interruptId: 'hitl_2',
            status: 'pending',
            payload: samplePayload({
                scopeExtension: Object.assign(samplePayload().scopeExtension, { arbitrary: true }),
            }),
        },
        { toolName: 'exec' }
    );
    assert.ok(arbitraryHtml.includes('hitl-scope-targets-input'), '任意執行類要有目標宣告欄位');

    const normalHtml = sandbox.buildScopeExtensionApprovalHtml(
        { interruptId: 'hitl_3', status: 'pending', payload: samplePayload() },
        { toolName: 'httpx' }
    );
    assert.ok(!normalHtml.includes('hitl-scope-targets-input'), '宣告式工具不該多一個目標宣告欄位');
});

test('已裁決卡片：決策詞彙要原樣保留，不得一律顯示成「已允許一次」', () => {
    const { sandbox } = load();
    const html = sandbox.buildScopeExtensionApprovalHtml(
        {
            interruptId: 'hitl_4',
            status: 'decided',
            decision: 'approve_permanent',
            payload: samplePayload(),
        },
        { toolName: 'httpx' }
    );
    assert.ok(html.includes('已加入常駐授權範圍'), '批准為常駐要顯示常駐語意');
    assert.ok(!html.includes('已允許一次'), '不得退化成通用文案');
});

test('任意執行類沒宣告目標 → 拒絕送出（fail closed）', async () => {
    const { sandbox, submitted } = load();
    const panel = makePanel({
        '.hitl-scope-permanent': '',
        '.hitl-scope-once': '',
        '.hitl-scope-conditional': '',
        '.hitl-scope-reject': '',
        '.hitl-scope-status': '',
        '.hitl-scope-targets-input': '   \n  \n',
        '.hitl-inline-comment': '',
    });
    sandbox.bindScopeExtensionApproval(panel, {
        interruptId: 'hitl_5',
        conversationId: 'conv-1',
        payload: samplePayload({
            scopeExtension: Object.assign(samplePayload().scopeExtension, { arbitrary: true }),
        }),
    });
    panel.__elements['.hitl-scope-permanent'].click();
    await new Promise((resolve) => setTimeout(resolve, 0));
    assert.equal(submitted.length, 0, '沒有宣告目標就不得送出任何決策');
    assert.ok(panel.__elements['.hitl-scope-status'].textContent.length > 0, '要給操作者看得見的錯誤');
});

test('宣告式工具按「只准這次」→ 送出 approve_once 且帶上條件欄位', async () => {
    const { sandbox, submitted } = load();
    const panel = makePanel({
        '.hitl-scope-permanent': '',
        '.hitl-scope-once': '',
        '.hitl-scope-conditional': '',
        '.hitl-scope-reject': '',
        '.hitl-scope-status': '',
        '.hitl-inline-comment': '客戶已同意',
        '.hitl-scope-owner': 'example-client',
        '.hitl-scope-maxuses': '3',
        '.hitl-scope-validuntil': '2026-12-01T00:00:00Z',
        '.hitl-scope-classes': 'harmless_request, bulk_scan',
    });
    sandbox.bindScopeExtensionApproval(panel, {
        interruptId: 'hitl_6',
        conversationId: 'conv-2',
        payload: samplePayload(),
    });
    panel.__elements['.hitl-scope-once'].click();
    await new Promise((resolve) => setTimeout(resolve, 0));
    assert.equal(submitted.length, 1);
    const [interruptId, decision, comment, editedArgs, conversationId, scopeOptions] = submitted[0];
    assert.equal(interruptId, 'hitl_6');
    assert.equal(decision, 'approve_once');
    assert.equal(comment, '客戶已同意');
    assert.equal(editedArgs, null);
    assert.equal(conversationId, 'conv-2');
    assert.deepEqual(Array.from(scopeOptions.scopeConditions.actionClasses), ['harmless_request', 'bulk_scan']);
    assert.equal(scopeOptions.scopeConditions.maxUses, 3);
    assert.equal(scopeOptions.scopeConditions.validUntil, '2026-12-01T00:00:00Z');
});

test('任意執行類有宣告目標 → 允許送出，並把宣告清單一起送上去', async () => {
    const { sandbox, submitted } = load();
    const panel = makePanel({
        '.hitl-scope-permanent': '',
        '.hitl-scope-once': '',
        '.hitl-scope-conditional': '',
        '.hitl-scope-reject': '',
        '.hitl-scope-status': '',
        '.hitl-scope-targets-input': 'api.example.com\ncdn.example.com\n',
        '.hitl-inline-comment': '',
    });
    sandbox.bindScopeExtensionApproval(panel, {
        interruptId: 'hitl_7',
        conversationId: 'conv-3',
        payload: samplePayload({
            scopeExtension: Object.assign(samplePayload().scopeExtension, { arbitrary: true }),
        }),
    });
    panel.__elements['.hitl-scope-permanent'].click();
    await new Promise((resolve) => setTimeout(resolve, 0));
    assert.equal(submitted.length, 1);
    assert.equal(submitted[0][1], 'approve_permanent');
    assert.deepEqual(Array.from(submitted[0][5].scopeTargets), ['api.example.com', 'cdn.example.com']);
});

test('有效期限格式錯誤 → 不得送出', async () => {
    const { sandbox, submitted } = load();
    const panel = makePanel({
        '.hitl-scope-permanent': '',
        '.hitl-scope-once': '',
        '.hitl-scope-conditional': '',
        '.hitl-scope-reject': '',
        '.hitl-scope-status': '',
        '.hitl-inline-comment': '',
        '.hitl-scope-validuntil': '不是時間',
    });
    sandbox.bindScopeExtensionApproval(panel, {
        interruptId: 'hitl_8',
        conversationId: 'conv-4',
        payload: samplePayload(),
    });
    panel.__elements['.hitl-scope-conditional'].click();
    await new Promise((resolve) => setTimeout(resolve, 0));
    assert.equal(submitted.length, 0, '時間格式錯誤時不得送出');
});

test('語系包：JS 用到的每個 hitl.scope.* 鍵在兩份語系包都要存在', () => {
    const keys = new Set();
    const re = /scopeExtT\(\s*'([A-Za-z0-9_]+)'/g;
    let m;
    while ((m = re.exec(source)) !== null) {
        keys.add('hitl.scope.' + m[1]);
    }
    assert.ok(keys.size >= 30, '應該掃到足夠多的 scope 鍵，實際 ' + keys.size);
    const missingZh = [];
    const missingEn = [];
    keys.forEach((key) => {
        if (!Object.prototype.hasOwnProperty.call(zhFlat, key)) missingZh.push(key);
        if (!Object.prototype.hasOwnProperty.call(enFlat, key)) missingEn.push(key);
    });
    assert.deepEqual(missingZh, [], 'zh-CN.json 缺少 scope 鍵');
    assert.deepEqual(missingEn, [], 'en-US.json 缺少 scope 鍵');
});

test('語系包：hitl.scope.* 兩份語系包的鍵集必須完全一致', () => {
    const zhScope = Object.keys(zhFlat).filter((k) => k.startsWith('hitl.scope.')).sort();
    const enScope = Object.keys(enFlat).filter((k) => k.startsWith('hitl.scope.')).sort();
    assert.deepEqual(zhScope, enScope, '兩份語系包的 hitl.scope.* 鍵集不同步');
    assert.ok(zhScope.length >= 40, 'scope 鍵數應該齊全，實際 ' + zhScope.length);
});
