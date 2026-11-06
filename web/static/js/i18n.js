// 前端国际化初始化（基于 i18next 浏览器版本）
(function () {
    const DEFAULT_LANG = 'zh-CN';
    const STORAGE_KEY = 'csai_lang';
    const RESOURCES_PREFIX = '/static/i18n';

    const loadedLangs = {};

    // 供 bootstrap 等逻辑等待：避免 chat 在 t() 未就绪时用中文硬编码渲染，导致与语言标签不一致
    let i18nReadyResolve;
    window.i18nReady = new Promise(function (resolve) {
        i18nReadyResolve = resolve;
    });

    // ========================================================================
    // 共用前端工具（單一實作來源）
    //
    // 全站共用的工具集中在這裡：字串轉義、時間格式化、SSE 讀取、列表分頁解析。
    //
    // 選 i18n.js 當宿主的原因：index.html 與 api-docs.html 兩個頁面都會載入
    // i18n.js，而且它的 <script> 位置比各頁面自己的腳本都早（index.html 第 7893 行、
    // api-docs.html 第 1077 行）。index.html 不可修改，因此這是唯一能承載
    // 「所有頁面都需要」的工具的位置。
    //
    // 轉義語意：null / undefined 視為空字串；0、false 等 falsy 值原樣輸出。
    // escapeHtml 連引號一起轉義，因此可安全用在 HTML 文字與屬性兩種位置。
    // ========================================================================

    // escapeHtml：HTML 轉義（文字與屬性皆安全）。
    function escapeHtml(text) {
        if (text == null) return '';
        const div = document.createElement('div');
        div.textContent = String(text);
        return div.innerHTML.replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    // escapeAttr：HTML 屬性轉義。
    function escapeAttr(text) {
        return escapeHtml(text).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
    }

    // escapeJsString：轉成可安全嵌入 JS 字串常量的形式。
    function escapeJsString(text) {
        return JSON.stringify(String(text == null ? '' : text));
    }

    // escapeJsStringAttr：escapeJsString + HTML 屬性轉義（用於 onclick="..." 內）。
    function escapeJsStringAttr(text) {
        return escapeAttr(escapeJsString(text));
    }

    // tr：翻譯查不到詞條時回傳 fallback。
    function tr(key, fallback) {
        if (typeof window.t !== 'function') return fallback;
        const value = window.t(key);
        return !value || value === key ? fallback : value;
    }

    // toast：優先使用全域 showToast，其次 showNotification，最後落到 console。
    function toast(message, type) {
        const kind = type || 'info';
        if (typeof window.showToast === 'function') {
            window.showToast(message, kind);
            return;
        }
        if (typeof window.showNotification === 'function') {
            window.showNotification(message, kind);
            return;
        }
        if (kind === 'error') console.error(message);
    }

    // showToast：全域提示（沿用既有 showNotification → console 的 fallback 鏈）。
    function showToast(message, type) {
        const kind = type || 'info';
        if (typeof window.showNotification === 'function') {
            window.showNotification(message, kind);
            return;
        }
        if (kind === 'error') console.error(message);
        else console.log('[' + kind + ']', message);
    }

    // showError：最簡單的錯誤提示。
    function showError(message) {
        if (typeof window.alert === 'function') window.alert(String(message == null ? '' : message));
    }

    // setStatus：更新狀態列文字（可選加上 is-error 樣式）。
    function setStatus(node, message, isError) {
        if (!node) return;
        node.textContent = message == null ? '' : String(message);
        if (typeof node.classList !== 'undefined' && typeof node.classList.toggle === 'function') {
            node.classList.toggle('is-error', !!isError);
        }
    }

    // $：以 id 取元素。
    function byId(id) {
        return document.getElementById(id);
    }

    // lines：把多行文字拆成非空行陣列。
    function lines(value) {
        return String(value || '').split(/\r?\n/u).map((item) => item.trim()).filter(Boolean);
    }

    // esc：HTML 轉義別名（等同 escapeHtml）。
    function esc(value) {
        return escapeHtml(value);
    }

    // parseFlexibleDate：寬鬆解析時間字串（RFC3339 / SQLite / 本地時間格式）。
    function parseFlexibleDate(value) {
        if (value instanceof Date) return value;
        if (typeof value !== 'string') return new Date(value);
        let date = new Date(value);
        if (!Number.isNaN(date.getTime())) return date;
        // SQLite 格式："2006-01-02 15:04:05"（可能帶時區）
        const sqliteMatch = value.match(/(\d{4}-\d{2}-\d{2}[\sT]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[+-]\d{2}:\d{2}|Z)?)/);
        if (sqliteMatch) {
            let candidate = sqliteMatch[1].replace(' ', 'T');
            if (!candidate.includes('Z') && !candidate.match(/[+-]\d{2}:\d{2}$/)) candidate += 'Z';
            date = new Date(candidate);
            if (!Number.isNaN(date.getTime())) return date;
        }
        // 更寬鬆："YYYY-MM-DD HH:MM:SS"
        const match = value.match(/(\d{4})-(\d{2})-(\d{2})[\sT](\d{2}):(\d{2}):(\d{2})/);
        if (match) {
            return new Date(
                parseInt(match[1], 10),
                parseInt(match[2], 10) - 1,
                parseInt(match[3], 10),
                parseInt(match[4], 10),
                parseInt(match[5], 10),
                parseInt(match[6], 10)
            );
        }
        return date;
    }

    // formatDateTime：時間格式化。
    // options.empty：空值／無法解析時的預設文字（預設 '-'）。
    // options.locale：Intl locale。
    // options.intl：toLocaleString 的選項。
    // options.raw：無法解析時回傳原始字串。
    // options.strict：套用合理年份檢查（1970 ~ 2100），超出範圍視為空值。
    function formatDateTime(value, options) {
        const opts = options || {};
        const empty = opts.empty === undefined ? '-' : opts.empty;
        if (value == null || value === '') return empty;
        const date = parseFlexibleDate(value);
        if (!date || Number.isNaN(date.getTime())) {
            if (opts.raw) return String(value);
            if (opts.strict) console.warn('i18n: unparsable datetime value:', value);
            return empty;
        }
        if (opts.strict) {
            const year = date.getFullYear();
            if (year < 1970 || year > 2100) return empty;
        }
        if (opts.intl) return date.toLocaleString(opts.locale || 'zh-CN', opts.intl);
        return date.toLocaleString(opts.locale || undefined);
    }

    // formatDuration：毫秒轉可讀長度。
    // options.empty：空值時的預設文字（預設 '-'）。
    // options.keys：自訂語系 key（{ ms, sec, min }），未指定時用預設的中文格式。
    function formatDuration(ms, options) {
        const opts = options || {};
        const empty = opts.empty === undefined ? '-' : opts.empty;
        const value = Number(ms);
        if (!Number.isFinite(value) || value <= 0) return empty;
        if (opts.keys) {
            const keys = opts.keys;
            if (value < 1000) return window.t(keys.ms, { n: value });
            if (value < 60000) return window.t(keys.sec, { n: (value / 1000).toFixed(1) });
            return window.t(keys.min, { n: (value / 60000).toFixed(1) });
        }
        const seconds = Math.floor(value / 1000);
        const minutes = Math.floor(seconds / 60);
        const hours = Math.floor(minutes / 60);
        // 走語言包，不要在程式裡寫死語系（否則英文介面會混進中文單位）。
        if (hours > 0) {
            return window.t('common.duration.hours', { n: hours }) +
                window.t('common.duration.minutes', { n: minutes % 60 });
        }
        if (minutes > 0) {
            return window.t('common.duration.minutes', { n: minutes }) +
                window.t('common.duration.seconds', { n: seconds % 60 });
        }
        return window.t('common.duration.seconds', { n: seconds });
    }

    // readApiError：讀取後端錯誤訊息（回應格式 {"error": ..., "message": ...}）。
    async function readApiError(response, fallback) {
        const fallbackText = fallback === undefined ? '' : fallback;
        if (!response) return fallbackText;
        try {
            const body = await response.clone().json();
            return body.error || body.message || fallbackText;
        } catch (error) {
            return fallbackText;
        }
    }

    // parseListTotalValue：解析後端回傳的總筆數。
    function parseListTotalValue(raw, itemsLength) {
        if (typeof raw === 'number' && Number.isFinite(raw) && raw >= 0) return raw;
        if (raw != null && raw !== '') {
            const n = parseInt(String(raw), 10);
            if (Number.isFinite(n) && n >= 0) return n;
        }
        return itemsLength;
    }

    // parseListOffsetValue：解析後端回傳的位移量。
    function parseListOffsetValue(raw) {
        if (typeof raw === 'number' && Number.isFinite(raw) && raw >= 0) return raw;
        if (raw != null && raw !== '') {
            const n = parseInt(String(raw), 10);
            if (Number.isFinite(n) && n >= 0) return n;
        }
        return 0;
    }

    // readSse：讀取 SSE 回應，逐事件呼叫 onEvent(eventData)。
    // options.yieldEvery：每處理 N 行讓出一次主執行緒（避免單次 read() 塞爆 UI）。
    // options.onParseError：解析失敗時的自訂處理。
    async function readSse(response, onEvent, options) {
        const opts = options || {};
        if (!response || !response.body || typeof response.body.getReader !== 'function') return null;
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        const yieldEvery = opts.yieldEvery || 32;
        let buffer = '';

        const dispatch = async function (batch) {
            for (let i = 0; i < batch.length; i++) {
                const line = batch[i];
                if (line.startsWith('data: ')) {
                    try {
                        await onEvent(JSON.parse(line.slice(6)));
                    } catch (e) {
                        if (typeof opts.onParseError === 'function') opts.onParseError(e, line);
                        else console.error('i18n: failed to parse event data:', e, line);
                    }
                }
                if ((i + 1) % yieldEvery === 0 && i + 1 < batch.length) {
                    await new Promise(function (resolve) { requestAnimationFrame(resolve); });
                }
            }
        };

        while (true) {
            const chunk = await reader.read();
            if (chunk.done) break;
            buffer += decoder.decode(chunk.value, { stream: true });
            const batch = buffer.split('\n');
            buffer = batch.pop() || '';
            await dispatch(batch);
        }
        // Flush decoder internal buffer to avoid dropping trailing partial UTF-8 bytes.
        buffer += decoder.decode();
        if (buffer.trim()) {
            const batch = buffer.split('\n');
            await dispatch(batch);
        }
        return reader;
    }

    // 共用工具對外介面。
    window.JySecUI = {
        escapeHtml: escapeHtml,
        escapeAttr: escapeAttr,
        escapeJsString: escapeJsString,
        escapeJsStringAttr: escapeJsStringAttr,
        tr: tr,
        toast: toast,
        showToast: showToast,
        showError: showError,
        setStatus: setStatus,
        $: byId,
        lines: lines,
        esc: esc,
        formatDateTime: formatDateTime,
        formatDuration: formatDuration,
        readApiError: readApiError,
        parseListOffsetValue: parseListOffsetValue,
        parseListTotalValue: parseListTotalValue,
        readSse: readSse,
    };

    // 轉義與字串工具同時以全域函式提供，讓既有呼叫端（多數檔案直接呼叫
    // escapeHtml(...)）不必改成命名空間呼叫。
    window.escapeHtml = escapeHtml;
    window.escapeAttr = escapeAttr;
    window.escapeJsString = escapeJsString;
    window.escapeJsStringAttr = escapeJsStringAttr;

    // i18next 初始化完成前先回傳 key，讓各頁面在 DOMContentLoaded 之前呼叫也不會拋錯。
    // 原本各檔案靠自己的 _t shim 兜底，現在統一由 window.t 提供。
    let i18nInitialized = false;
    window.t = function (key, opts) {
        if (!i18nInitialized || typeof i18next === 'undefined') return key;
        return i18next.t(key, opts);
    };

    // uiT(key, fallback)：带后备值的翻译 helper。
    //
    // window.t 的第二参数是插值选项（opts），不能拿来当后备文案，所以页面里
    // 需要「查不到就退回原文」的场合一律走 uiT。语言包还没加载完时也退回
    // fallback，界面不会出现空白或露出 key。
    window.uiT = function (key, fallback) {
        try {
            if (window.i18next && typeof window.i18next.t === 'function') {
                const value = window.i18next.t(key, {});
                if (value && value !== key) return value;
            }
        } catch (e) { /* ignore */ }
        return fallback === undefined ? key : fallback;
    };

    function detectInitialLang() {
        try {
            const stored = localStorage.getItem(STORAGE_KEY);
            if (stored) {
                return stored;
            }
        } catch (e) {
            console.warn('无法读取语言设置:', e);
        }

        const navLang = (navigator.language || navigator.userLanguage || '').toLowerCase();
        if (navLang.startsWith('zh')) {
            return 'zh-CN';
        }
        if (navLang.startsWith('en')) {
            return 'en-US';
        }
        return DEFAULT_LANG;
    }

    async function loadLanguageResources(lang) {
        if (loadedLangs[lang]) {
            return;
        }
        try {
            const resp = await fetch(RESOURCES_PREFIX + '/' + lang + '.json', {
                cache: 'no-cache'
            });
            if (!resp.ok) {
                console.warn('加载语言包失败:', lang, resp.status);
                return;
            }
            const data = await resp.json();
            if (typeof i18next !== 'undefined') {
                i18next.addResourceBundle(lang, 'translation', data, true, true);
            }
            loadedLangs[lang] = true;
        } catch (e) {
            console.error('加载语言包异常:', lang, e);
        }
    }

    function applyTranslations(root) {
        if (typeof i18next === 'undefined') return;
        const container = root || document;
        if (!container) return;

        const elements = container.querySelectorAll('[data-i18n]');
        elements.forEach(function (el) {
            const key = el.getAttribute('data-i18n');
            if (!key) return;
            const skipText = el.getAttribute('data-i18n-skip-text') === 'true';
            const isFormControl = (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA');
            const attrList = el.getAttribute('data-i18n-attr');
            const translated = i18next.t(key);
            // 缺键时保留模板中的后备文案，避免页面直接显示 assets.project 一类内部键名。
            const text = translated && translated !== key ? translated : '';
            // 仅当元素无子元素（仅文本或空）时才替换文本，避免覆盖卡片内的数字、子节点等；input/textarea 永不设置 textContent
            const hasNoElementChildren = !el.querySelector('*');
            if (!skipText && !isFormControl && hasNoElementChildren && text && typeof text === 'string') {
                el.textContent = text;
            }

            if (attrList) {
                const titleKey = el.getAttribute('data-i18n-title');
                attrList.split(',').map(function (s) { return s.trim(); }).forEach(function (attr) {
                    if (!attr) return;
                    var val = text;
                    if (attr === 'title' && titleKey) {
                        var titleText = i18next.t(titleKey);
                        if (titleText && titleText !== titleKey && typeof titleText === 'string') val = titleText;
                    }
                    if (val && typeof val === 'string') {
                        el.setAttribute(attr, val);
                    }
                });
            }
        });

        // 对话输入框：若 value 与 placeholder 相同，清空 value 以便正确显示占位提示
        try {
            const chatInput = document.getElementById('chat-input');
            if (chatInput && chatInput.tagName === 'TEXTAREA') {
                const ph = (chatInput.getAttribute('placeholder') || '').trim();
                if (ph && chatInput.value.trim() === ph) {
                    chatInput.value = '';
                }
            }
        } catch (e) { /* ignore */ }

        // 更新 html lang 属性
        try {
            if (document && document.documentElement) {
                document.documentElement.lang = i18next.language || DEFAULT_LANG;
            }
        } catch (e) {
            // ignore
        }
    }

    function updateLangLabel() {
        const label = document.getElementById('current-lang-label');
        if (!label || typeof i18next === 'undefined') return;
        const lang = (i18next.language || DEFAULT_LANG).toLowerCase();
        if (lang.indexOf('zh') === 0) {
            label.textContent = i18next.t('lang.zhCN');
        } else {
            label.textContent = i18next.t('lang.enUS');
        }
    }

    function closeLangDropdown() {
        const dropdown = document.getElementById('lang-dropdown');
        if (dropdown) {
            dropdown.style.display = 'none';
        }
    }

    function handleGlobalClickForLangDropdown(ev) {
        const dropdown = document.getElementById('lang-dropdown');
        const btn = document.querySelector('.lang-switcher-btn');
        if (!dropdown || dropdown.style.display !== 'block') return;
        const target = ev.target;
        if (btn && btn.contains(target)) {
            return;
        }
        if (!dropdown.contains(target)) {
            closeLangDropdown();
        }
    }

    async function changeLanguage(lang) {
        if (typeof i18next === 'undefined') return;
        const current = i18next.language || DEFAULT_LANG;
        if (lang === current) return;
        await loadLanguageResources(lang);
        await i18next.changeLanguage(lang);
        try {
            localStorage.setItem(STORAGE_KEY, lang);
        } catch (e) {
            console.warn('无法保存语言设置:', e);
        }
        applyTranslations(document);
        updateLangLabel();
        if (typeof window.refreshThemeToggleLabel === 'function') {
            window.refreshThemeToggleLabel();
        }
        try {
            window.__locale = lang;
        } catch (e) { /* ignore */ }
        try {
            document.dispatchEvent(new CustomEvent('languagechange', { detail: { lang: lang } }));
        } catch (e) { /* ignore */ }
    }

    async function initI18n() {
        if (typeof i18next === 'undefined') {
            console.warn('i18next 未加载，跳过前端国际化初始化');
            if (typeof i18nReadyResolve === 'function') i18nReadyResolve();
            return;
        }

        const initialLang = detectInitialLang();
        await i18next.init({
            lng: initialLang,
            fallbackLng: DEFAULT_LANG,
            debug: false,
            resources: {}
        });

        await loadLanguageResources(initialLang);
        // 語系資源就緒後才讓 window.t 真正查表；在此之前一律回傳 key。
        i18nInitialized = true;
        applyTranslations(document);
        updateLangLabel();
        if (typeof window.refreshThemeToggleLabel === 'function') {
            window.refreshThemeToggleLabel();
        }
        try {
            window.__locale = i18next.language || initialLang;
        } catch (e) { /* ignore */ }

        // 导出全局函数供其他脚本调用（支持插值参数，如 window.t('key', { count: 2 })）
        window.changeLanguage = changeLanguage;
        window.applyTranslations = applyTranslations;

        // 语言切换下拉支持
        window.toggleLangDropdown = function () {
            const dropdown = document.getElementById('lang-dropdown');
            if (!dropdown) return;
            if (dropdown.style.display === 'block') {
                dropdown.style.display = 'none';
            } else {
                dropdown.style.display = 'block';
            }
        };
        window.onLanguageSelect = function (lang) {
            changeLanguage(lang);
            closeLangDropdown();
        };

        document.addEventListener('click', handleGlobalClickForLangDropdown);

        // 若 chat 已在 i18n 完成前用后备中文渲染了系统就绪消息，这里按当前语言纠正一次
        try {
            if (typeof refreshSystemReadyMessageBubbles === 'function') {
                refreshSystemReadyMessageBubbles();
            }
        } catch (e) { /* ignore */ }

        if (typeof i18nReadyResolve === 'function') i18nReadyResolve();
    }

    document.addEventListener('DOMContentLoaded', function () {
        // i18n 初始化在 DOM Ready 后执行
        initI18n().catch(function (e) {
            console.error('初始化国际化失败:', e);
            if (typeof i18nReadyResolve === 'function') i18nReadyResolve();
        });
    });
})();
