(function () {
    'use strict';

    const STORAGE_KEY = 'jysec-theme';
    const THEME_EVENT = 'jysec-themechange';
    const THEMES = ['system', 'light', 'dark'];
    const FALLBACK_LABELS = {
        system: '跟随系统',
        light: '浅色',
        dark: '暗色'
    };
    const FALLBACK_TITLES = {
        system: '当前：跟随系统主题。点击切换为浅色。',
        light: '当前：浅色主题。点击切换为暗色。',
        dark: '当前：暗色主题。点击切换为跟随系统。'
    };
    const TITLE_KEYS = {
        system: 'titleSystem',
        light: 'titleLight',
        dark: 'titleDark'
    };

    const EXACT_KEY_MIGRATIONS = [
        ['cyberstrike-theme', 'jysec-theme'],
        ['cyberstrike-auth', 'jysec-auth'],
        ['cyberstrike-chat-draft', 'jysec-chat-draft'],
        ['cyberstrike-chat-recent-conversations-expanded', 'jysec-chat-recent-conversations-expanded'],
        ['cyberstrike-chat-agent-mode', 'jysec-chat-agent-mode'],
        ['cyberstrike-chat-ai-channel', 'jysec-chat-ai-channel'],
        ['cyberstrike-chat-reasoning-mode', 'jysec-chat-reasoning-mode'],
        ['cyberstrike-chat-reasoning-effort', 'jysec-chat-reasoning-effort'],
        ['cyberstrike-chat-task-sync-v1', 'jysec-chat-task-sync-v1'],
        ['cyberstrike_hitl_logs_page_size', 'jysec_hitl_logs_page_size'],
        ['cyberstrike_hitl_pending_page_size', 'jysec_hitl_pending_page_size'],
        ['cyberstrike.asset_page_size', 'jysec.asset_page_size'],
        ['cyberstrike.asset_saved_views', 'jysec.asset_saved_views'],
        ['cyberstrike.projects_list_page_size', 'jysec.projects_list_page_size'],
        ['cyberstrike.project_assets_page_size', 'jysec.project_assets_page_size'],
        ['cyberstrike.activeProjectId', 'jysec.activeProjectId'],
        ['cyberstrike-project-folder-completion-seen', 'jysec-project-folder-completion-seen'],
        ['cyberstrike.conversations_page_size', 'jysec.conversations_page_size'],
        ['cyberstrike.conversations_sort_by', 'jysec.conversations_sort_by'],
        ['cyberstrike.conversations_project_filter', 'jysec.conversations_project_filter'],
        ['cyberstrike-notification-last-seen-at', 'jysec-notification-last-seen-at'],
        ['cyberstrike_audit_page_size', 'jysec_audit_page_size'],
        ['cyberstrike.dashboard.severityStatusFilter', 'jysec.dashboard.severityStatusFilter']
    ];
    const PREFIX_KEY_MIGRATIONS = [
        ['cyberstrike-chat-agent-mode:conversation', 'jysec-chat-agent-mode:conversation'],
        ['cyberstrike-chat-hitl:', 'jysec-chat-hitl:'],
        ['cyberstrike-hitl-timeout-default-v1:', 'jysec-hitl-timeout-default-v1:']
    ];

    function migrateJysecStorageKeys() {
        try {
            for (let i = 0; i < EXACT_KEY_MIGRATIONS.length; i++) {
                const from = EXACT_KEY_MIGRATIONS[i][0];
                const to = EXACT_KEY_MIGRATIONS[i][1];
                if (localStorage.getItem(to) != null) continue;
                const raw = localStorage.getItem(from);
                if (raw == null) continue;
                localStorage.setItem(to, raw);
                localStorage.removeItem(from);
            }
            const keys = [];
            for (let i = 0; i < localStorage.length; i++) {
                keys.push(localStorage.key(i));
            }
            for (let i = 0; i < keys.length; i++) {
                const key = keys[i];
                if (!key) continue;
                for (let j = 0; j < PREFIX_KEY_MIGRATIONS.length; j++) {
                    const fromPrefix = PREFIX_KEY_MIGRATIONS[j][0];
                    const toPrefix = PREFIX_KEY_MIGRATIONS[j][1];
                    if (key.indexOf(fromPrefix) !== 0) continue;
                    const to = toPrefix + key.slice(fromPrefix.length);
                    if (localStorage.getItem(to) == null) {
                        localStorage.setItem(to, localStorage.getItem(key));
                    }
                    localStorage.removeItem(key);
                    break;
                }
            }
        } catch (err) {
            /* ignore */
        }
    }

    migrateJysecStorageKeys();
    window.migrateJysecStorageKeys = migrateJysecStorageKeys;

    const media = window.matchMedia ? window.matchMedia('(prefers-color-scheme: dark)') : null;

    function themeText(key, fallback) {
        if (typeof window.t === 'function') {
            const value = window.t('theme.' + key);
            if (value && value !== 'theme.' + key) {
                return value;
            }
        }
        return fallback;
    }

    function getLabel(preference) {
        return themeText(preference, FALLBACK_LABELS[preference] || FALLBACK_LABELS.system);
    }

    function getTitle(preference) {
        const titleKey = TITLE_KEYS[preference] || TITLE_KEYS.system;
        return themeText(titleKey, FALLBACK_TITLES[preference] || FALLBACK_TITLES.system);
    }

    function normalizePreference(value) {
        return THEMES.includes(value) ? value : 'dark';
    }

    function readPreference() {
        try {
            return normalizePreference(localStorage.getItem(STORAGE_KEY));
        } catch (err) {
            return 'dark';
        }
    }

    function resolveTheme(preference) {
        if (preference === 'dark' || preference === 'light') {
            return preference;
        }
        return media && media.matches ? 'dark' : 'light';
    }

    function updateButton(preference, resolved) {
        const btn = document.getElementById('theme-toggle-btn');
        const label = document.getElementById('theme-toggle-label');
        if (!btn) {
            return;
        }
        btn.dataset.themePreference = preference;
        btn.dataset.theme = resolved;
        const title = getTitle(preference);
        btn.title = title;
        btn.setAttribute('aria-label', title);
        if (label) {
            label.textContent = getLabel(preference);
        }
    }

    function applyTheme(preference) {
        const normalized = normalizePreference(preference);
        const resolved = resolveTheme(normalized);
        const root = document.documentElement;
        root.setAttribute('data-theme-preference', normalized);
        root.setAttribute('data-theme', resolved);
        root.style.colorScheme = resolved;
        updateButton(normalized, resolved);
        document.dispatchEvent(
            new CustomEvent(THEME_EVENT, {
                detail: { preference: normalized, resolved: resolved },
            }),
        );
    }

    function savePreference(preference) {
        const normalized = normalizePreference(preference);
        try {
            localStorage.setItem(STORAGE_KEY, normalized);
        } catch (err) {
            // Ignore storage failures; the current page can still apply the theme.
        }
        applyTheme(normalized);
    }

    window.setThemePreference = savePreference;
    window.getThemePreference = readPreference;
    window.cycleThemePreference = function () {
        const current = readPreference();
        const next = THEMES[(THEMES.indexOf(current) + 1) % THEMES.length];
        savePreference(next);
    };
    window.refreshThemeToggleLabel = function () {
        applyTheme(readPreference());
    };

    if (media) {
        const onSystemThemeChange = function () {
            if (readPreference() === 'system') {
                applyTheme('system');
            }
        };
        if (typeof media.addEventListener === 'function') {
            media.addEventListener('change', onSystemThemeChange);
        } else if (typeof media.addListener === 'function') {
            media.addListener(onSystemThemeChange);
        }
    }

    document.addEventListener('languagechange', function () {
        applyTheme(readPreference());
    });

    function initTheme() {
        applyTheme(readPreference());
        if (window.i18nReady && typeof window.i18nReady.then === 'function') {
            window.i18nReady.then(function () {
                applyTheme(readPreference());
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initTheme);
    } else {
        initTheme();
    }
})();
