const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');

const source = fs.readFileSync('web/static/js/xss.js', 'utf8');
const { toDisplayText } = require('./xss.js');

test('special characters remain text and are never rendered through HTML sinks', () => {
    const value = `<img src=x onerror=alert(1)>"'&`;
    assert.equal(toDisplayText(value), value);
    // innerHTML 仅允许静态语言包（t() 返回自带文案，不是使用者输入；
    // 见 xss.js 中的安全注释），任何其他 innerHTML 赋值都是回归。
    const assignments = source.match(/\.innerHTML\s*=\s*[^;]+/g) || [];
    assert.ok(assignments.length > 0, 'expected the static i18n innerHTML assignment to exist');
    for (const line of assignments) {
        assert.match(line, /\.innerHTML\s*=\s*t\(/, `non-i18n innerHTML assignment: ${line.trim()}`);
    }
    assert.doesNotMatch(source, /\.outerHTML\s*=/);
    assert.doesNotMatch(source, /insertAdjacentHTML\s*\(/);
    assert.match(source, /cell\.textContent\s*=\s*toDisplayText\(value\)/);
    assert.match(source, /createTextNode\(toDisplayText\(entry\[1\]\)\)/);
});

test('dynamic action buttons use event listeners rather than inline handlers', () => {
    assert.doesNotMatch(source, /["'`]onclick\s*=/i);
    assert.match(source, /addEventListener\("click"/);
});

test('UI creates only constrained callback types', () => {
    assert.match(source, /type:\s*type/);
    assert.match(source, /ttl_seconds:\s*ttl/);
    assert.match(source, /one_time:\s*oneTime/);
    // 禁的是 Storage API 实际调用；语言包说明文字里出现 "localStorage" 单词不算。
    assert.doesNotMatch(source, /localStorage\s*[.[]/);
    assert.doesNotMatch(source, /sessionStorage\s*[.[]/);
});
