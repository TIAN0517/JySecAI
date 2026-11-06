const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

// 登入閘的 session 持久性測試。
//
// 背景：舊版把「任何 API 回 401」都當成 session 過期，直接 clearAuthStorage()
// 清掉 localStorage 裡的 token；下一次按重新整理就因為沒有 token 而跳登入閘，
// 伺服器端的 session 其實還活著。這就是「按重新整理都會跳登入出來」的成因。
//
// 這支測試把行為釘死：
//   1. 單一端點 401（session 仍有效）→ 不得清掉 session
//   2. 單一端點 401（session 也失效）→ 必須登出
//   3. /api/auth/validate 自己回 401   → 必須登出
const source = fs.readFileSync('web/static/js/auth.js', 'utf8');

function load() {
    const store = new Map();
    const noop = () => {};
    const sandbox = {
        console,
        setTimeout: (fn) => { fn(); return 0; },
        clearTimeout: noop,
        setInterval: () => 0,
        clearInterval: noop,
        localStorage: {
            getItem: (k) => (store.has(k) ? store.get(k) : null),
            setItem: (k, v) => { store.set(k, String(v)); },
            removeItem: (k) => { store.delete(k); },
        },
        document: {
            addEventListener: noop,
            removeEventListener: noop,
            getElementById: () => null,
            querySelector: () => null,
            querySelectorAll: () => [],
            body: { classList: { add: noop, remove: noop, contains: () => false } },
        },
        openAppModal: noop,
        closeAppModal: noop,
        installPermissionClickGuard: noop,
        // Element 是瀏覽器全域；auth.js 的 applyRBACToUI 會用 `root instanceof Element`。
        Element: class Element {},
        Headers: class Headers {
            constructor(init) { this.map = new Map(Object.entries(init || {})); }
            has(k) { return this.map.has(k); }
            get(k) { return this.map.get(k); }
            set(k, v) { this.map.set(k, v); }
        },
    };
    sandbox.window = sandbox;
    sandbox.fetch = async () => ({ ok: true, status: 200, json: async () => ({}) });
    vm.createContext(sandbox);
    vm.runInContext(source, sandbox);
    return { sandbox, store };
}

function seedSession(sandbox) {
    sandbox.saveAuth('tok-1', new Date(Date.now() + 3600 * 1000).toISOString(), {
        user: { username: 'admin' },
        roles: ['admin'],
        permissions: ['dashboard:read'],
        scope: 'all',
    });
}

test('單一端點回 401 但 session 仍有效時，不得清掉 session', async () => {
    const { sandbox, store } = load();
    seedSession(sandbox);
    assert.ok(store.has('jysec-auth'), 'session should be persisted after login');

    sandbox.fetch = async (url) => {
        if (String(url).includes('/api/auth/validate')) {
            return { ok: true, status: 200, json: async () => ({ token: 'tok-1' }) };
        }
        return { ok: false, status: 401, json: async () => ({ error: 'unauthorized' }) };
    };

    await assert.rejects(() => sandbox.apiFetch('/api/config'), /未授权访问|unauthorized/);
    assert.ok(store.has('jysec-auth'), 'a single 401 must not wipe the persisted session');
});

test('單一端點回 401 且 session 也失效時，必須登出', async () => {
    const { sandbox, store } = load();
    seedSession(sandbox);

    sandbox.fetch = async () => ({ ok: false, status: 401, json: async () => ({ error: 'unauthorized' }) });

    await assert.rejects(() => sandbox.apiFetch('/api/config'));
    assert.equal(store.has('jysec-auth'), false, 'a dead session must be cleared');
});

test('/api/auth/validate 自己回 401 時，必須登出且不重複確認', async () => {
    const { sandbox, store } = load();
    seedSession(sandbox);

    let validateCalls = 0;
    sandbox.fetch = async (url) => {
        if (String(url).includes('/api/auth/validate')) {
            validateCalls += 1;
            return { ok: false, status: 401, json: async () => ({ error: '会话已过期' }) };
        }
        return { ok: true, status: 200, json: async () => ({}) };
    };

    await assert.rejects(() => sandbox.apiFetch('/api/auth/validate'));
    assert.equal(store.has('jysec-auth'), false, 'validate failure must clear the session');
    assert.equal(validateCalls, 1, 'validate must not be re-checked against itself');
});
