const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = fs.existsSync('web/templates/index.html')
    ? process.cwd()
    : path.resolve(__dirname, '../../..');
const htmlPath = path.join(root, 'web/templates/index.html');
const cssPath = path.join(root, 'web/static/css/style.css');
const jsPath = path.join(root, 'web/static/js/monitor.js');

const html = fs.readFileSync(htmlPath, 'utf8');
const css = fs.readFileSync(cssPath, 'utf8');
const source = fs.readFileSync(jsPath, 'utf8');

function sectionIndex(className) {
    const marker = `class="monitor-section ${className}"`;
    const idx = html.indexOf(marker);
    assert.notEqual(idx, -1, `missing section ${className}`);
    return idx;
}

test('MCP 监控页 DOM 顺序为统计总览 → 禁用清单 → 执行记录', () => {
    const overview = sectionIndex('monitor-overview');
    const servers = sectionIndex('monitor-mcp-servers-section');
    const executions = sectionIndex('monitor-executions');
    assert.ok(overview < servers, 'overview must precede disabled/server inventory');
    assert.ok(servers < executions, 'server inventory must precede execution records');
    assert.doesNotMatch(
        html,
        /id="monitor-mcp-servers"\s+class="mcp-server-inventory"/,
        'mount node must not itself be the card grid'
    );
});

