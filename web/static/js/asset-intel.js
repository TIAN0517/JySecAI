// 資產情報 (Asset Intelligence) 頁面邏輯
// 橋接 asset_intelligence MCP 的 SQLite 資料庫，提供 FOFA + ZoomEye 資訊整合

const ASSET_INTEL_API_BASE = '/api/assets-intel';

// 載入所有 Asset Intel 數據
async function loadAssetIntelData() {
    try {
        const [providers, assets, history, quota] = await Promise.all([
            fetchJSON(`${ASSET_INTEL_API_BASE}/providers`),
            fetchJSON(`${ASSET_INTEL_API_BASE}`),
            fetchJSON(`${ASSET_INTEL_API_BASE}/history?limit=10`),
            fetchJSON(`${ASSET_INTEL_API_BASE}/quota`)
        ]);
        
        renderProviderStatus(providers);
        renderAssetSummary(assets?.stats || assets);
        renderAssetTable(assets?.items || [], history);
        renderHistory(history?.items || []);
    } catch (err) {
        console.error('Failed to load asset intel data:', err);
        showAiToast(uiT('assetIntel.loadFailed', '載入失敗: ') + err.message, 'error');
    }
}

// 供應商狀態渲染
function renderProviderStatus(providers) {
    const fofaDot = document.getElementById('fofa-status-dot');
    const fofaText = document.getElementById('fofa-status-text');
    const zoomeyeDot = document.getElementById('zoomeye-status-dot');
    const zoomeyeText = document.getElementById('zoomeye-status-text');
    
    if (!fofaDot || !fofaText || !zoomeyeDot || !zoomeyeText) return;
    
    const fofaConfigured = providers?.fofa?.configured;
    const zoomeyeConfigured = providers?.zoomeye?.configured;
    
    fofaDot.className = 'provider-status-dot ' + (fofaConfigured ? 'active' : 'inactive');
    fofaText.textContent = fofaConfigured ? uiT('assetIntel.connected', '已連接') : uiT('assetIntel.notConfigured', '未配置');
    
    zoomeyeDot.className = 'provider-status-dot ' + (zoomeyeConfigured ? 'active' : 'inactive');
    zoomeyeText.textContent = zoomeyeConfigured ? uiT('assetIntel.connected', '已連接') : uiT('assetIntel.notConfigured', '未配置');
}

// 資產總覽渲染
function renderAssetSummary(stats) {
    const total = document.getElementById('ai-stat-total');
    const ips = document.getElementById('ai-stat-ips');
    const domains = document.getElementById('ai-stat-domains');
    const updated = document.getElementById('ai-stat-updated');
    
    if (!total || !ips || !domains || !updated) return;
    
total.textContent = stats?.total_assets || stats?.total || 0;
ips.textContent = stats?.unique_ips || 0;
domains.textContent = stats?.unique_domains || 0;
    updated.textContent = stats?.last_updated ? new Date(stats.last_updated).toLocaleString() : '—';
}

