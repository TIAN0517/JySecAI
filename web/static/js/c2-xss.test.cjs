const fs = require('node:fs');
const test = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');

const source = fs.readFileSync('web/static/js/c2.js', 'utf8');

function between(startMarker, endMarker) {
    const start = source.indexOf(startMarker);
    const end = source.indexOf(endMarker, start);
    assert.notEqual(start, -1, `${startMarker} should exist`);
    assert.notEqual(end, -1, `${endMarker} should follow ${startMarker}`);
    return source.slice(start, end);
}

function escapeHelpers() {
    return between('function escapeHtml(', '/** 任务列表操作按钮');
}

function escapeContext() {
    let text = '';
    const document = {
        createElement() {
            return {
                set textContent(value) {
                    text = String(value).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
                },
                get innerHTML() { return text; }
            };
        }
    };
    return { document };
}

test('session info and file names escape special characters in text and attributes', () => {
    const special = `< > " ' &`;
    const ctx = vm.createContext({
        ...escapeContext(),
        C2: {},
        isEmptyInfoValue: (value) => value == null || String(value) === '',
        c2t: (key) => key
    });
    const renderFileList = between('C2.renderFileList = function(output) {', 'C2.refreshFiles = function() {')
        .replace(/^C2\.renderFileList = /, '').trim().replace(/;$/, '');
    vm.runInContext([
        escapeHelpers(),
        between('function sessionInfoRow(', 'function renderSessionInfoPanel('),
        `C2.renderFileList = ${renderFileList};`
    ].join('\n'), ctx);

    const sessionHTML = ctx.sessionInfoRow('Implant UUID', special, { copy: true });
    const fileContainer = { innerHTML: '' };
    ctx.document.getElementById = () => fileContainer;
    ctx.C2.parseLsLine = () => ({ name: special, isDir: false, size: 1, mode: 'file' });
    ctx.c2t = (key) => key;
    ctx.formatBytes = () => '1 B';
    ctx.C2.renderFileList('ignored');

    const escapedAttr = '&lt; &gt; &quot; &#39; &amp;';
    assert.match(sessionHTML, new RegExp(`data-c2-copy-value="${escapedAttr.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}"`));
    assert.match(sessionHTML, /&lt; &gt; " ' &amp;/);
    assert.match(fileContainer.innerHTML, /data-c2-file-name="&lt; &gt; &quot; &#39; &amp;"/);
    assert.match(fileContainer.innerHTML, /&lt; &gt; " ' &amp;/);
    assert.doesNotMatch(sessionHTML + fileContainer.innerHTML, /onclick\s*=/i);
});

test('C2 copy, directory-open, and download actions use delegated event handlers', () => {
    const listeners = {};
    const document = {
        documentElement: { dataset: {} },
        addEventListener(type, handler) { listeners[type] = handler; }
    };
    const calls = [];
    const C2 = {
        copyText: (value) => calls.push(['copy', value]),
        openDirectory: (value) => calls.push(['open', value]),
        downloadFile: (value) => calls.push(['download', value])
    };
    const ctx = vm.createContext({ document, C2 });
    vm.runInContext(between('function bindC2SafeActionDelegation()', 'function runC2SafeAction('), ctx);
    ctx.bindC2SafeActionDelegation();

    const special = `< > " ' &`;
    function click(button) {
        listeners.click({
            target: {
                closest(selector) {
                    if (selector === '[data-c2-copy-value]' && button.getAttribute('data-c2-copy-value') != null) return button;
                    if (selector === '[data-c2-file-action]' && button.getAttribute('data-c2-file-action') != null) return button;
                    return null;
                }
            },
            preventDefault() {},
            stopPropagation() {}
        });
    }
    click({ getAttribute: (name) => name === 'data-c2-copy-value' ? special : null });
    click({ getAttribute: (name) => ({
        'data-c2-file-action': 'open',
        'data-c2-file-name': special
    })[name] || null });
    click({ getAttribute: (name) => ({
        'data-c2-file-action': 'download',
        'data-c2-file-name': special
    })[name] || null });

    assert.deepEqual(calls, [['copy', special], ['open', special], ['download', special]]);
});

test('file-list API errors are escaped before they enter HTML', () => {
    const loadFileList = between('C2.loadFileList = function(sessionId, path) {', 'C2.waitForFileList = function(taskId, sessionId, path) {');
    assert.match(loadFileList, /escapeHtml\(data\.error\)/);
    assert.doesNotMatch(loadFileList, /\$\{data\.error\}/);
});
