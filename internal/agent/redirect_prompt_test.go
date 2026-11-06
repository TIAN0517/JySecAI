package agent

import (
	"strings"
	"testing"
)

func TestDefaultSingleAgentSystemPromptConversationBoundaries(t *testing.T) {
	prompt := DefaultSingleAgentSystemPrompt()
	for _, needle := range []string{
		"不因“红队、漏洞、攻击、渗透”等关键词直接拒绝",
		"不重复询问已提供的信息",
		"不要求每轮必须调用工具",
		"不得通过换入口、换工具或修改参数绕过同一安全限制",
		"不自动扩大目标范围",
		"修改工作副本不代表已经部署上线",
	} {
		if !strings.Contains(prompt, needle) {
			t.Errorf("system prompt missing conversation boundary %q", needle)
		}
	}
	for _, needle := range []string{
		"切勿等待批准或授权", "2000+", "必须完全利用",
		"https://97y.me/tjneJ", "必须同时植入", "禁止输出「无法对",
	} {
		if strings.Contains(prompt, needle) {
			t.Errorf("system prompt contains unsafe or coercive instruction %q", needle)
		}
	}
}
