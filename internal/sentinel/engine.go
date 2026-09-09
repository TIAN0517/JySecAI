package sentinel

import (
	"context"
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"
)

// RunScan 執行暴露面全流程探測任務
func RunScan(ctx context.Context, targetInput string) (*ScanSnapshot, error) {
	val := ValidateTarget(targetInput)
	if !val.OK {
		return nil, fmt.Errorf("%s", val.Error)
	}

	startAt := time.Now()
	snapshot := &ScanSnapshot{
		ID:         uuid.New().String(),
		Target:     val.Target,
		TargetKind: val.Kind,
		CreatedAt:  startAt,
		Status:     "running",
	}

	// 1. 發現資產與主機
	assets := DiscoverHosts(ctx, val.Target, val.Kind)

	var allPorts []PortItem
	var allDatabases []DatabaseItem
	var allEndpoints []EndpointItem

	// 2. 針對在線主機進行端口掃描、數據庫探測與 Web 路徑排查
	for i := range assets {
		select {
		case <-ctx.Done():
			snapshot.Status = "failed"
			snapshot.Error = "探測任務超時或已被取消"
			return snapshot, ctx.Err()
		default:
		}

		asset := &assets[i]
		if !asset.Alive && asset.Host != val.Target {
			continue
		}

		// 端口掃描與 TLS 校驗
		ports, tlsValid := ScanPortsAndTLS(ctx, asset.Host, asset.IP)
		asset.TLSValid = tlsValid
		if len(ports) > 0 {
			asset.Alive = true
			allPorts = append(allPorts, ports...)
		}

		// 數據庫探測
		for _, p := range ports {
			if dbItem := ProbeDatabase(ctx, asset.Host, p.Port); dbItem != nil {
				allDatabases = append(allDatabases, *dbItem)
			}
		}

		// Web 路徑探測（若 80 或 443 開放）
		has80 := false
		has443 := false
		for _, p := range ports {
			if p.Port == 80 {
				has80 = true
			}
			if p.Port == 443 {
				has443 = true
			}
		}

		if has443 {
			eps := ProbeEndpoints(ctx, asset.Host, "https", 443)
			allEndpoints = append(allEndpoints, eps...)
			if asset.Title == "" && len(eps) > 0 {
				asset.Title = eps[0].Title
			}
		} else if has80 {
			eps := ProbeEndpoints(ctx, asset.Host, "http", 80)
			allEndpoints = append(allEndpoints, eps...)
			if asset.Title == "" && len(eps) > 0 {
				asset.Title = eps[0].Title
			}
		}
	}

	snapshot.Assets = assets
	snapshot.Ports = allPorts
	snapshot.Databases = allDatabases
	snapshot.Endpoints = allEndpoints

	// 3. 自動聚合生成發現項（Findings）
	snapshot.Findings = generateFindings(snapshot)

	// 4. 計算統計指標
	endAt := time.Now()
	snapshot.FinishedAt = endAt.Format(time.RFC3339)
	snapshot.DurationMs = endAt.Sub(startAt).Milliseconds()
	snapshot.Status = "completed"

	summary := ScanSummary{
		HostCount:     len(snapshot.Assets),
		OpenPortCount: len(snapshot.Ports),
		EndpointCount: len(snapshot.Endpoints),
		DatabaseCount: len(snapshot.Databases),
	}

	for _, a := range snapshot.Assets {
		if a.Alive {
			summary.AliveCount++
		}
	}

	for _, ep := range snapshot.Endpoints {
		for _, t := range ep.Tags {
			if t == "login" || t == "auth" {
				summary.LoginCount++
				break
			}
		}
	}

	for _, f := range snapshot.Findings {
		switch f.Severity {
		case "high":
			summary.HighCount++
		case "medium":
			summary.MediumCount++
		case "low":
			summary.LowCount++
		case "info":
			summary.InfoCount++
		}
	}

	snapshot.Summary = summary
	return snapshot, nil
}