// 資產表格渲染
function renderAssetTable(items, history) {
    const container = document.getElementById('ai-asset-table');
    if (!container) return;
    
    if (!items || items.length === 0) {
        container.innerHTML = uiT('assetIntel.emptyAssets', '<p class="muted">尚無資產數據，請先透過 MCP 或 API 查詢</p>');
        return;
    }
    
    let html = '<table class="ai-data-table"><thead><tr>';
    html += uiT('assetIntel.headFull', '<th>IP</th><th>域名</th><th>埠號</th><th>協議</th><th>服務</th><th>產品</th><th>國家</th><th>城市</th><th>來源</th><th>最後見識</th>');
    html += '</tr></thead><tbody>';
    
    items.slice(0, 100).forEach(item => {
        html += '<tr>';
        html += `<td>${escapeHtml(item.ip || '—')}</td>`;
        html += `<td>${escapeHtml(item.domain || '—')}</td>`;
        html += `<td>${item.port || '—'}</td>`;
        html += `<td>${escapeHtml(item.protocol || '—')}</td>`;
        html += `<td>${escapeHtml(item.service || '—')}</td>`;
        html += `<td>${escapeHtml(truncate(item.product, 20))}</td>`;
        html += `<td>${escapeHtml(item.country || '—')}</td>`;
        html += `<td>${escapeHtml(item.city || '—')}</td>`;
        html += `<td>${escapeHtml(item.source_providers || '—')}</td>`;
        html += `<td>${item.last_seen ? new Date(item.last_seen).toLocaleString() : '—'}</td>`;
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

// 查詢歷史渲染
function renderHistory(items) {
    const container = document.getElementById('ai-history-list');
    if (!container) return;
    
    if (!items || items.length === 0) {
        container.innerHTML = uiT('assetIntel.emptyHistory', '<p class="muted">尚無查詢歷史</p>');
        return;
    }
    
    let html = '<ul class="ai-history-ul">';
    items.forEach(item => {
        html += '<li class="ai-history-item">';
        html += `<span class="ai-history-time">${item.created_at ? new Date(item.created_at).toLocaleString() : '—'}</span>`;
        html += `<span class="ai-history-provider">${escapeHtml(item.provider || '—')}</span>`;
        html += `<span class="ai-history-query">${escapeHtml(truncate(item.query, 60))}</span>`;
        html += `<span class="ai-history-results">${item.results_count || 0} 筆結果</span>`;
        html += `<span class="ai-history-status ${item.ok ? 'success' : 'error'}">${item.ok ? '✓' : '✗'}</span>`;
        html += '</li>';
    });
    html += '</ul>';
    container.innerHTML = html;
}

// 搜尋資產
async function searchAssetIntel() {
    const ip = document.getElementById('ai-search-ip')?.value.trim();
    const domain = document.getElementById('ai-search-domain')?.value.trim();
    const service = document.getElementById('ai-search-service')?.value;
    const resultsContainer = document.getElementById('ai-search-results');
    
    if (!resultsContainer) return;
    if (!ip && !domain && !service) {
        showAiToast(uiT('assetIntel.needCondition', '請輸入至少一個搜尋條件'), 'warning');
        return;
    }
    
    resultsContainer.innerHTML = uiT('assetIntel.searching', '<p class="muted">搜尋中...</p>');
    
    const params = new URLSearchParams();
    if (ip) params.append('ip', ip);
    if (domain) params.append('domain', domain);
    if (service) params.append('service', service);
    
    try {
        const data = await fetchJSON(`${ASSET_INTEL_API_BASE}/search?${params.toString()}`);
        renderSearchResults(data?.items || []);
    } catch (err) {
        resultsContainer.innerHTML = `<p class="error">搜尋失敗: ${err.message}</p>`;
    }
}

// 搜尋結果渲染
function renderSearchResults(items) {
    const container = document.getElementById('ai-search-results');
    if (!container) return;
    
    if (!items || items.length === 0) {
        container.innerHTML = uiT('assetIntel.noMatch', '<p class="muted">未找到匹配的資產</p>');
        return;
    }
    
    let html = `<p class="muted">找到 ${items.length} 筆匹配</p><table class="ai-data-table"><thead><tr>`;
    html += uiT('assetIntel.headBase', '<th>IP</th><th>域名</th><th>埠號</th><th>協議</th><th>服務</th><th>產品</th><th>國家</th>');
    html += '</tr></thead><tbody>';
    
    items.forEach(item => {
        html += '<tr>';
        html += `<td>${escapeHtml(item.ip || '—')}</td>`;
        html += `<td>${escapeHtml(item.domain || '—')}</td>`;
        html += `<td>${item.port || '—'}</td>`;
        html += `<td>${escapeHtml(item.protocol || '—')}</td>`;
        html += `<td>${escapeHtml(item.service || '—')}</td>`;
        html += `<td>${escapeHtml(truncate(item.product || '', 20))}</td>`;
        html += `<td>${escapeHtml(item.country || '—')}</td>`;
        html += '</tr>';
    });
    
    html += '</tbody></table>';
    container.innerHTML = html;
}

// 通用函數 — 使用 apiFetch 以確保 Authorization header 正確附加
async function fetchJSON(url) {
    const resp = await apiFetch(url);
    if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
    }
    return await resp.json();
}

function truncate(str, maxLen) {
    if (!str) return '';
    return str.length > maxLen ? str.substring(0, maxLen) + '...' : str;
}

function showAiToast(message, type = 'info') {
    const existing = document.querySelector('.ai-toast-container');
    if (existing) existing.remove();
    
    const container = document.createElement('div');
    container.className = 'ai-toast-container';
    container.innerHTML = `<div class="ai-toast ai-toast-${type}">${message}</div>`;
    document.body.appendChild(container);
    
    setTimeout(() => {
        container.remove();
    }, 4000);
}

// 初始化
document.addEventListener('DOMContentLoaded', () => {
    if (currentPage === 'asset-intel') {
        loadAssetIntelData();
    }
});

// 暴露全域函數
window.loadAssetIntelData = loadAssetIntelData;
window.searchAssetIntel = searchAssetIntel;