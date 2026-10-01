const fs = require('node:fs');
const test = require('node:test');
const assert = require('node:assert/strict');

const c2 = fs.readFileSync('web/static/js/c2.js', 'utf8');
const zh = JSON.parse(fs.readFileSync('web/static/i18n/zh-CN.json', 'utf8'));
const en = JSON.parse(fs.readFileSync('web/static/i18n/en-US.json', 'utf8'));

// ---------------------------------------------------------------------------
// XSS：任何送進 innerHTML 的错误文案都必须先 escapeHtml。
//
// 背景：c2.js 的档案清单在载入失败时把 data.error 直接插进 innerHTML，
// 而同一个函式里其他错误路径（2817 / 3665 / 3667）都已经 escapeHtml ——
// 这一处是漏网的。服务端回传的错误可能带上 beacon 端的主机名、路径或命令输出，
// 未经 escape 就等于把控制权交给内容。
// ---------------------------------------------------------------------------

test('档案清单的错误提示经过 escapeHtml', () => {
    assert.match(c2, /escapeHtml\(data\.error\)/);
});

// 通用防回归：innerHTML 赋值中不得出现未经转义的 error 插值。
test('innerHTML 赋值中没有未转义的 error 插值', () => {
    const offenders = c2.match(/innerHTML\s*=\s*`[^`]*`/g) || [];
    for (const snippet of offenders) {
        // 抓出所有 ${...} 片段，确认每个都走 escapeHtml / escapeAttr / c2t。
        const interpolations = snippet.match(/\$\{[^}]*\}/g) || [];
        for (const expr of interpolations) {
            const safe =
                /\$\{\s*escapeHtml\(/.test(expr) ||
                /\$\{\s*escapeAttr\(/.test(expr) ||
                /\$\{\s*c2t\(/.test(expr);
            if (!safe && /error/i.test(expr)) {
                assert.fail(`innerHTML 中存在未转义的 error 插值: ${expr}\n  片段: ${snippet}`);
            }
        }
    }
});

// term.writeln 走的是 xterm.js 终端缓冲，不是 innerHTML，因此不需要 escapeHtml。
// 这里固定该前提，避免日后有人把终端输出改成 innerHTML 渲染时静默失去这层判断。
test('终端输出仍走 xterm 而非 innerHTML', () => {
    assert.match(c2, /term\.writeln\(`\\x1b\[31mError: \$\{data\.error\}/);
    assert.doesNotMatch(c2, /innerHTML\s*=\s*`[^`]*\$\{task\.error\}`/);
});

// ---------------------------------------------------------------------------
// 明文 Beacon 交互必须显式 opt-in。
// ---------------------------------------------------------------------------

test('未开启 opt-in 时 check-in 拒绝明文', () => {
    assert.match(c2, /c2\.listeners\.allowPlaintextCheckIn/);
});

test('明文 Beacon 开关的中英文案齐备且说明风险', () => {
    const zhLabel = zh.c2.listeners.allowPlaintextCheckIn;
    const zhHint = zh.c2.listeners.allowPlaintextCheckInHint;
    const enLabel = en.c2.listeners.allowPlaintextCheckIn;
    const enHint = en.c2.listeners.allowPlaintextCheckInHint;

    assert.equal(typeof zhLabel, 'string');
    assert.equal(typeof zhHint, 'string');
    assert.equal(typeof enLabel, 'string');
    assert.equal(typeof enHint, 'string');

    // 提示必须说明「默认关闭」，否则使用者会误以为这是安全默认值。
    assert.match(zhHint, /默认关闭/);
    assert.match(enHint, /Off by default/);
    // 也必须点明代价：内容会以明文过链路。
    assert.match(zhHint, /明文/);
    assert.match(enHint, /plaintext/i);
});

test('开关只在 http / https 类型下显示，且与 legacy shell 各自独立', () => {
    assert.match(c2, /lt === 'http' \|\| lt === 'https'[\s\S]{0,400}c2-listener-plaintext-checkin/);
    assert.match(c2, /if \(legacyEl \|\| plaintextEl\)/);
    assert.match(c2, /merged\.allow_plaintext_checkin = plaintextEl\.checked === true/);
    // 两个开关不能互相覆盖：保存 legacy shell 时不得把 plaintext 设为 false。
    assert.match(c2, /merged\.allow_legacy_shell = legacyEl\.checked === true/);
});