func generateFindings(s *ScanSnapshot) []FindingItem {
	var findings []FindingItem
	idx := 0

	// 1. 數據庫暴露項
	for _, db := range s.Databases {
		idx++
		if db.Risk == "unauth" {
			findings = append(findings, FindingItem{
				ID:       fmt.Sprintf("finding-%d", idx),
				Severity: "high",
				Category: "database",
				Host:     db.Host,
				Title:    fmt.Sprintf("%s 數據庫未授權訪問漏洞", db.EngineName),
				Detail:   fmt.Sprintf("在主機 %s 端口 %d 檢測到未授權訪問：%s。該服務未配置任何身份認證，公網任何人皆可讀取甚至修改敏感數據。", db.Host, db.Port, db.Evidence),
			})
		} else {
			findings = append(findings, FindingItem{
				ID:       fmt.Sprintf("finding-%d", idx),
				Severity: "medium",
				Category: "database",
				Host:     db.Host,
				Title:    fmt.Sprintf("%s 數據庫服務暴露在公網", db.EngineName),
				Detail:   fmt.Sprintf("主機 %s 端口 %d 開放了 %s 服務：%s。強烈建議配置安全組策略，限制僅允許內網訪問。", db.Host, db.Port, db.EngineName, db.Evidence),
			})
		}
	}

	// 2. 端點暴露項（登錄、測試/樣例、API）
	for _, ep := range s.Endpoints {
		idx++
		isLogin := hasTag(ep.Tags, "login") || hasTag(ep.Tags, "auth")
		isTest := hasTag(ep.Tags, "test") || strings.Contains(ep.URL, "/test") || strings.Contains(ep.URL, "/dev") || strings.Contains(ep.URL, "/staging")
		isSample := hasTag(ep.Tags, "sample") || strings.Contains(ep.URL, "/demo") || strings.Contains(ep.URL, "/sample")
		isApi := hasTag(ep.Tags, "api") || hasTag(ep.Tags, "doc") || hasTag(ep.Tags, "actuator")

		// SPA 回退降級為 info
		if ep.SPAFallback {
			findings = append(findings, FindingItem{
				ID:       fmt.Sprintf("finding-%d", idx),
				Severity: "info",
				Category: "other",
				Host:     extractHostFromURL(ep.URL),
				Title:    fmt.Sprintf("單頁應用 404 回退路徑: %s", ep.URL),
				Detail:   fmt.Sprintf("該路徑返回 HTTP 200，但與 404 隨機探測頁面特徵完全一致，已被標記為 SPA 路由回退，非獨立測試/登錄系統。"),
				URL:      ep.URL,
			})
			continue
		}

		if isLogin {
			findings = append(findings, FindingItem{
				ID:       fmt.Sprintf("finding-%d", idx),
				Severity: "medium",
				Category: "login",
				Host:     extractHostFromURL(ep.URL),
				Title:    fmt.Sprintf("對外公開登錄頁/認證接口: %s", ep.URL),
				Detail:   fmt.Sprintf("檢測到對外開放的用戶/管理員認證登錄入口 (HTTP %d)，頁面標題: '%s'。可能面臨撞庫或憑據爆破風險。", ep.Status, ep.Title),
				URL:      ep.URL,
			})
		} else if isTest {
			findings = append(findings, FindingItem{
				ID:       fmt.Sprintf("finding-%d", idx),
				Severity: "medium",
				Category: "test",
				Host:     extractHostFromURL(ep.URL),
				Title:    fmt.Sprintf("對外暴露的測試/開發環境: %s", ep.URL),
				Detail:   fmt.Sprintf("檢測到疑似測試或開發環境入口 (HTTP %d)，通常包含未充分加固的接口或調試代碼。", ep.Status),
				URL:      ep.URL,
			})
		} else if isSample {
			findings = append(findings, FindingItem{
				ID:       fmt.Sprintf("finding-%d", idx),
				Severity: "low",
				Category: "sample",
				Host:     extractHostFromURL(ep.URL),
				Title:    fmt.Sprintf("對外暴露的樣例系統: %s", ep.URL),
				Detail:   fmt.Sprintf("檢測到樣例或演示入口 (HTTP %d)。", ep.Status),
				URL:      ep.URL,
			})
		} else if isApi {
			sev := "medium"
			if strings.Contains(ep.URL, "/actuator/env") {
				sev = "high"
			}
			findings = append(findings, FindingItem{
				ID:       fmt.Sprintf("finding-%d", idx),
				Severity: sev,
				Category: "api",
				Host:     extractHostFromURL(ep.URL),
				Title:    fmt.Sprintf("對外暴露的 API 文檔/監控端點: %s", ep.URL),
				Detail:   fmt.Sprintf("檢測到接口文檔或監控端點開放 (HTTP %d)，可能洩露系統接口結構或環境配置。", ep.Status),
				URL:      ep.URL,
			})
		}
	}

	// 3. 高危/敏感端口開放
	for _, p := range s.Ports {
		// 跳過標準 HTTP(80)/HTTPS(443)
		if p.Port == 80 || p.Port == 443 {
			continue
		}
		// 數據庫端口已有單獨條目，不再重複生成高危 port 項
		if isDatabasePort(p.Port) {
			continue
		}

		idx++
		sev := "medium"
		switch p.Port {
		case 2375, 6443, 873:
			sev = "high"
		case 21, 23, 3389, 5900:
			sev = "medium"
		default:
			sev = "low"
		}

		findings = append(findings, FindingItem{
			ID:       fmt.Sprintf("finding-%d", idx),
			Severity: sev,
			Category: "port",
			Host:     p.Host,
			Title:    fmt.Sprintf("非標準/敏感端口開放: %s:%d (%s)", p.Host, p.Port, p.Service),
			Detail:   fmt.Sprintf("主機 %s 檢測到開放的非標準服務端口 %d (%s)。若非業務必要，建議在防火牆或安全組中關閉。", p.Host, p.Port, p.Service),
		})
	}

	return findings
}

func hasTag(tags []string, tag string) bool {
	for _, t := range tags {
		if t == tag {
			return true
		}
	}
	return false
}

func extractHostFromURL(rawURL string) string {
	parts := strings.Split(rawURL, "://")
	if len(parts) > 1 {
		hostPart := strings.Split(parts[1], "/")[0]
		return strings.Split(hostPart, ":")[0]
	}
	return ""
}

func isDatabasePort(port int) bool {
	for _, def := range AllDatabaseEngines {
		for _, p := range def.Ports {
			if p == port {
				return true
			}
		}
	}
	return false
}
