// Package vulnoutbound 負責把平台資料轉成對外（外部 MySQL 接收端）成果。
//
// 這一層存在的理由是「遮蔽必須只有一個地方」：平台即時送出與回填既有資料
// 必須走同一條轉換路徑，否則會出現「即時的資料有遮蔽、���填的沒有」的落差，
// 而那種落差正是資料外洩最常發生的地方。
package vulnoutbound

import (
	"encoding/json"

	"jysecai/internal/database"
	"jysecai/internal/receiver"
	"jysecai/internal/vulnmask"
)

// VulnerabilityPayload 把漏洞記錄映射成接收端成果，並套用去識別化遮蔽。
//
// 遮蔽對象：target、title、evidence、body 與 meta 內的描述類文字，
// 以及 conversation_tag / task_tag 等自由文字欄位。
// 保留對象：識別碼（source_id / conversation_id）、分類、嚴重度、狀態、信心值 ——
// 這些是分析維度，遮掉就沒有倉儲的意義。
//
// 注意 title 也要遮：實務上標題常夾帶真實位址
// （例：「三主機對本源 IP 52.128.238.210 返回一致的 403」），
// 只遮 target/evidence 會讓標題把位址直接帶出去。
//
// 遮蔽分成兩輪：同一組預設帳密會以不同欄位、不同語境出現在同一筆資料裡
// （<input type="password" name="_txtPassword" value="RS106"> 與
// <input type="text" name="_txtUsername" value="RS106"> 是同一個值），
// 只遮 password 欄位會讓 username 欄位把同一個密碼值帶出去。
// 第一輪各欄位獨立遮蔽並收集憑證值，第二輪把收集到的值在所有欄位裡一併抹掉。
func VulnerabilityPayload(v *database.Vulnerability, policy vulnmask.Policy) receiver.Payload {
	if v == nil {
		return receiver.Payload{}
	}
	session := policy.NewSession()

	// 第一輪：各欄位獨立遮蔽。
	title := session.Mask(v.Title)
	target := session.Mask(v.Target)
	evidence := session.Mask(v.Evidence)
	body := session.Mask(v.Description)
	preconditions := session.Mask(v.Preconditions)
	reproductionSteps := session.Mask(v.ReproSteps)
	impact := session.Mask(v.Impact)
	recommendation := session.Mask(v.Recommendation)
	retestNotes := session.Mask(v.RetestNotes)
	typeRaw := session.Mask(v.TypeRaw)
	conversationTag := session.Mask(v.ConversationTag)
	taskTag := session.Mask(v.TaskTag)
	taskID := session.Mask(v.TaskID)
	taskQueueID := session.Mask(v.TaskQueueID)

	// 第二輪：把第一輪辨識出的憑證值在其他欄位裡一併抹掉。
	title = session.Scrub(title)
	target = session.Scrub(target)
	evidence = session.Scrub(evidence)
	body = session.Scrub(body)
	preconditions = session.Scrub(preconditions)
	reproductionSteps = session.Scrub(reproductionSteps)
	impact = session.Scrub(impact)
	recommendation = session.Scrub(recommendation)
	retestNotes = session.Scrub(retestNotes)
	typeRaw = session.Scrub(typeRaw)
	conversationTag = session.Scrub(conversationTag)
	taskTag = session.Scrub(taskTag)
	taskID = session.Scrub(taskID)
	taskQueueID = session.Scrub(taskQueueID)

	return receiver.Payload{
		SourceKind:      receiver.SourceKindVulnerability,
		SourceID:        v.ID,
		ProjectID:       v.ProjectID,
		ConversationID:  v.ConversationID,
		VulnerabilityID: v.ID,
		Category:        v.Type,
		TypeCode:        v.TypeCode,
		Title:           title,
		Target:          target,
		Severity:        v.Severity,
		Status:          v.Status,
		Confidence:      v.Confidence,
		Evidence:        evidence,
		Body:            body,
		Meta: marshalMeta(map[string]any{
			"description":            body,
			"preconditions":          preconditions,
			"reproduction_steps":     reproductionSteps,
			"impact":                 impact,
			"recommendation":         recommendation,
			"retest_notes":           retestNotes,
			"vulnerability_type_raw": typeRaw,
			"conversation_tag":       conversationTag,
			"task_tag":               taskTag,
			"task_id":                taskID,
			"task_queue_id":          taskQueueID,
			"deduplicated":           v.Deduplicated,
			"evidence_merge":         v.Merged,
			"confidence_promoted":    v.Promoted,
		}),
		OccurredAt: v.CreatedAt,
	}
}

// marshalMeta 把多型欄位序列化；失敗時回傳空 JSON 物件而不是壞掉的字串。
func marshalMeta(meta map[string]any) string {
	if len(meta) == 0 {
		return "{}"
	}
	data, err := json.Marshal(meta)
	if err != nil {
		return "{}"
	}
	return string(data)
}
