const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');

const source = fs.readFileSync('web/static/js/c2.js', 'utf8');
// 轉義 helper 現在是全站共用單一來源（web/static/js/i18n.js 的 window.escapeHtml /
// window.escapeAttr），c2.js 裡的本地副本已移除。這支測試要驗的是「XSS 轉義有沒有生效」，
// 所以 helper 要從真正的來源取，而不是從被改動的呼叫端取。
const i18nSource = fs.readFileSync('web/static/js/i18n.js', 'utf8');

function extractFunction(name, from) {
    const haystack = from || source;
    const marker = `function ${name}(`;
    const start = haystack.indexOf(marker);
    assert.notEqual(start, -1, `missing ${name}`);
    const brace = haystack.indexOf('{', start);
    let depth = 0;
    for (let i = brace; i < haystack.length; i += 1) {
        if (haystack[i] === '{') depth += 1;
        else if (haystack[i] === '}' && --depth === 0) return haystack.slice(start, i + 1);
    }
    throw new Error(`unterminated ${name}`);
}

function htmlDocument() {
    return {
        createElement() {
            let text = '';
            return {
                set textContent(value) { text = String(value); },
                get innerHTML() {
                    return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
                        .replace(/"/g, '&quot;').replace(/'/g, '&#39;');
                }
            };
        }
    };
}

test('copy values are escaped data attributes and never inline JavaScript', () => {
    const context = { document: htmlDocument(), result: '' };
    const payload = `"'><img src=x onerror=alert(1)>`;
    vm.runInNewContext([
        extractFunction('isEmptyInfoValue'),
        extractFunction('escapeHtml', i18nSource),
        extractFunction('escapeAttr', i18nSource),
        'function c2t() { return "Copy"; }',
        extractFunction('sessionInfoRow'),
        `result = sessionInfoRow('label', ${JSON.stringify(payload)}, { copy: true });`
    ].join('\n'), context);

    assert.match(context.result, /data-c2-copy-value=/);
    assert.doesNotMatch(context.result, /onclick\s*=/i);
    assert.doesNotMatch(context.result, /<img/i);
    assert.doesNotMatch(context.result, /data-c2-copy-value="[^"]*"'>/i);
    assert.match(context.result, /&lt;img/);
});

test('file actions use delegated data attributes and dynamic errors are escaped', () => {
    assert.doesNotMatch(source, /onclick\s*=\s*['"]C2\.(?:openDirectory|downloadFile)\([^)]*JSON\.stringify/i);
    assert.match(source, /data-c2-file-action=/);
    assert.match(source, /data-c2-file-name="\$\{escapeAttr\(entry\.name\)\}"/);
    assert.match(source, /<div class="c2-error">\$\{escapeHtml\(data\.error\)\}<\/div>/);
});
