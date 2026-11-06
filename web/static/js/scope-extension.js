/**
 * 授權範圍擴充（scope_extension）審批卡。
 *
 * 為什麼獨立成一個檔案
 * ------------------
 * scope_extension 是 HITL 的第三種中斷模式：它不是「這次工具呼叫要不要批」，
 * 而是「這些目標不在任何授權範圍內，要不要把它納進授權」。兩種語意差很多：
 * 前者是一次性放行，後者會寫進平台資料庫的授權狀態機（常駐集／授權券／拒絕記憶）。
 *
 * 把卡片渲染與互動獨立出來有兩個好處：
 *   1. 不動到既有 approval / review_edit 的審批流程（那條路徑線上正在用）。
 *   2. 決策詞彙與條件欄位集中在一處，後端契約要改時只改這裡。
 *
 * 決策詞彙（與後端 internal/handler/scope_gate*.go 一致）：
 *   approve_permanent   — 寫入 scope_targets（常駐授權）
 *   approve_once        — 寫入 scope_grants（max_uses = 1）
 *   approve_conditional — 寫入 scope_grants（帶次數／時段條件）
 *   reject              — 寫入 scope_denials（記住拒絕，之後不再打擾）
 *
 * 任意執行類工具（arbitrary = true）必須由操作者宣告「本次將接觸的目標清單」，
 * 沒宣告就不准批准——這是設計 §3.1 的要求：目標藏在指令裡時，用制度關盲區。
 */
