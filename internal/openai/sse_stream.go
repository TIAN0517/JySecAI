package openai

// SSEAccumulatedKey 为 SSE progress 事件 data 中的服务端权威流式全文快照字段。
// 前端应优先用该字段更新 buffer，避免对 delta 二次 normalize 导致叠字。
const SSEAccumulatedKey = "accumulated"

// WithSSEAccumulated 在 progress data 中附带当前流式累计全文（权威快照）。
func WithSSEAccumulated(data map[string]interface{}, accumulated string) map[string]interface{} {
	if data == nil {
		data = make(map[string]interface{}, 1)
	}
	data[SSEAccumulatedKey] = accumulated
	return data
}
