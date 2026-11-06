const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

const root = fs.existsSync('web/templates/index.html')
    ? process.cwd()
    : path.resolve(__dirname, '../../..');
const cssPath = path.join(root, 'web/static/css/style.css');
const jsPath = path.join(root, 'web/static/js/settings.js');
const htmlPath = path.join(root, 'web/templates/index.html');

const css = fs.readFileSync(cssPath, 'utf8');
const source = fs.readFileSync(jsPath, 'utf8');
const html = fs.readFileSync(htmlPath, 'utf8');

function extractFunction(name, nextName) {
    const start = source.indexOf(`function ${name}(`);
    assert.notEqual(start, -1, `missing ${name}`);
    const end = source.indexOf(`function ${nextName}(`, start + 1);
    assert.notEqual(end, -1, `missing terminator ${nextName}`);
    return source.slice(start, end);
}

test('禁用卡片不再用浅色 inline 背景，超时只在数值 > 0 时渲染', () => {
    assert.match(source, /class="external-mcp-disabled-reason"/);
    assert.doesNotMatch(source, /background: #f1f5f9/);
    assert.match(source, /Number\(server\.config && server\.config\.timeout\) > 0/);
    assert.match(source, /external-mcp-detail--wide/);
});

test('管理页字段网格用 1fr 填满宽度，长文本可换行', () => {
    assert.match(css, /\.external-mcp-item-details\s*\{[^}]*display:\s*flex/s);
    assert.match(
        css,
        /\.external-mcp-detail-row\s*\{[^}]*grid-template-columns:\s*repeat\(auto-fit,\s*minmax\(160px,\s*1fr\)\)/s
    );
    assert.match(css, /\.external-mcp-detail--wide\s*\{[^}]*width:\s*100%/s);
    assert.match(css, /\.external-mcp-disabled-reason\s*\{[^}]*overflow-wrap:\s*anywhere/s);
    assert.match(css, /\.external-mcp-item-details span\s*\{[^}]*overflow-wrap:\s*anywhere/s);
    assert.doesNotMatch(css, /minmax\(150px,\s*auto\)/);
});

test('MCP 管理页结构仍是工具配置 + 外部 MCP，未改 API 路径', () => {
    assert.match(html, /id="page-mcp-management"/);
    assert.match(html, /id="external-mcp-list"/);
    assert.match(source, /apiFetch\('\/api\/external-mcp'\)/);
    assert.match(source, /toggleExternalMCP\(/);
    assert.match(source, /editExternalMCP\(/);
    assert.match(source, /deleteExternalMCP\(/);
});

test('pentester-mcp 禁用卡：有禁用原因，timeout=300 显示秒数，无 timeout 不出现空标签', () => {
    function render(servers) {
        const document = {
            getElementById(id) {
                return this.nodes[id] || null;
            },
            querySelector() { return { classList: { add() {}, remove() {} } }; },
            nodes: { 'external-mcp-list': { innerHTML: '' } }
        };
        const ctx = {
            document,
            window: {
                t: (k) => ({
                    'mcp.disabled': '已禁用',
                    'mcp.start': '启动',
                    'mcp.startConnection': '启动连接',
                    'mcp.editConfig': '编辑配置',
                    'mcp.deleteConfig': '删除配置',
                    'mcp.transportMode': '传输模式',
                    'mcp.description': '描述',
                    'mcp.timeout': '超时时间',
                    'mcp.secondsUnit': '秒',
                    'mcp.command': '命令',
                    'mcpMonitor.disabledReasonLabel': '禁用原因：',
                    'common.edit': '编辑',
                    'common.delete': '删除'
                }[k] || k)
            },
            escapeHtml: (s) => String(s == null ? '' : s)
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;'),
            settingsEscapeAttr: (s) => String(s).replace(/"/g, '&quot;'),
            settingsEscapeJsStringAttr: (s) => JSON.stringify(String(s)),
            mcpDisabledReason: () => '程序目录不存在；kali-mcp + hexstrike 已覆盖同类工具',
            toolsExternalMcpFilter: '',
            updateExternalMcpCardSelection() {},
            servers
        };
        vm.runInNewContext(
            `${extractFunction('renderExternalMCPList', 'renderExternalMCPStats')}\nrenderExternalMCPList(servers);`,
            ctx
        );
        return document.nodes['external-mcp-list'].innerHTML;
    }

    const withTimeout = render({
        'pentester-mcp': {
            status: 'disabled',
            tool_count: 0,
            config: {
                type: 'stdio',
                command: '/opt/jysecai/pentester-mcp/.venv/bin/python',
                description: 'Pentester-MCP verified web reconnaissance and validation tools',
                timeout: 300
            }
        }
    });
    assert.match(withTimeout, /external-mcp-disabled-reason/);
    assert.match(withTimeout, /禁用原因：/);
    assert.match(withTimeout, /300 秒/);
    assert.match(withTimeout, /传输模式/);
    assert.match(withTimeout, /STDIO/);
    assert.match(withTimeout, /external-mcp-detail-row/);
    assert.match(withTimeout, /external-mcp-detail--wide/);
    assert.match(withTimeout, /toggleExternalMCP\("pentester-mcp"/);
    assert.match(withTimeout, /editExternalMCP\("pentester-mcp"\)/);
    assert.match(withTimeout, /deleteExternalMCP\("pentester-mcp"\)/);

    const noTimeout = render({
        'pentester-mcp': {
            status: 'disabled',
            config: {
                type: 'stdio',
                description: 'Pentester-MCP verified web reconnaissance and validation tools',
                timeout: 0
            }
        }
    });
    assert.doesNotMatch(noTimeout, /超时时间/);
    assert.match(noTimeout, /external-mcp-disabled-reason/);
});