(function () {
    'use strict';

    var SCOPE_MODE = 'scope_extension';

    var APPROVE_DECISIONS = {
        approve_permanent: true,
        approve_once: true,
        approve_conditional: true
    };

    function scopeExtT(key, fallback, vars) {
        var fullKey = 'hitl.scope.' + key;
        try {
            if (typeof window.t === 'function') {
                var translated = window.t(fullKey, vars || {});
                if (typeof translated === 'string' && translated && translated !== fullKey) {
                    return translated;
                }
            }
        } catch (e) { /* ignore */ }
        return fallback;
    }

    function scopeExtEscape(value) {
        if (typeof escapeHtml === 'function') return escapeHtml(value);
        return String(value === null || value === undefined ? '' : value);
    }

    /** 是不是 scope_extension 模式。 */
    function scopeExtIsMode(mode) {
        return String(mode || '').trim().toLowerCase() === SCOPE_MODE;
    }

    /** 是不是 scope_extension 的決策詞彙（用來判斷「卡片已解決」）。 */
    function scopeExtIsDecision(decision) {
        var value = String(decision || '').trim().toLowerCase();
        return value === 'reject' || Object.prototype.hasOwnProperty.call(APPROVE_DECISIONS, value);
    }

    /** 是不是「批准」類決策（用來決定卡片要顯示成功還是拒絕）。 */
    function scopeExtIsApproval(decision) {
        var value = String(decision || '').trim().toLowerCase();
        return value === 'approve' || Object.prototype.hasOwnProperty.call(APPROVE_DECISIONS, value);
    }

    /** 取出 payload.scopeExtension。 */
    function scopeExtPayload(data) {
        var payload = (data && data.payload && typeof data.payload === 'object') ? data.payload : {};
        var ext = (payload.scopeExtension && typeof payload.scopeExtension === 'object') ? payload.scopeExtension : {};
        return ext;
    }

    /** 目標清單（未覆蓋目標）。 */
    function scopeExtTargets(ext) {
        return Array.isArray(ext && ext.uncovered) ? ext.uncovered : [];
    }

    /** 相鄰已授權目標。 */
    function scopeExtAdjacent(ext) {
        return Array.isArray(ext && ext.adjacent) ? ext.adjacent : [];
    }

    function scopeExtTargetHost(item) {
        if (!item) return '';
        if (typeof item === 'string') return item;
        var host = String(item.host || item.raw || item.key || '');
        var port = String(item.port || '').trim();
        if (port && host.indexOf(':') < 0) host = host + ':' + port;
        return host;
    }

    function scopeExtRenderTargets(list) {
        var arr = Array.isArray(list) ? list : [];
        if (!arr.length) {
            return '<div class="hitl-scope-empty">' + scopeExtEscape(scopeExtT('scopeEmptyTargets', '(none provided)')) + '</div>';
        }
        return '<ul class="hitl-scope-list">' + arr.map(function (item) {
            return '<li><code>' + scopeExtEscape(scopeExtTargetHost(item)) + '</code></li>';
        }).join('') + '</ul>';
    }

    function scopeExtRenderAdjacent(list) {
        var arr = Array.isArray(list) ? list : [];
        if (!arr.length) {
            return '<div class="hitl-scope-empty">' + scopeExtEscape(scopeExtT('scopeAdjacentNone', '(no adjacent authorized target)')) + '</div>';
        }
        return '<ul class="hitl-scope-list">' + arr.map(function (item) {
            var host = scopeExtEscape((item && item.host) || '');
            var owner = String((item && item.owner) || '').trim();
            var until = String((item && item.validUntil) || '').trim();
            var parts = ['<code>' + host + '</code>'];
            if (owner) {
                parts.push(scopeExtEscape(scopeExtT('scopeAdjacentOwner', 'Owner') + ': ' + owner));
            }
            if (until) {
                parts.push(scopeExtEscape(scopeExtT('scopeAdjacentValidUntil', 'Valid until') + ': ' + until));
            }
            return '<li>' + parts.join(' · ') + '</li>';
        }).join('') + '</ul>';
    }

    function scopeExtResolvedText(decision, timedOut, cancelled) {
        var value = String(decision || '').trim().toLowerCase();
        if (cancelled) return scopeExtT('scopeCancelled', 'Task cancelled; scope decision cancelled');
        if (timedOut) return scopeExtT('scopeTimedOut', 'Scope decision timed out; auto-rejected and remembered');
        if (value === 'approve_permanent') return scopeExtT('scopePermanentApproved', 'Added to the permanent scope');
        if (value === 'approve_once') return scopeExtT('scopeOnceApproved', 'Allowed for this call');
        if (value === 'approve_conditional') return scopeExtT('scopeConditionalApproved', 'Allowed with conditions');
        if (value === 'reject') return scopeExtT('scopeRejected', 'Rejected and remembered');
        return scopeExtT('scopeHumanApproved', 'Allowed once');
    }

    /**
     * 渲染 scope_extension 卡片。
     *
     * data 是 HITL 中斷事件資料（對應既有 hitl_interrupt 事件的 payload）。
     */
    function buildScopeExtensionApprovalHtml(data, opts) {
        var options = opts || {};
        var payload = (data && data.payload && typeof data.payload === 'object') ? data.payload : {};
        var ext = scopeExtPayload(data);
        var toolName = Object.prototype.hasOwnProperty.call(options, 'toolName')
            ? String(options.toolName || '')
            : String((data && data.toolName) || payload.toolName || '-');

        var status = String((data && data.status) || '').trim().toLowerCase();
        var decision = String((data && data.decision) || '').trim().toLowerCase();
        var comment = String((data && data.comment) || data.decisionMessage || '');
        var timedOut = status === 'timeout' ||
            (String((data && data.decidedBy) || '').trim().toLowerCase() === 'system' && /timeout|超时/i.test(comment));
        var cancelled = status === 'cancelled';
        var resolved = !!(data && data.resolved) || status === 'decided' || status === 'timeout' ||
            cancelled || scopeExtIsDecision(decision);

        var actionClass = String(ext.actionClass || '').trim();
        var reason = String(ext.reason || '').trim();
        var arbitrary = ext.arbitrary === true;

        var shield = '<svg class="hitl-codex-shield" viewBox="0 0 20 20" fill="none" aria-hidden="true"><path d="M10 2.2l6 2.5v4.5c0 3.8-2.35 6.55-6 8.6-3.65-2.05-6-4.8-6-8.6V4.7l6-2.5z" stroke="currentColor" stroke-width="1.45" stroke-linejoin="round"/><path d="M7.5 10l1.55 1.55L12.8 7.8" stroke="currentColor" stroke-width="1.45" stroke-linecap="round" stroke-linejoin="round"/></svg>';
        var toolHeading = toolName
            ? '<div class="hitl-codex-tool-row">' + shield + '<span>' + scopeExtEscape(toolName) + '</span></div>'
            : '';

        if (resolved) {
            var ok = scopeExtIsApproval(decision) && !timedOut;
            var stateText = scopeExtResolvedText(decision, timedOut, cancelled);
            var commentHtml = comment && comment !== 'process restarted' && comment !== 'task cancelled'
                ? '<p class="hitl-codex-explainer">' + scopeExtEscape(comment) + '</p>'
                : '';
            return toolHeading +
                '<div class="hitl-codex-state hitl-codex-state--' + (ok ? 'approved' : 'rejected') + '">' +
                '<span class="hitl-codex-state-icon" aria-hidden="true">' + (ok ? '✓' : '×') + '</span>' +
                '<strong>' + scopeExtEscape(stateText) + '</strong>' +
                '</div>' + commentHtml;
        }

        var metaBits = [];
        if (actionClass) {
            metaBits.push(scopeExtEscape(scopeExtT('scopeActionClassLabel', 'Action class') + ': ' + actionClass));
        }
        metaBits.push(scopeExtEscape(scopeExtT('scopeReasonLabel', 'Reason') + ': ' +
            (reason ? reason : scopeExtT('scopeReasonNotCovered', 'Not covered by any scope allow-list'))));

        var declareHtml = arbitrary
            ? '<div class="hitl-scope-declare">' +
              '<div class="hitl-scope-label">' + scopeExtEscape(scopeExtT('scopeDeclareTitle', 'Targets this call will touch (required, one per line)')) + '</div>' +
              '<div class="hitl-input-help">' + scopeExtEscape(scopeExtT('scopeArbitraryNotice', 'Arbitrary-execution tool: declare the targets it will touch, otherwise approval is refused.')) + '</div>' +
              '<textarea class="hitl-scope-input hitl-scope-targets-input" spellcheck="false" placeholder="' +
              scopeExtEscape(scopeExtT('scopeDeclarePlaceholder', 'e.g. api.example.com')) + '"></textarea>' +
              '</div>'
            : '';

        var conditionsHtml =
            '<details class="hitl-approval-details hitl-scope-conditions-details">' +
            '<summary>' + scopeExtEscape(scopeExtT('scopeConditionsTitle', 'Conditional approval (uses / window / classes)')) + '</summary>' +
            '<div class="hitl-scope-conditions">' +
            '<label class="hitl-scope-field">' +
            '<span>' + scopeExtEscape(scopeExtT('scopeOwnerLabel', 'Owner')) + '</span>' +
            '<input class="hitl-config-input hitl-scope-input hitl-scope-owner" type="text" placeholder="' +
            scopeExtEscape(scopeExtT('scopeOwnerPlaceholder', 'e.g. example-client')) + '">' +
            '</label>' +
            '<label class="hitl-scope-field">' +
            '<span>' + scopeExtEscape(scopeExtT('scopeMaxUsesLabel', 'Max uses')) + '</span>' +
            '<input class="hitl-config-input hitl-scope-input hitl-scope-maxuses" type="number" min="1" placeholder="1">' +
            '</label>' +
            '<label class="hitl-scope-field">' +
            '<span>' + scopeExtEscape(scopeExtT('scopeValidUntilLabel', 'Valid until')) + '</span>' +
            '<input class="hitl-config-input hitl-scope-input hitl-scope-validuntil" type="text" placeholder="' +
            scopeExtEscape(scopeExtT('scopeValidUntilPlaceholder', '2026-12-01T00:00:00Z (empty = unlimited)')) + '">' +
            '</label>' +
            '<label class="hitl-scope-field hitl-scope-field--wide">' +
            '<span>' + scopeExtEscape(scopeExtT('scopeActionClassesLabel', 'Action classes (comma separated, empty = this call\'s class)')) + '</span>' +
            '<input class="hitl-config-input hitl-scope-input hitl-scope-classes" type="text" placeholder="harmless_request">' +
            '</label>' +
            '</div>' +
            '</details>';

        return toolHeading +
            '<div class="hitl-approval-heading">' +
            '<span class="hitl-approval-eyebrow">' + scopeExtEscape(scopeExtT('scopePendingStatus', 'Waiting for scope decision')) + '</span>' +
            '<h3>' + scopeExtEscape(scopeExtT('scopeQuestion', 'These targets are not in any scope. How do you want to handle them?')) + '</h3>' +
            '</div>' +
            '<div class="hitl-scope-card">' +
            '<div class="hitl-scope-section">' +
            '<div class="hitl-scope-label">' + scopeExtEscape(scopeExtT('scopeUncoveredTitle', 'Uncovered targets')) + '</div>' +
            scopeExtRenderTargets(scopeExtTargets(ext)) +
            '</div>' +
            '<div class="hitl-scope-meta">' + metaBits.join(' · ') + '</div>' +
            '<div class="hitl-scope-section">' +
            '<div class="hitl-scope-label">' + scopeExtEscape(scopeExtT('scopeAdjacentTitle', 'Adjacent authorized targets')) + '</div>' +
            scopeExtRenderAdjacent(scopeExtAdjacent(ext)) +
            '</div>' +
            declareHtml +
            conditionsHtml +
            '<details class="hitl-approval-details hitl-approval-comment-details">' +
            '<summary>' + scopeExtEscape(scopeExtT('scopeCommentTitle', 'Add a decision note (optional)')) + '</summary>' +
            '<input class="hitl-config-input hitl-inline-comment" type="text" placeholder="' +
            scopeExtEscape(scopeExtT('commentPlaceholder', 'e.g. client confirmed this test in writing')) + '">' +
            '</details>' +
            '</div>' +
            '<div class="hitl-pending-actions hitl-inline-actions">' +
            '<div class="hitl-input-help hitl-scope-status" aria-live="polite"></div>' +
            '<button type="button" class="btn-secondary hitl-scope-reject">' +
            scopeExtEscape(scopeExtT('scopeReject', 'Reject')) + '</button>' +
            '<button type="button" class="btn-secondary hitl-scope-once">' +
            scopeExtEscape(scopeExtT('scopeApproveOnce', 'Allow once')) + '</button>' +
            '<button type="button" class="btn-secondary hitl-scope-conditional">' +
            scopeExtEscape(scopeExtT('scopeApproveConditional', 'Approve with conditions')) + '</button>' +
            '<button type="button" class="btn-primary hitl-scope-permanent">' +
            scopeExtEscape(scopeExtT('scopeApprovePermanent', 'Approve permanently')) + '</button>' +
            '</div>';
    }

    /** 讀取操作者宣告的目標清單（每行一個）。 */
    function scopeExtReadDeclaredTargets(panel) {
        var input = panel.querySelector('.hitl-scope-targets-input');
        if (!input) return [];
        var out = [];
        String(input.value || '').split(/[\r\n,;]+/).forEach(function (line) {
            var value = String(line || '').trim();
            if (value) out.push(value);
        });
        return out;
    }

    /** 讀取附條件授權的欄位。 */
    function scopeExtReadConditions(panel) {
        var ownerEl = panel.querySelector('.hitl-scope-owner');
        var maxUsesEl = panel.querySelector('.hitl-scope-maxuses');
        var validUntilEl = panel.querySelector('.hitl-scope-validuntil');
        var classesEl = panel.querySelector('.hitl-scope-classes');
        var classes = [];
        if (classesEl) {
            String(classesEl.value || '').split(/[,;]+/).forEach(function (item) {
                var value = String(item || '').trim();
                if (value) classes.push(value);
            });
        }
        var maxUses = 0;
        if (maxUsesEl && String(maxUsesEl.value || '').trim()) {
            maxUses = parseInt(String(maxUsesEl.value).trim(), 10);
            if (!isFinite(maxUses) || maxUses <= 0) maxUses = 0;
        }
        return {
            owner: ownerEl ? String(ownerEl.value || '').trim() : '',
            actionClasses: classes,
            maxUses: maxUses,
            validUntil: validUntilEl ? String(validUntilEl.value || '').trim() : ''
        };
    }

    /** 送出 scope_extension 決策。 */
    function scopeExtSubmit(panel, data, decision) {
        var statusEl = panel.querySelector('.hitl-scope-status');
        var ext = scopeExtPayload(data);
        var buttons = panel.querySelectorAll('.hitl-scope-reject, .hitl-scope-once, .hitl-scope-conditional, .hitl-scope-permanent');
        var setBusy = function (busy) {
            for (var i = 0; i < buttons.length; i++) buttons[i].disabled = busy;
        };
        var fail = function (message) {
            if (statusEl) statusEl.textContent = message;
            setBusy(false);
        };

        var isReject = decision === 'reject';
        var declared = scopeExtReadDeclaredTargets(panel);
        if (ext.arbitrary === true && !isReject && declared.length === 0) {
            fail(scopeExtT('scopeMissingTargets', 'Declare the targets this call will touch first'));
            return;
        }

        var scopeConditions = scopeExtReadConditions(panel);
        if (scopeConditions.validUntil) {
            var parsed = new Date(scopeConditions.validUntil);
            if (isNaN(parsed.getTime())) {
                fail(scopeExtT('scopeInvalidDate', 'Invalid valid-until (RFC3339, e.g. 2026-12-01T00:00:00Z)'));
                return;
            }
        }

        var commentEl = panel.querySelector('.hitl-inline-comment');
        var comment = commentEl ? String(commentEl.value || '').trim() : '';
        setBusy(true);

        var submit = (typeof window.submitHitlDecisionWithPayload === 'function')
            ? window.submitHitlDecisionWithPayload
            : null;
        if (!submit) {
            fail(scopeExtT('scopeSubmitFailed', 'Submit failed, please retry'));
            return;
        }
        var conversationId = (data && data.conversationId) ||
            (typeof window.currentConversationId === 'string' ? window.currentConversationId : '');

        Promise.resolve(submit(data.interruptId, decision, comment, null, conversationId, {
            scopeConditions: scopeConditions,
            scopeTargets: declared
        })).then(function (ok) {
            if (ok === false) {
                fail(scopeExtT('scopeSubmitFailed', 'Submit failed, please retry'));
                return;
            }
            panel.classList.add('hitl-inline-done');
            var ok2 = scopeExtIsApproval(decision);
            panel.innerHTML = buildScopeExtensionApprovalHtml(Object.assign({}, data, {
                resolved: true,
                decision: decision,
                comment: comment,
                status: 'decided'
            }), { toolName: (data && data.toolName) || '' });
            if (statusEl) statusEl.textContent = ok2
                ? scopeExtT('scopeResumed', 'Decided; the original tool call continues…')
                : scopeExtT('scopeRejectedNotice', 'This target is remembered as rejected; do not retry');
        }).catch(function (err) {
            fail(scopeExtT('scopeSubmitFailed', 'Submit failed, please retry') + (err && err.message ? ': ' + err.message : ''));
        });
    }

    /** 綁定卡片的按鈕與輸入。 */
    function bindScopeExtensionApproval(panel, data) {
        if (!panel || !data || !data.interruptId) return;
        if (panel.__scopeExtensionBound) return;
        panel.__scopeExtensionBound = true;

        var map = [
            ['.hitl-scope-permanent', 'approve_permanent'],
            ['.hitl-scope-once', 'approve_once'],
            ['.hitl-scope-conditional', 'approve_conditional'],
            ['.hitl-scope-reject', 'reject']
        ];
        map.forEach(function (entry) {
            var button = panel.querySelector(entry[0]);
            if (!button) return;
            button.addEventListener('click', function () {
                scopeExtSubmit(panel, data, entry[1]);
            });
        });
    }

    /**
     * 設定頁「待處理審批」清單裡的 scope_extension 項目。
     *
     * 與聊天內嵌卡片共用同一組欄位，但送出走 submitHitlDecisionWithPayload。
     */
    function renderScopeExtensionPendingItem(item) {
        var payloadObj = (typeof hitlParsePayloadObject === 'function')
            ? hitlParsePayloadObject(item.payload || '')
            : {};
        var ext = (payloadObj && payloadObj.scopeExtension && typeof payloadObj.scopeExtension === 'object')
            ? payloadObj.scopeExtension
            : {};
        var interruptId = String(item.id || '');
        var conversationId = String(item.conversationId || '');
        var qId = JSON.stringify(interruptId).replace(/"/g, '&quot;');
        var qConv = JSON.stringify(conversationId).replace(/"/g, '&quot;');

        var actionClass = String(ext.actionClass || '').trim();
        var reason = String(ext.reason || '').trim();
        var arbitrary = ext.arbitrary === true;

        var declareHtml = arbitrary
            ? '<div class="hitl-scope-declare">' +
              '<div class="hitl-scope-label">' + scopeExtEscape(scopeExtT('scopeDeclareTitle', 'Targets this call will touch (required, one per line)')) + '</div>' +
              '<textarea class="hitl-scope-input hitl-scope-targets-input" id="hitl-scope-targets-' + scopeExtEscape(interruptId) + '" spellcheck="false" placeholder="' +
              scopeExtEscape(scopeExtT('scopeDeclarePlaceholder', 'e.g. api.example.com')) + '"></textarea>' +
              '</div>'
            : '';

        return '<div class="hitl-pending-item hitl-pending-item--scope">' +
            '<div class="hitl-pending-item-header">' +
            '<div class="hitl-pending-item-title">' +
            '<span class="hitl-tool-badge">' + scopeExtEscape(item.toolName || '-') + '</span>' +
            '<span class="hitl-mode-tag hitl-mode-tag--scope_extension">' + scopeExtEscape(scopeExtT('scopeModeLabel', 'Scope extension')) + '</span>' +
            '</div>' +
            '<button class="hitl-dismiss-btn" title="' + scopeExtEscape(scopeExtT('dismiss', 'Dismiss')) + '" onclick="dismissHitlItem(' + qId + ')">&times;</button>' +
            '</div>' +
            '<div class="hitl-pending-meta">' + scopeExtEscape(scopeExtT('conversationLabel', 'Conversation:')) + ' ' + scopeExtEscape(conversationId || '-') + '</div>' +
            '<div class="hitl-scope-card">' +
            '<div class="hitl-scope-section">' +
            '<div class="hitl-scope-label">' + scopeExtEscape(scopeExtT('scopeUncoveredTitle', 'Uncovered targets')) + '</div>' +
            scopeExtRenderTargets(scopeExtTargets(ext)) +
            '</div>' +
            '<div class="hitl-scope-meta">' +
            scopeExtEscape(scopeExtT('scopeActionClassLabel', 'Action class') + ': ' + (actionClass || '-')) + ' · ' +
            scopeExtEscape(scopeExtT('scopeReasonLabel', 'Reason') + ': ' +
                (reason ? reason : scopeExtT('scopeReasonNotCovered', 'Not covered by any scope allow-list'))) +
            '</div>' +
            '<div class="hitl-scope-section">' +
            '<div class="hitl-scope-label">' + scopeExtEscape(scopeExtT('scopeAdjacentTitle', 'Adjacent authorized targets')) + '</div>' +
            scopeExtRenderAdjacent(scopeExtAdjacent(ext)) +
            '</div>' +
            declareHtml +
            '<details class="hitl-approval-details hitl-scope-conditions-details">' +
            '<summary>' + scopeExtEscape(scopeExtT('scopeConditionsTitle', 'Conditional approval (uses / window / classes)')) + '</summary>' +
            '<div class="hitl-scope-conditions">' +
            '<label class="hitl-scope-field"><span>' + scopeExtEscape(scopeExtT('scopeOwnerLabel', 'Owner')) + '</span>' +
            '<input class="hitl-config-input hitl-scope-input hitl-scope-owner" id="hitl-scope-owner-' + scopeExtEscape(interruptId) + '" type="text" placeholder="' +
            scopeExtEscape(scopeExtT('scopeOwnerPlaceholder', 'e.g. example-client')) + '"></label>' +
            '<label class="hitl-scope-field"><span>' + scopeExtEscape(scopeExtT('scopeMaxUsesLabel', 'Max uses')) + '</span>' +
            '<input class="hitl-config-input hitl-scope-input hitl-scope-maxuses" id="hitl-scope-maxuses-' + scopeExtEscape(interruptId) + '" type="number" min="1" placeholder="1"></label>' +
            '<label class="hitl-scope-field"><span>' + scopeExtEscape(scopeExtT('scopeValidUntilLabel', 'Valid until')) + '</span>' +
            '<input class="hitl-config-input hitl-scope-input hitl-scope-validuntil" id="hitl-scope-validuntil-' + scopeExtEscape(interruptId) + '" type="text" placeholder="' +
            scopeExtEscape(scopeExtT('scopeValidUntilPlaceholder', '2026-12-01T00:00:00Z (empty = unlimited)')) + '"></label>' +
            '<label class="hitl-scope-field hitl-scope-field--wide"><span>' + scopeExtEscape(scopeExtT('scopeActionClassesLabel', 'Action classes (comma separated, empty = this call\'s class)')) + '</span>' +
            '<input class="hitl-config-input hitl-scope-input hitl-scope-classes" id="hitl-scope-classes-' + scopeExtEscape(interruptId) + '" type="text" placeholder="harmless_request"></label>' +
            '</div>' +
            '</details>' +
            '<div class="hitl-input-help">' + scopeExtEscape(scopeExtT('commentHelp', 'Note (optional): briefly record why you decided.')) + '</div>' +
            '<input id="hitl-comment-' + scopeExtEscape(interruptId) + '" class="hitl-config-input hitl-inline-comment" type="text" placeholder="' +
            scopeExtEscape(scopeExtT('commentPlaceholder', 'e.g. client confirmed this test in writing')) + '">' +
            '</div>' +
            '<div class="hitl-pending-actions">' +
            '<div class="hitl-input-help hitl-scope-status" id="hitl-scope-status-' + scopeExtEscape(interruptId) + '" aria-live="polite"></div>' +
            '<button class="btn-secondary" onclick="submitScopeExtensionDecision(' + qId + ',&quot;reject&quot;,' + qConv + ')">' +
            scopeExtEscape(scopeExtT('scopeReject', 'Reject')) + '</button>' +
            '<button class="btn-secondary" onclick="submitScopeExtensionDecision(' + qId + ',&quot;approve_once&quot;,' + qConv + ')">' +
            scopeExtEscape(scopeExtT('scopeApproveOnce', 'Allow once')) + '</button>' +
            '<button class="btn-secondary" onclick="submitScopeExtensionDecision(' + qId + ',&quot;approve_conditional&quot;,' + qConv + ')">' +
            scopeExtEscape(scopeExtT('scopeApproveConditional', 'Approve with conditions')) + '</button>' +
            '<button class="btn-primary" onclick="submitScopeExtensionDecision(' + qId + ',&quot;approve_permanent&quot;,' + qConv + ')">' +
            scopeExtEscape(scopeExtT('scopeApprovePermanent', 'Approve permanently')) + '</button>' +
            '</div>' +
            '</div>';
    }

    /** 設定頁待審批清單用的決策送出。 */
    function submitScopeExtensionDecision(interruptId, decision, conversationId) {
        var id = String(interruptId || '');
        var ext = { arbitrary: false };
        var statusEl = document.getElementById('hitl-scope-status-' + id);
        var fail = function (message) {
            if (statusEl) statusEl.textContent = message;
        };

        var targetsEl = document.getElementById('hitl-scope-targets-' + id);
        var declared = [];
        if (targetsEl) {
            String(targetsEl.value || '').split(/[\r\n,;]+/).forEach(function (line) {
                var value = String(line || '').trim();
                if (value) declared.push(value);
            });
        }
        var commentEl = document.getElementById('hitl-comment-' + id);
        var comment = commentEl ? String(commentEl.value || '').trim() : '';

        var ownerEl = document.getElementById('hitl-scope-owner-' + id);
        var maxUsesEl = document.getElementById('hitl-scope-maxuses-' + id);
        var validUntilEl = document.getElementById('hitl-scope-validuntil-' + id);
        var classesEl = document.getElementById('hitl-scope-classes-' + id);
        var classes = [];
        if (classesEl) {
            String(classesEl.value || '').split(/[,;]+/).forEach(function (item) {
                var value = String(item || '').trim();
                if (value) classes.push(value);
            });
        }
        var maxUses = 0;
        if (maxUsesEl && String(maxUsesEl.value || '').trim()) {
            maxUses = parseInt(String(maxUsesEl.value).trim(), 10);
            if (!isFinite(maxUses) || maxUses <= 0) maxUses = 0;
        }
        var validUntil = validUntilEl ? String(validUntilEl.value || '').trim() : '';
        if (validUntil) {
            var parsed = new Date(validUntil);
            if (isNaN(parsed.getTime())) {
                fail(scopeExtT('scopeInvalidDate', 'Invalid valid-until (RFC3339, e.g. 2026-12-01T00:00:00Z)'));
                return;
            }
        }

        var scopeConditions = {
            owner: ownerEl ? String(ownerEl.value || '').trim() : '',
            actionClasses: classes,
            maxUses: maxUses,
            validUntil: validUntil
        };

        var submit = (typeof window.submitHitlDecisionWithPayload === 'function')
            ? window.submitHitlDecisionWithPayload
            : null;
        if (!submit) {
            fail(scopeExtT('scopeSubmitFailed', 'Submit failed, please retry'));
            return;
        }
        Promise.resolve(submit(id, decision, comment, null, conversationId, {
            scopeConditions: scopeConditions,
            scopeTargets: declared
        })).then(function (ok) {
            if (ok === false) {
                fail(scopeExtT('scopeSubmitFailed', 'Submit failed, please retry'));
                return;
            }
            if (typeof window.refreshHitlPending === 'function') {
                window.refreshHitlPending();
            }
        }).catch(function (err) {
            fail(scopeExtT('scopeSubmitFailed', 'Submit failed, please retry') + (err && err.message ? ': ' + err.message : ''));
        });
    }

    window.scopeExtIsMode = scopeExtIsMode;
    window.scopeExtIsDecision = scopeExtIsDecision;
    window.scopeExtIsApproval = scopeExtIsApproval;
    window.scopeExtPayload = scopeExtPayload;
    window.buildScopeExtensionApprovalHtml = buildScopeExtensionApprovalHtml;
    window.bindScopeExtensionApproval = bindScopeExtensionApproval;
    window.renderScopeExtensionPendingItem = renderScopeExtensionPendingItem;
    window.submitScopeExtensionDecision = submitScopeExtensionDecision;
})();
