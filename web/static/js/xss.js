// Safe callback UI: XSS canary verification plus one-time SSRF/XXE probes.
var XSS = (function () {
	"use strict";

	var apiObject = {};
	var currentPayloads = [];
	var currentCaptures = [];
	var refreshTimer = null;

	function toDisplayText(value) {
		return value === null || value === undefined ? "" : String(value);
	}

	// 与 assets.js 的 assetT 同一套约定（key, fallback, options）：取不到语言包
	// 时回退到硬编码中文，绝不把 "xss.colName" 这类内部键名显示给使用者，也不
	// 让界面出现空白——语言包是异步加载的，首屏很容易先于它渲染完成。
	function t(key, fallback, options) {
		if (window.i18next && typeof window.i18next.t === "function") {
			var value = window.i18next.t(key, options || {});
			if (value && value !== key) return value;
		}
		return fallback === undefined ? "" : fallback;
	}

	// 含 <code> 的提示句无法用 data-i18n 翻译——applyTranslations 只替换「没有
	// 子元素」的节点，带 <code> 的段落会被跳过。这里自行注入：译文来自本项目
	// 自带的语言包（不是使用者输入），因此使用 innerHTML 是安全的。
	function applyHintMarkup(elementId, key, fallbackHTML, options) {
		var el = document.getElementById(elementId);
		if (!el) return;
		el.innerHTML = t(key, fallbackHTML, options);
	}

	apiObject.applyStaticTranslations = function () {
		applyHintMarkup(
			"xss-script-hint",
			"xss.scriptHint",
			'将以下脚本植入目标页面的 XSS 触发点（如 <code>&lt;img src=x onerror=…&gt;</code>、事件属性、URL 参数注入点）。目标浏览器打开后会自动回连收集服务。XSS 模式只收割 <code>jysec_*</code> 测试 Canary，不会回连登录或工作会话 Cookie；探针模式只记录一次交互，不保存请求内容。',
			{ canary: "<code>jysec_*</code>" }
		);
		applyHintMarkup(
			"xss-config-hint",
			"xss.configHint",
			'启用后，生成的载荷即可回连收割 Cookie / localStorage / sessionStorage。需同时配置 <code>public_url</code> 为公网/内网可达地址。安全模式只允许 <code>jysec_*</code> Canary；SSRF / XXE 探针为一次性且不保存 Header、Body、Cookie 或查询参数。',
			{ canary: "<code>jysec_*</code>" }
		);
	};

	async function request(path, options) {
		var opts = options || {};
		var headers = new Headers(opts.headers || {});
		if (opts.body && !headers.has("Content-Type")) {
			headers.set("Content-Type", "application/json");
		}
		opts.headers = headers;
		var fetcher = typeof apiFetch === "function" ? apiFetch : fetch;
		var response = await fetcher("/api" + path, opts);
		var data = null;
		try {
			data = await response.json();
		} catch (_) {
			data = {};
		}
		if (!response.ok) {
			throw new Error(data.error || ("HTTP " + response.status));
		}
		return data;
	}

	function clear(element) {
		if (element) element.replaceChildren();
	}

	function appendCell(row, value, className) {
		var cell = document.createElement("td");
		if (className) cell.className = className;
		var text = toDisplayText(value);
		cell.textContent = toDisplayText(value);
		if (className === "cookie-cell" || className === "xss-clip") {
			cell.title = text;
			cell.classList.add("xss-clip");
		}
		row.appendChild(cell);
		return cell;
	}

	function statusKind(payload) {
		if (!payload.enabled) return "muted";
		if (payload.consumed_at) return "used";
		if (payload.expires_at && new Date(payload.expires_at).getTime() <= Date.now()) return "expired";
		return "ok";
	}

	function putBadge(cell, text, kind) {
		var badge = document.createElement("span");
		badge.className = "xss-badge xss-badge--" + kind;
		badge.textContent = text;
		cell.replaceChildren(badge);
	}

	function setEmpty(wrapId, empty, isEmpty) {
		if (empty) empty.hidden = !isEmpty;
		var wrap = document.getElementById(wrapId);
		if (wrap) wrap.classList.toggle("is-empty", isEmpty);
	}

	function formatTime(value) {
		if (!value) return "—";
		var date = new Date(value);
		return Number.isNaN(date.getTime()) ? toDisplayText(value) : date.toLocaleString();
	}

	function statusText(payload) {
		if (!payload.enabled) return t("xss.statusDisabled", "已停用");
		if (payload.consumed_at) return t("xss.statusUsed", "已使用");
		if (payload.expires_at && new Date(payload.expires_at).getTime() <= Date.now()) return t("xss.statusExpired", "已过期");
		return t("xss.statusAvailable", "可用");
	}

	function typeLabel(type) {
		return type === "probe" ? t("xss.labelProbe", "SSRF/XXE 探针") : t("xss.labelCanary", "XSS Canary");
	}

	function showError(prefix, error) {
		window.alert(prefix + ": " + (error && error.message ? error.message : error));
	}

	apiObject.closeModal = function (source) {
		var overlay = source && source.classList && source.classList.contains("xss-modal-overlay")
			? source
			: source && source.closest ? source.closest(".xss-modal-overlay") : null;
		if (overlay) overlay.style.display = "none";
	};

	apiObject.openGenerateModal = function () {
		var modal = document.getElementById("xss-generate-modal");
		if (!modal) return;
		document.getElementById("xss-generate-name").value = "";
		document.getElementById("xss-generate-source").value = "";
		document.getElementById("xss-generate-type").value = "image";
		document.getElementById("xss-generate-ttl").value = "3600";
		document.getElementById("xss-generate-one-time").checked = true;
		modal.style.display = "flex";
	};

	apiObject.generatePayload = async function () {
		var name = document.getElementById("xss-generate-name").value.trim();
		var domain = document.getElementById("xss-generate-source").value.trim();
		var type = document.getElementById("xss-generate-type").value;
		var ttl = Number(document.getElementById("xss-generate-ttl").value || 3600);
		var oneTime = document.getElementById("xss-generate-one-time").checked;
		if (!name) {
			window.alert(t("xss.errNameRequired", "请输入名称"));
			return;
		}
		try {
			var data = await request("/xss/payloads", {
				method: "POST",
				body: JSON.stringify({ name: name, type: type, domain: domain, ttl_seconds: ttl, one_time: oneTime }),
			});
			apiObject.closeModal(document.getElementById("xss-generate-modal"));
			var output = data.type === "probe"
				? data.public_url
				: '<script src="' + data.public_url + '"></' + "script>";
			document.getElementById("xss-script-text").value = output;
			document.getElementById("xss-script-modal").style.display = "flex";
			await apiObject.loadPayloads();
		} catch (error) {
			showError(t("xss.errCreateCallback", "生成接管载荷失败"), error);
		}
	};

	apiObject.loadPayloads = async function () {
		try {
			var data = await request("/xss/payloads");
			currentPayloads = Array.isArray(data.payloads) ? data.payloads : [];
			var body = document.getElementById("xss-payload-list");
			var empty = document.getElementById("xss-payload-empty");
			clear(body);
			document.getElementById("xss-payload-count").textContent = String(currentPayloads.length);
			setEmpty("xss-payload-wrap", empty, currentPayloads.length === 0);
			currentPayloads.forEach(function (payload) {
				var row = document.createElement("tr");
				appendCell(row, payload.name || "—");
				appendCell(row, payload.domain || typeLabel(payload.type), "xss-clip");
				var statusCell = appendCell(row, "");
				putBadge(statusCell, statusText(payload), statusKind(payload));
				appendCell(row, formatTime(payload.created_at));
				var actions = appendCell(row, "");
				actions.className = "xss-row-actions";

				var view = document.createElement("button");
				view.type = "button";
				view.className = "btn-secondary btn-sm";
				view.textContent = payload.type === "probe" ? t("xss.viewUrl", "查看 URL") : t("xss.viewScript", "查看脚本");
				view.addEventListener("click", function () {
					document.getElementById("xss-script-text").value = payload.payload || "";
					document.getElementById("xss-script-modal").style.display = "flex";
				});
				actions.appendChild(view);

				var remove = document.createElement("button");
				remove.type = "button";
				remove.className = "btn-danger btn-sm";
				remove.textContent = t("common.delete", "刪除");
				remove.addEventListener("click", function () { apiObject.deletePayload(payload.id); });
				actions.appendChild(remove);
				body.appendChild(row);
			});
		} catch (error) {
			showError(t("xss.errLoadCallbacks", "加载接管载荷失败"), error);
		}
	};

	apiObject.deletePayload = async function (id) {
		if (!window.confirm(t("xss.confirmDelete", "确定删除此载荷与回显记录？"))) return;
		try {
			await request("/xss/payloads/" + encodeURIComponent(String(id)), { method: "DELETE" });
			await Promise.all([apiObject.loadPayloads(), apiObject.loadCaptures()]);
		} catch (error) {
			showError(t("xss.errDelete", "删除失败"), error);
		}
	};

	apiObject.loadCaptures = async function () {
		try {
			var data = await request("/xss/captures");
			currentCaptures = Array.isArray(data.captures) ? data.captures : [];
			var filterEl = document.getElementById("xss-capture-status");
			var filter = filterEl ? filterEl.value : "";
			var visible = currentCaptures.filter(function (capture) {
				var isProbe = capture.extra === "interaction-probe";
				if (filter === "probe") return isProbe;
				if (filter === "canary") return !isProbe;
				return true;
			});
			var body = document.getElementById("xss-capture-list");
			var empty = document.getElementById("xss-capture-empty");
			clear(body);
			document.getElementById("xss-capture-count").textContent = String(visible.length);
			if (empty) {
				if (!empty.dataset.emptyDefault) empty.dataset.emptyDefault = empty.textContent;
				empty.textContent = currentCaptures.length === 0
					? empty.dataset.emptyDefault
					: t("xss.filterEmpty", "No matches");
			}
			setEmpty("xss-capture-wrap", empty, visible.length === 0);
			visible.forEach(function (capture) {
				var isProbe = capture.extra === "interaction-probe";
				var row = document.createElement("tr");
				appendCell(row, formatTime(capture.created_at));
				appendCell(row, capture.url || capture.domain || "—", "xss-clip");
				appendCell(row, capture.domain || "—", "xss-clip");
				appendCell(row, capture.cookie || "—", "cookie-cell");
				var kindCell = appendCell(row, "");
				var kindLabel = t("xss.labelCanary", "XSS Canary");
				var kindStyle = "ok";
				if (isProbe) {
					kindLabel = t("xss.labelProbe", "SSRF/XXE probe");
					kindStyle = "probe";
				} else if (capture.extra === "metadata" || capture.extra === "keepsession") {
					kindLabel = capture.extra;
				}
				putBadge(kindCell, kindLabel, kindStyle);
				var actions = appendCell(row, "");
				actions.className = "xss-row-actions";
				var detail = document.createElement("button");
				detail.type = "button";
				detail.className = "btn-secondary btn-sm";
				detail.textContent = t("xss.detail", "详情");
				detail.addEventListener("click", function () { apiObject.showCapture(capture); });
				actions.appendChild(detail);
				body.appendChild(row);
			});
		} catch (error) {
			showError(t("xss.errLoadRecords", "加载回显记录失败"), error);
		}
	};

	apiObject.showCapture = function (capture) {
		var body = document.getElementById("xss-detail-body");
		clear(body);
		var list = document.createElement("dl");
		list.className = "xss-detail-list";
		[
			[t("xss.labelTime", "时间"), formatTime(capture.created_at)],
			[t("xss.labelType", "类型"), capture.extra || "xss-canary"],
			["Canary", capture.cookie || "—"],
			[t("xss.labelSource", "来源"), capture.url || capture.domain || "—"],
			[t("xss.colPage", "页面"), capture.domain || "—"],
			[t("xss.labelSourceIp", "来源 IP"), capture.ip || "—"],
			["User-Agent", capture.user_agent || "—"],
		].forEach(function (entry) {
			var label = document.createElement("dt");
			label.textContent = entry[0];
			var value = document.createElement("dd");
			value.appendChild(document.createTextNode(toDisplayText(entry[1])));
			list.appendChild(label);
			list.appendChild(value);
		});
		body.appendChild(list);
		document.getElementById("xss-detail-modal").style.display = "flex";
	};

	apiObject.showConfig = async function () {
		try {
			var data = await request("/xss/config");
			document.getElementById("xss-config-enabled").checked = Boolean(data.enabled);
			document.getElementById("xss-config-bind").value = data.bind_host + ":" + data.bind_port;
			document.getElementById("xss-config-url").value = data.public_url || "";
			document.getElementById("xss-config-cooldown").value = data.cooldown_seconds || 60;
			document.getElementById("xss-config-canary").value = data.canary_cookie_name || "jysec_xss_canary";
			document.getElementById("xss-config-ttl").value = data.probe_ttl_seconds || 3600;
			document.getElementById("xss-config-rate").value = data.rate_limit_per_minute || 30;
			document.getElementById("xss-config-modal").style.display = "flex";
		} catch (error) {
			showError(t("xss.errLoadConfig", "获取配置失败"), error);
		}
	};

	apiObject.copyScript = async function () {
		var textarea = document.getElementById("xss-script-text");
		var button = document.getElementById("xss-copy-script");
		try {
			await navigator.clipboard.writeText(textarea.value);
		} catch (_) {
			textarea.focus();
			textarea.select();
			document.execCommand("copy");
		}
		if (!button) return;
		var previous = button.textContent;
		button.textContent = t("xss.copied", "Copied");
		window.setTimeout(function () {
			button.textContent = previous;
		}, 1600);
	};

	apiObject.saveConfig = function () {
		window.alert(t("xss.readonlyNotice", "此页仅显示安全设置；请在服务器 config.yaml 修改后重启服务。"));
	};

	apiObject.init = async function () {
		var status = document.getElementById("xss-status-text");
		apiObject.applyStaticTranslations();
		try {
			await Promise.all([apiObject.loadPayloads(), apiObject.loadCaptures()]);
			if (status) {
				status.textContent = t(
					"xss.safeModeStatus",
					"安全模式：仅收集 jysec_* canary；SSRF/XXE 探针不保存请求内容"
				);
			}
		} catch (_) {
			if (status) {
				status.textContent = t("xss.unavailableStatus", "安全回连服务暂时无法使用");
			}
		}
		if (!refreshTimer) {
			refreshTimer = window.setInterval(function () {
				if (document.getElementById("page-xss") && document.getElementById("page-xss").classList.contains("active")) {
					Promise.all([apiObject.loadPayloads(), apiObject.loadCaptures()]);
				}
			}, 10000);
		}
	};

	apiObject._toDisplayText = toDisplayText;

	// 語言切換時重繪兩段含 <code> 的提示句（全站慣例：監聽 languagechange，
	// 由 i18n.js 在 changeLanguage 後派發）。其餘文案由 applyTranslations 處理。
	// Node 測試環境無 DOM：包在存在性檢查裡，xss-safety.test.cjs 才能 require 本檔。
	if (typeof document !== "undefined" && typeof document.addEventListener === "function") {
		document.addEventListener("languagechange", function () {
			try {
				apiObject.applyStaticTranslations();
				apiObject.loadPayloads();
				apiObject.loadCaptures();
			} catch (_) {
				/* 語言切換失敗不得中斷頁面 */
			}
		});
	}

	return apiObject;
})();

if (typeof module !== "undefined" && module.exports) {
	module.exports = { toDisplayText: XSS._toDisplayText };
}
