## JySecAI 前端國際化方案

本文件說明 JySecAI Web 前端（`web/templates/index.html` + `web/static/js/*.js`）的國際化設計與開發規範，確保在不引入打包工具和不改動後端路由的前提下，實現可擴充套件、低返工的多語言支援。

當前目標：

- **支援中英文切換（zh-CN / en-US）**
- 後續可方便擴充套件更多語言（如 ja-JP、ko-KR 等）

---

## 一、總體設計原則

- **前端主導的客戶端國際化**：所有 UI 文案在瀏覽器端根據當前語言動態渲染，後端 Go 僅負責結構和資料，不參與語言分發。
- **單一 HTML 模板**：繼續使用一份 `index.html` 模板，不為不同語言複製模板檔案。
- **文案與邏輯分離**：所有可見文字透過「鍵值表」管理（多語言 JSON），HTML / JS 只寫 key，不直接寫中文/英文常量。
- **漸進式改造**：先覆蓋 header / 登入 / 側邊欄 / 系統設定等關鍵區域，其他頁面按模組逐步遷移，避免一次性大改動。
- **可回退預設語言**：即使目標語言未完全翻譯，也能回退到預設中文，不出現原始 key。

---

## 二、技術選型與目錄結構

### 2.1 技術選型

- **i18n 引擎**：使用 [i18next](https://www.i18next.com/) 的瀏覽器 UMD 版本（透過 CDN 引入），無需打包器。
- **資源格式**：每種語言一份 JSON 檔案，採用「域 + 語義」的層級 key 方案，例如：
  - `common.ok`
  - `nav.dashboard`
  - `header.apiDocs`
  - `settings.robot.wecom.token`

### 2.2 目錄結構

- `web/templates/index.html`  
  - 頁面骨架 + 所有靜態文案位置，將逐步改為 `data-i18n` 標記。
- `web/static/js/i18n.js`  
  - 前端 i18n 初始化與 DOM 應用邏輯（本方案新增）。
- `web/static/i18n/`（新增目錄）
  - `zh-CN.json`：中文文案（預設語言）
  - `en-US.json`：英文文案
  - 未來可新增：`ja-JP.json`、`ko-KR.json` 等。

---

## 三、文案組織規範

### 3.1 Key 命名約定

- 採用「**模組.語義**」形式，最多 2–3 級，確保可讀性：
  - 導航：`nav.dashboard`、`nav.chat`、`nav.settings`
  - 頭部：`header.title`、`header.apiDocs`、`header.logout`
  - 登入：`login.title`、`login.subtitle`、`login.passwordLabel`、`login.submit`
  - 儀表盤：`dashboard.title`、`dashboard.refresh`、`dashboard.runningTasks`
  - 系統設定：`settings.title`、`settings.nav.basic`、`settings.nav.robot`、`settings.apply`
  - 機器人配置：`settings.robot.wecom.enabled`、`settings.robot.wecom.token` 等。
- 儘量按「介面區域」而不是「檔名」劃分域，便於非開發人員理解。

### 3.2 JSON 示例

`web/static/i18n/zh-CN.json` 示例：

```json
{
  "common": {
    "ok": "確定",
    "cancel": "取消"
  },
  "nav": {
    "dashboard": "儀表盤",
    "chat": "對話",
    "infoCollect": "資訊收集",
    "tasks": "任務管理",
    "vulnerabilities": "漏洞管理",
    "settings": "系統設定"
  },
  "header": {
    "title": "JySecAI",
    "apiDocs": "API 文件",
    "logout": "退出登入",
    "language": "介面語言"
  },
  "login": {
    "title": "登入 JySecAI",
    "subtitle": "請輸入配置中的訪問密碼",
    "passwordLabel": "密碼",
    "passwordPlaceholder": "輸入登入密碼",
    "submit": "登入"
  }
}
```

英文檔案 `en-US.json` 保持相同 key，不同 value：

```json
{
  "common": {
    "ok": "OK",
    "cancel": "Cancel"
  },
  "nav": {
    "dashboard": "Dashboard",
    "chat": "Chat",
    "infoCollect": "Recon",
    "tasks": "Tasks",
    "vulnerabilities": "Vulnerabilities",
    "settings": "Settings"
  },
  "header": {
    "title": "JySecAI",
    "apiDocs": "API Docs",
    "logout": "Sign out",
    "language": "Interface language"
  },
  "login": {
    "title": "Sign in to JySecAI",
    "subtitle": "Enter the access password from config",
    "passwordLabel": "Password",
    "passwordPlaceholder": "Enter password",
    "submit": "Sign in"
  }
}
```

> 約定：**新增介面時，必須先定義 i18n key，再在 HTML/JS 中使用 key**，禁止直接寫死中文/英文。

---

## 四、HTML 標記規範（data-i18n）

### 4.1 基本規則

- 使用 `data-i18n` 將元素文字與某個 key 繫結：

```html
<span data-i18n="nav.dashboard">儀表盤</span>
```

- 預設行為：指令碼會替換元素的 `textContent`。
- 同時翻譯屬性時，額外使用 `data-i18n-attr`，逗號分隔多個屬性名：

```html
<button
  class="openapi-doc-btn"
  onclick="window.open('/api-docs', '_blank')"
  data-i18n="header.apiDocs"
  data-i18n-attr="title"
  title="API 文件">
  <span data-i18n="header.apiDocs">API 文件</span>
</button>
```

### 4.2 預設文字的作用

- HTML 內的中文預設值作為「**無 JS / 初始化前**」的佔位內容：
  - 頁面在 JS 尚未載入完成時不會出現空白或 key。
  - JS 初始化後會用當前語言覆蓋這些文字。

---

## 五、JavaScript 中的文案規範

### 5.1 全域性翻譯函式 `t()`

由 `i18n.js` 暴露以下全域性函式：

- `window.t(key: string): string`  
  - 返回當前語言下的翻譯文字，若缺失則回退到預設語言，再不行則返回 key 本身。
- `window.changeLanguage(lang: string): Promise<void>`  
  - 切換語言並重新整理頁面文案（不會重新整理整頁）。

示例（以 `web/static/js/settings.js` 為例）：

```js
// 之前
alert('載入配置失敗: ' + error.message);

// 之後
alert(t('settings.loadConfigFailed') + ': ' + error.message);
```

> 規範：**JS 內所有面向使用者的提示、按鈕文字、對話方塊標題都應透過 `t()` 獲取**，不直接寫死中文/英文。

### 5.2 漸進遷移建議

- 優先改造：
  - 頻繁彈出的錯誤提示 / 成功提示；
  - 登入相關、系統設定相關文案。
- 低優先順序：
  - 僅面向運維人員的除錯提示，可以暫時保留英文/中文常量。

---

## 六、i18n 初始化與語言切換實現

### 6.1 語言選擇策略

- 預設語言：`zh-CN`。
- 優先順序（從高到低）：
  1. `localStorage` 中的使用者選擇（key：`csai_lang`）。
  2. 瀏覽器 `navigator.language`（`zh` 開頭 → `zh-CN`，否則 `en-US`）。
  3. 預設 `zh-CN`。

### 6.2 初始化流程（`i18n.js`）

1. 讀取初始語言。
2. 初始化 i18next：
   - `lng` 為當前語言；
   - `fallbackLng` 為 `zh-CN`；
   - 資源先留空，採用按需載入。
3. 透過 `fetch` 拉取 `/static/i18n/{lng}.json` 並 `i18next.addResources`。
4. 更新：
   - `<html lang="...">` 屬性；
   - 所有帶 `data-i18n` / `data-i18n-attr` 的元素。
5. 暴露 `window.t` 與 `window.changeLanguage`。

### 6.3 DOM 應用邏輯

虛擬碼：

```js
function applyTranslations(root = document) {
  const elements = root.querySelectorAll('[data-i18n]');
  elements.forEach(el => {
    const key = el.getAttribute('data-i18n');
    if (!key) return;
    const text = i18next.t(key);
    if (text) {
      el.textContent = text;
    }

    const attrList = el.getAttribute('data-i18n-attr');
    if (attrList) {
      attrList.split(',').map(s => s.trim()).forEach(attr => {
        if (!attr) return;
        const val = i18next.t(key);
        if (val) el.setAttribute(attr, val);
      });
    }
  });
}
```

> 對於由 JS 動態插入的元素，需要在插入後再次呼叫 `applyTranslations(新容器)`。

---

## 七、語言切換 UI 規範

### 7.1 位置與形態

- 位置：`index.html` header 右側 `API 文件` 按鈕附近（靠近使用者頭像）。
- 互動形式：
  - 一個緊湊的語言切換元件，例如：
    - `🌐` 圖示 + 當前語言文字（`中文` / `English`）的下拉按鈕；
    - 下拉內容列出所有可用語言。

### 7.2 示例結構

```html
<div class="lang-switcher">
  <button class="btn-secondary lang-switcher-btn" onclick="toggleLangDropdown()" data-i18n="header.language">
    <span class="lang-switcher-icon">🌐</span>
    <span id="current-lang-label">中文</span>
  </button>
  <div id="lang-dropdown" class="lang-dropdown" style="display: none;">
    <div class="lang-option" data-lang="zh-CN" onclick="onLanguageSelect('zh-CN')">中文</div>
    <div class="lang-option" data-lang="en-US" onclick="onLanguageSelect('en-US')">English</div>
  </div>
</div>
```

對應 JS（在 `i18n.js` 中）：

```js
function onLanguageSelect(lang) {
  changeLanguage(lang).then(updateLangLabel).catch(console.error);
  closeLangDropdown();
}

function updateLangLabel() {
  const labelEl = document.getElementById('current-lang-label');
  if (!labelEl) return;
  const lang = i18next.language || 'zh-CN';
  labelEl.textContent = lang.startsWith('zh') ? '中文' : 'English';
}
```

> 規範：**語言切換隻更新文案，不重新整理整頁，也不修改 URL hash**。

---

## 八、開發流程建議

### 8.1 新增 / 修改介面的流程

1. 設計介面時，先列出所有文案。
2. 在對應語言 JSON 中補充/修改 key 與翻譯。
3. 在 HTML 中使用 `data-i18n`，在 JS 中使用 `t('...')`。
4. 在瀏覽器中切換中英文，確認兩種語言顯示都正確。

### 8.2 漸進式改造順序（推薦）

1. **階段 1（已規劃）**
   - 引入 i18next 與 `i18n.js`。
   - 新建 `zh-CN.json` / `en-US.json`（先覆蓋 header / 登入 / 左側導航）。
   - 實現 header 區域語言切換元件。
2. **階段 2**（已完成）
   - 系統設定頁面（包括機器人配置頁面）全部文案 i18n 化。
   - `settings.js` 中的提示與錯誤資訊改用 `t()`。
3. **階段 3**（進行中）
   - 儀表盤、任務管理、漏洞管理、MCP、Skills、Roles 等頁面按模組逐步遷移。
4. **階段 4**
   - 清理 JS / HTML 中殘留的硬編碼中文，統一透過 i18n。

---

## 九、後續擴充套件新語言

當需要新增語言時：

1. 在 `web/static/i18n/` 中新增 `{lang}.json`，複製現有英文/中文檔案結構，補充對應翻譯。
2. 在語言切換下拉中新增對應選項，例如：
   - `data-lang="ja-JP"` / 文字 `日本語`
3. 無需修改 `i18n.js` 或現有 HTML/JS 邏輯，即可支援新語言。

---

## 十、注意事項與坑點

- **不要複製多份 HTML 模板** 來做多語言，那樣維護成本極高，本方案統一由前端 i18n 控制。
- **避免 key 直接用中文/英文句子**，統一採用「模組.語義」短 key，便於 diff 與搜尋。
- 避免在 CSS 中寫死文字（如 `content: "xxx"`），如確有需要，應透過 JS 設定並走 i18n。
- 對於後端返回的可本地化錯誤文字（未來可能支援），優先由後端根據 `Accept-Language` 返回對應語言，前端只負責展示。

