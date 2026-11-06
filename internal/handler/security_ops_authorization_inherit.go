package handler

import (
	"encoding/json"
	"strings"
	"time"

	"jysecai/internal/database"
)

// 授權繼承（authorization inheritance）
//
// 問題
// ----
// 一份案件只有一份書面授權，但平台上每開一個掃描任務就要重打一次授權編號、
// 授權人、授權期間、授權範圍，還要再勾一次「我確認擁有書面測試授權」。
// 同一份授權書被抄寫十次，除了抄錯的機率之外沒有任何好處。
//
// 做法
// ----
// 新任務沒有帶完整授權事實時，從**同一專案**既有的授權記錄裡挑一笔符合下列全部
// 條件的，沿用過來：
//
//  1. 那筆記錄是人工確認過的（attested=true）且有授權編號。
//  2. 它現在仍然有效（未過期、未超過 90 日）。
//  3. 它的授權範圍涵蓋這次要掃的所有目標。
//
// 三條同時成立才繼承。繼承來的記錄會帶著 sourceRunId / inherited / inheritedAt，
// 所以「這筆授權是誰在什麼時候確認的、這次是沿用來的」在稽核時查得到 —— 證據強度
// 不會因為沿用而消失。
//
// 底線
// ----
// 繼承只會沿用**人已經做過的確認**，不會替你產生新的確認：
//   - 沒有任何人工確認過的授權 → 不繼承，維持原本「請提供授權」的錯誤訊息。
//   - 繼承來的授權人姓名、編號永遠是人寫的那份，不是模型產生的。
//   - 已經有明確授權編號但缺授權人這種「半填」的狀態，仍然要求人工補齊 ——
//     只補空白欄位會讓「半填」變成「全填」而來源不明，寧可拒絕。

// inheritAuthorization 找出可以沿用的授權記錄。
//
// 回傳 false 代表沒有可沿用的來源（呼叫端應維持原本的驗證錯誤訊息）。
func (h *SecurityOpsHandler) inheritAuthorization(req securityOpsCreateRequest) (securityOpsAuthorization, bool) {
	projectID := strings.TrimSpace(req.ProjectID)
	if projectID == "" {
		return securityOpsAuthorization{}, false
	}
	targets := trimLines(req.Targets)
	if len(targets) == 0 {
		return securityOpsAuthorization{}, false
	}

	runs, err := h.db.ListSecurityOpsRuns("", projectID, true, 50)
	if err != nil {
		return securityOpsAuthorization{}, false
	}

	now := h.now()
	for _, run := range runs {
		var auth securityOpsAuthorization
		if err := json.Unmarshal([]byte(run.AuthorizationJSON), &auth); err != nil {
			continue
		}
		if !auth.Attested || strings.TrimSpace(auth.ID) == "" {
			continue
		}
		if !authorizationCurrent(auth, now) {
			continue
		}
		patterns := trimLines(auth.TargetPatterns)
		if len(patterns) == 0 {
			continue
		}
		covered := true
		for _, target := range targets {
			if !targetInScope(target, patterns) {
				covered = false
				break
			}
		}
		if !covered {
			continue
		}
		auth.SourceRunID = run.ID
		auth.Inherited = true
		auth.InheritedAt = now
		return auth, true
	}
	return securityOpsAuthorization{}, false
}

// mergeSecurityOpsAuthorization 把繼承來的授權事實補進請求缺的欄位。
//
// 只有「完全沒帶」的欄位才會被補上：請求已經給的值一律保留 —— 呼叫端明確寫出來的
// 授權範圍與操作模式，是這一次任務自己的決定，不該被舊記錄蓋掉。
//
// 半填的授權（有編號但缺授權人之類）不會被補成全填：那種狀態代表「有人填了一半」，
// 補完之後看不出是哪一次確認的，證據鏈會斷掉。
func mergeSecurityOpsAuthorization(requested, inherited securityOpsAuthorization) securityOpsAuthorization {
	if strings.TrimSpace(requested.ID) != "" {
		// 已經帶編號：視為呼叫端指定了這筆授權，不做繼承。
		return requested
	}
	merged := requested
	if strings.TrimSpace(merged.ID) == "" {
		merged.ID = inherited.ID
	}
	if merged.ProjectID == "" {
		merged.ProjectID = inherited.ProjectID
	}
	if len(merged.TargetPatterns) == 0 {
		merged.TargetPatterns = inherited.TargetPatterns
	}
	if len(merged.Operations) == 0 {
		merged.Operations = inherited.Operations
	}
	if merged.ValidFrom.IsZero() {
		merged.ValidFrom = inherited.ValidFrom
	}
	if merged.ValidUntil.IsZero() {
		merged.ValidUntil = inherited.ValidUntil
	}
	if strings.TrimSpace(merged.ApprovedBy) == "" {
		merged.ApprovedBy = inherited.ApprovedBy
	}
	if !merged.Attested {
		merged.Attested = inherited.Attested
	}
	merged.SourceRunID = inherited.SourceRunID
	merged.Inherited = inherited.Inherited
	merged.InheritedAt = inherited.InheritedAt
	return merged
}

// authorizationBasis 是授權書上要寫的「授權依據」說明。
//
// 繼承來的授權要說清楚：這份文件轉錄自哪一筆記錄、誰確認的、何時確認的。
// 沒有這行字，讀文件的人會以為是這一次才簽的。
func authorizationBasis(auth securityOpsAuthorization, now time.Time) string {
	if !auth.Attested || strings.TrimSpace(auth.ApprovedBy) == "" {
		return ""
	}
	basis := "本授權依據甲方授權人 " + strings.TrimSpace(auth.ApprovedBy) + " 確認之書面授權"
	if strings.TrimSpace(auth.ID) != "" {
		basis += "（授權編號 " + strings.TrimSpace(auth.ID) + "）"
	}
	if !auth.InheritedAt.IsZero() {
		basis += "；平台於 " + auth.InheritedAt.UTC().Format("2006-01-02") + " 沿用該授權"
	}
	if strings.TrimSpace(auth.SourceRunID) != "" {
		basis += "（來源記錄 " + strings.TrimSpace(auth.SourceRunID) + "）"
	}
	return basis
}

// securityOpsAuthorizationFromRun 從掃描任務取出授權記錄。
func securityOpsAuthorizationFromRun(run database.SecurityOpsRun) (securityOpsAuthorization, bool) {
	var auth securityOpsAuthorization
	if err := json.Unmarshal([]byte(run.AuthorizationJSON), &auth); err != nil {
		return securityOpsAuthorization{}, false
	}
	return auth, true
}