test('禁用清单 Grid 随容器变宽，外层挂载点不是 grid', () => {
    assert.match(css, /#monitor-mcp-servers\s*\{[^}]*display:\s*block/s);
    assert.match(css, /\.mcp-server-inventory\s*\{[^}]*grid-template-columns:\s*repeat\(5/s);
    assert.match(css, /@media \(max-width: 900px\)\s*\{\s*\.mcp-server-inventory\s*\{[^}]*repeat\(2/s);
    assert.match(css, /@media \(max-width: 640px\)\s*\{\s*\.mcp-server-inventory\s*\{[^}]*minmax\(0,\s*1fr\)/s);
    assert.match(css, /\.mcp-server-chip__reason\s*\{[^}]*overflow-wrap:\s*anywhere/s);
});

test('JS 不再把禁用清单插到 monitor-sections 的第一个子节点', () => {
    assert.doesNotMatch(source, /insertBefore\(wrap,\s*sections\.firstChild\)/);
    assert.match(source, /function placeMonitorMcpServersSection/);
    assert.match(source, /overview\.nextElementSibling === section/);
});

function harness() {
    const nodes = [];
    function el(tag, attrs = {}) {
        const node = {
            tagName: tag.toUpperCase(),
            className: attrs.className || '',
            id: attrs.id || '',
            _innerHTML: attrs.innerHTML || '',
            children: [],
            parentNode: null,
            classList: {
                remove(name) {
                    node.className = node.className.split(/\s+/).filter((c) => c && c !== name).join(' ');
                }
            },
            closest(sel) {
                let cur = node;
                while (cur) {
                    if (sel.startsWith('.') && cur.className.split(/\s+/).includes(sel.slice(1))) return cur;
                    cur = cur.parentNode;
                }
                return null;
            },
            querySelector(sel) {
                if (sel.startsWith('.')) {
                    const cls = sel.slice(1);
                    return node.children.find((c) => c.className.split(/\s+/).includes(cls)) || null;
                }
                if (sel.startsWith('#')) {
                    const id = sel.slice(1);
                    return node.children.find((c) => c.id === id) || null;
                }
                return null;
            },
            insertBefore(child, ref) {
                if (child.parentNode) {
                    const oldKids = child.parentNode.children;
                    const oldIdx = oldKids.indexOf(child);
                    if (oldIdx >= 0) oldKids.splice(oldIdx, 1);
                }
                const idx = ref ? node.children.indexOf(ref) : node.children.length;
                node.children.splice(idx < 0 ? node.children.length : idx, 0, child);
                child.parentNode = node;
            },
            appendChild(child) {
                node.insertBefore(child, null);
            },
            get nextSibling() {
                if (!node.parentNode) return null;
                const idx = node.parentNode.children.indexOf(node);
                return node.parentNode.children[idx + 1] || null;
            },
            get nextElementSibling() {
                return node.nextSibling;
            }
        };
        Object.defineProperty(node, 'innerHTML', {
            get() { return node._innerHTML || ''; },
            set(value) {
                node._innerHTML = String(value);
                const idMatch = String(value).match(/id="([^"]+)"/);
                if (idMatch && !node.children.some((c) => c.id === idMatch[1])) {
                    const child = el('div', { id: idMatch[1] });
                    node.children.push(child);
                    child.parentNode = node;
                }
            }
        });
        nodes.push(node);
        return node;
    }

    const overview = el('section', { className: 'monitor-section monitor-overview' });
    const executions = el('section', { className: 'monitor-section monitor-executions' });
    const sections = el('div', { className: 'monitor-sections' });
    sections.appendChild(overview);
    sections.appendChild(executions);
    const page = el('div', { id: 'page-mcp-monitor' });
    page.appendChild(sections);

    const document = {
        getElementById(id) {
            return nodes.find((n) => n.id === id) || null;
        },
        querySelector(sel) {
            if (sel === '#page-mcp-monitor .monitor-sections') return sections;
            return null;
        },
        createElement(tag) {
            return el(tag);
        }
    };

    const start = source.indexOf('function mcpDisabledReason');
    const end = source.indexOf('async function refreshMonitorMcpServers');
    const slice = source.slice(start, end);
    const context = vm.createContext({
        window: { t: null, __locale: 'zh-CN' },
        document,
        escapeHtml: (value) => String(value),
        mcpMonitorT: () => '',
    });
    vm.runInContext(slice, context);
    return { context, sections, overview, executions, document };
}

test('ensureMonitorMcpServersMount 把区块插到统计总览之后', () => {
    const { context, sections, overview, executions } = harness();
    const el = context.ensureMonitorMcpServersMount();
    assert.ok(el);
    assert.equal(sections.children[0], overview);
    assert.equal(sections.children[1].className.includes('monitor-mcp-servers-section'), true);
    assert.equal(sections.children[2], executions);
    assert.equal(el.className.includes('mcp-server-inventory'), false);
});

test('已存在但顺序错误的禁用清单会被搬到统计总览下方', () => {
    const { context, sections, overview, executions, document } = harness();
    const wrap = document.createElement('section');
    wrap.className = 'monitor-section monitor-mcp-servers-section';
    const mount = document.createElement('div');
    mount.id = 'monitor-mcp-servers';
    mount.className = 'mcp-server-inventory';
    wrap.appendChild(mount);
    sections.insertBefore(wrap, overview);
    assert.equal(sections.children[0], wrap);

    const el = context.ensureMonitorMcpServersMount();
    assert.equal(sections.children[0], overview);
    assert.equal(sections.children[1], wrap);
    assert.equal(sections.children[2], executions);
    assert.equal(el.className.includes('mcp-server-inventory'), false);
});

test('renderMonitorMcpServers 在挂载点内再包一层卡片 Grid，并保留禁用原因换行节点', () => {
    const { context } = harness();
    const el = context.ensureMonitorMcpServersMount();
    context.renderMonitorMcpServers({
        cloudflare: { status: 'disabled', config: { disabled_reason: '没有 Cloudflare API token，连上会 401' } },
        hexstrike: { status: 'connected', config: {} }
    }, { connected: 1, enabled: 1, disabled: 1, total: 2 });
    assert.match(el.innerHTML, /class="mcp-server-inventory"/);
    assert.match(el.innerHTML, /class="mcp-server-chip__reason"/);
    assert.match(el.innerHTML, /没有 Cloudflare API token/);
    assert.match(el.innerHTML, /is-disabled/);
});
