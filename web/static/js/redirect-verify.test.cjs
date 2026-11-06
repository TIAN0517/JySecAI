const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

// 批次跳轉驗證控制台的純邏輯測試：情蒐結果如何變成目標清單。
const source = fs.readFileSync('web/static/js/redirect-verify.js', 'utf8');

function load() {
    const sandbox = { window: {}, console };
    sandbox.window.window = sandbox.window;
    vm.createContext(sandbox);
    vm.runInContext(source, sandbox);
    return sandbox.window;
}

test('extractRedirectVerifyHosts 收集各 provider 的主機欄位', () => {
    const { extractRedirectVerifyHosts } = load();
    const hosts = extractRedirectVerifyHosts([
        { host: 'a.example.com', ip: '1.1.1.1' },
        { hostname: 'b.example.com' },
        { domain: 'c.example.com' },
        { hostnames: ['d.example.com', 'e.example.com'] },
        { ip_str: '2.2.2.2' }
    ]);
    assert.deepEqual([...hosts], [
        'a.example.com',
        '1.1.1.1',
        'b.example.com',
        'c.example.com',
        'd.example.com',
        'e.example.com',
        '2.2.2.2'
    ]);
});

test('extractRedirectVerifyHosts 去掉重複與空值', () => {
    const { extractRedirectVerifyHosts } = load();
    const hosts = extractRedirectVerifyHosts([
        { host: 'a.example.com' },
        { host: 'a.example.com' },
        { host: '' },
        { ip: null }
    ]);
    assert.deepEqual([...hosts], ['a.example.com']);
});

test('extractRedirectVerifyHosts 對空結果回傳空陣列', () => {
    const { extractRedirectVerifyHosts } = load();
    assert.deepEqual([...extractRedirectVerifyHosts([])], []);
    assert.deepEqual([...extractRedirectVerifyHosts(null)], []);
});

test('extractRedirectVerifyURLs 只留 http/https 並去重', () => {
    const { extractRedirectVerifyURLs } = load();
    const urls = extractRedirectVerifyURLs([
        'https://victim.example.com/go?url=x',
        'https://victim.example.com/go?url=x',
        'http://victim.example.com/next',
        'ftp://victim.example.com/no',
        'javascript:alert(1)',
        '',
        null
    ]);
    assert.deepEqual([...urls], [
        'https://victim.example.com/go?url=x',
        'http://victim.example.com/next'
    ]);
});

test('extractRedirectVerifyURLs 對空值回傳空陣列', () => {
    const { extractRedirectVerifyURLs } = load();
    assert.deepEqual([...extractRedirectVerifyURLs(null)], []);
    assert.deepEqual([...extractRedirectVerifyURLs(undefined)], []);
});

test('renderRedirectVerifyEvidence 把真跳轉與僅回顯分成不同標籤', () => {
    const { renderRedirectVerifyEvidence } = load();
    const real = renderRedirectVerifyEvidence({ evidence: 'location', confirmed: true });
    const echo = renderRedirectVerifyEvidence({ evidence: 'body_echo', body_echo: true });
    const none = renderRedirectVerifyEvidence({ evidence: 'none' });
    assert.ok(real.includes('redirect-verify-badge--hit'), '真跳轉應使用命中樣式：' + real);
    assert.ok(echo.includes('redirect-verify-badge--warn'), '僅回顯應使用警示樣式：' + echo);
    assert.ok(none.includes('redirect-verify-muted'), '沒有證據應顯示破折號：' + none);
    assert.notEqual(real, echo);
});

test('renderRedirectVerifyEvidence 舊資料沒有 evidence 欄位時仍能分辨僅回顯', () => {
    const { renderRedirectVerifyEvidence } = load();
    const legacyEcho = renderRedirectVerifyEvidence({ body_echo: true });
    const legacyNone = renderRedirectVerifyEvidence({});
    assert.ok(legacyEcho.includes('redirect-verify-badge--warn'), legacyEcho);
    assert.ok(legacyNone.includes('redirect-verify-muted'), legacyNone);
});

test('formatRedirectVerifyPercent 固定小數一位並處理非法值', () => {
    const { formatRedirectVerifyPercent } = load();
    assert.equal(formatRedirectVerifyPercent(50), '50.0%');
    assert.equal(formatRedirectVerifyPercent(33.333), '33.3%');
    assert.equal(formatRedirectVerifyPercent(0), '0.0%');
    assert.equal(formatRedirectVerifyPercent(undefined), '0%');
    assert.equal(formatRedirectVerifyPercent('abc'), '0%');
});
