// Rich UUID XSS management. API/DB strings are always rendered as text.
var XSS = (function () {
    'use strict';
    const module = {};
    const el = id => document.getElementById(id);
    const text = value => value == null ? '' : String(value);
    function node(tag, value) {
        const n = document.createElement(tag);
        if (value != null) n.textContent = text(value);
        return n;
    }
    function error(err) { el('xss-status-text').textContent = 'XSS: ' + text(err.message || err); }
    async function api(path, options = {}) {
        const res = await apiFetch('/api/xss' + path, {
            credentials: 'same-origin', ...options,
            headers: { 'Content-Type': 'application/json', ...(options.headers || {}) }
        });
        if (!res.ok) throw new Error('Request failed: HTTP ' + res.status);
        return res.json();
    }
    function modal(id) { el(id).style.display = 'flex'; }
    module.closeModal = function (element) {
        const target = typeof element === 'string' ? el(element) : element.closest('.xss-modal-overlay');
        if (target) target.style.display = 'none';
    };
    function action(label, permission, fn) {
        const b = node('button', label);
        b.type = 'button'; b.className = 'btn-secondary btn-sm';
        b.dataset.requirePermission = permission;
        b.addEventListener('click', () => Promise.resolve().then(fn).catch(error));
        return b;
    }
    function permissions() { if (typeof applyRBACToUI === 'function') applyRBACToUI(el('page-xss')); }
    function row(values) { const r = node('tr'); values.forEach(v => r.appendChild(node('td', v))); return r; }
    module.loadPayloads = async function () {
        const data = await api('/payloads');
        const list = el('xss-payload-list'); list.replaceChildren();
        (data.payloads || []).forEach(p => {
            const r = row([p.name, p.source_url, p.status, p.created_at]);
            const cell = node('td');
            cell.appendChild(action('Script', 'xss:read', async () => {
                const d = await api('/payloads/' + encodeURIComponent(p.id));
                el('xss-script-text').value = text(d.payload.script); modal('xss-script-modal');
            }));
            cell.appendChild(action('Delete', 'xss:delete', async () => {
                if (!window.confirm('Delete this payload? Historical captures are retained.')) return;
                await api('/payloads/' + encodeURIComponent(p.id), {method: 'DELETE'}); await module.loadPayloads();
            }));
            r.appendChild(cell); list.appendChild(r);
        });
        el('xss-payload-count').textContent = text(data.total);
        el('xss-payload-empty').hidden = !!data.total; permissions();
    };
    module.openGenerateModal = function () { modal('xss-generate-modal'); };
    module.generatePayload = async function () {
        try {
            const d = await api('/payloads/generate', {method: 'POST', body: JSON.stringify({
                name: el('xss-generate-name').value, source_url: el('xss-generate-source').value,
                domain: el('xss-generate-domain').value, domain_only: el('xss-generate-domain-only').checked
            })});
            module.closeModal('xss-generate-modal');
            el('xss-script-text').value = text(d.payload.script); modal('xss-script-modal');
            await module.loadPayloads();
        } catch (err) { error(err); }
    };
    module.copyScript = async function () {
        try { await navigator.clipboard.writeText(el('xss-script-text').value); } catch (err) { error(err); }
    };
    function detail(label, value) {
        const section = node('section'); section.appendChild(node('h4', label));
        section.appendChild(node('pre', typeof value === 'object' ? JSON.stringify(value, null, 2) : value));
        return section;
    }
    module.showCapture = async function (id) {
        const d = await api('/captures/' + encodeURIComponent(id));
        const c = d.capture, body = el('xss-detail-body'); body.replaceChildren();
        ['id','payload_id','project_id','conversation_id','source_url','page_title','user_agent',
            'client_ip','url_fragment','status','cookies','local_storage','session_storage','api_keys',
            'created_at','updated_at'].forEach(k => body.appendChild(detail(k, c[k])));
        modal('xss-detail-modal');
    };
    module.loadCaptures = async function () {
        try {
            const data = await api('/captures?status=' + encodeURIComponent(el('xss-capture-status').value));
            const list = el('xss-capture-list'); list.replaceChildren();
            (data.captures || []).forEach(c => {
                const r = row([c.created_at, c.source_url, c.page_title, (c.cookies || []).length, c.status]);
                const cell = node('td');
                cell.appendChild(action('Details', 'xss:read', () => module.showCapture(c.id)));
                const select = node('select'); select.dataset.requirePermission = 'xss:write';
                ['new','seized','analyzed','ignored'].forEach(s => {
                    const option = node('option', s); option.value = s; select.appendChild(option);
                });
                select.value = text(c.status);
                select.addEventListener('change', async () => {
                    try { await api('/captures/' + encodeURIComponent(c.id) + '/status', {
                        method:'PUT', body:JSON.stringify({status:select.value})}); await module.loadCaptures(); }
                    catch (err) { select.value = text(c.status); error(err); }
                });
                cell.appendChild(select);
                cell.appendChild(action('Delete', 'xss:delete', async () => {
                    if (!window.confirm('Delete this capture?')) return;
                    await api('/captures/' + encodeURIComponent(c.id), {method:'DELETE'}); await module.loadCaptures();
                }));
                r.appendChild(cell); list.appendChild(r);
            });
            el('xss-capture-count').textContent = text(data.total);
            el('xss-capture-empty').hidden = !!data.total; permissions();
        } catch (err) { error(err); throw err; }
    };
    async function config() {
        const d = await api('/config');
        el('xss-status-text').textContent = d.enabled ? 'Collector enabled' : 'Collector disabled';
        el('xss-config-enabled').checked = !!d.enabled; el('xss-config-enabled').disabled = true;
        el('xss-config-bind').value = text(d.bind_host) + ':' + text(d.bind_port);
        el('xss-config-url').value = text(d.public_url);
        el('xss-config-cooldown').value = text(d.cooldown_seconds); return d;
    }
    module.showConfig = async function () {
        try { await config(); modal('xss-config-modal'); } catch (err) { error(err); }
    };
    module.saveConfig = function () { error(new Error('Configuration is read-only; changes require deployment review.')); };
    module.init = async function () {
        try { await Promise.all([config(), module.loadPayloads(), module.loadCaptures()]); }
        catch (err) { error(err); }
    };
    return module;
}());
