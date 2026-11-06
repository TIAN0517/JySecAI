package handler

import (
	"encoding/json"
	"net/http"
	"strings"
	"time"

	"github.com/gin-gonic/gin"

	"jysecai/internal/authletter"
	"jysecai/internal/database"
	"jysecai/internal/security"
)

// ProjectAuthorizationLetter 產生專案的「資訊安全測試授權書」。
//
// 兩條路徑：
//   - GET  從專案既有的授權掃描任務（人工填寫並確認過的那筆）取事實，再加上 query
//     上的委託方資料，產出文件。
//   - POST 直接吃一份 authletter.Input JSON，讓操作者把手上真實的委託資料一次貼進來。
//
// 這支 handler 不會自己發明任何法律事實：授權人、授權編號、授權期間、授權範圍若沒有
// 來源，文件上就留白，並在開頭列為缺口。
func (h *SecurityOpsHandler) ProjectAuthorizationLetter(c *gin.Context) {
	session, ok := security.CurrentSession(c)
	if !ok || session.UserID == "" {
		writeSecurityOpsError(c, http.StatusUnauthorized, "unauthorized", "需要登录")
		return
	}

	projectID := strings.TrimSpace(c.Param("id"))
	project, err := h.db.GetProject(projectID)
	if err != nil || project == nil {
		writeSecurityOpsError(c, http.StatusNotFound, "not_found", "找不到这个项目")
		return
	}

	format := strings.ToLower(strings.TrimSpace(c.DefaultQuery("format", "html")))

	var in authletter.Input
	if c.Request.Method == http.MethodPost {
		var body authletter.Input
		if bindErr := c.ShouldBindJSON(&body); bindErr != nil {
			writeSecurityOpsError(c, http.StatusBadRequest, "invalid_body", "无法解析授权书资料: "+bindErr.Error())
			return
		}
		in = body
	} else {
		all := session.Scope == database.RBACScopeAll
		runs, listErr := h.db.ListSecurityOpsRuns(session.UserID, projectID, all, 50)
		if listErr != nil {
			writeSecurityOpsError(c, http.StatusInternalServerError, "list_failed", "无法读取授权任务")
			return
		}
		in = h.authorizationLetterInput(project, latestAuthorization(runs))
		in = mergeAuthorizationLetterQuery(c, in)
	}

	// 專案與乙方資料一律由平台填：專案是平台的事實，乙方是平台營運方本身。
	if strings.TrimSpace(in.ProjectID) == "" {
		in.ProjectID = project.ID
	}
	if strings.TrimSpace(in.ProjectName) == "" {
		in.ProjectName = project.Name
	}
	applyEngagementVendor(&in, h)

	result := authletter.Build(in, time.Now().UTC())

	switch format {
	case "json":
		recordJSON, marshalErr := authletter.RecordJSON(result.Record)
		if marshalErr != nil {
			writeSecurityOpsError(c, http.StatusInternalServerError, "render_failed", "无法输出授权记录")
			return
		}
		c.JSON(http.StatusOK, gin.H{
			"documentId": result.DocumentID,
			"qualified":  result.Qualified,
			"attested":   result.Attested,
			"gaps":       result.Gaps,
			"markdown":   result.Markdown,
			"html":       result.HTML,
			"record":     json.RawMessage(recordJSON),
		})
	case "md", "markdown":
		c.Header("Content-Disposition", `attachment; filename="`+result.DocumentID+`.md"`)
		c.Data(http.StatusOK, "text/markdown; charset=utf-8", []byte(result.Markdown))
	default:
		c.Header("Content-Disposition", `attachment; filename="`+result.DocumentID+`.html"`)
		c.Data(http.StatusOK, "text/html; charset=utf-8", []byte(result.HTML))
	}
}

// latestAuthorization 取最近一筆帶有授權編號的授權記錄。
//
// 掃描任務是按 created_at DESC 取的，所以第一筆就是最新的。挑「有 ID 的」是因為
// 沒填編號的任務等於沒有可核對的授權憑據。
func latestAuthorization(runs []database.SecurityOpsRun) securityOpsAuthorization {
	for _, run := range runs {
		var auth securityOpsAuthorization
		if err := json.Unmarshal([]byte(run.AuthorizationJSON), &auth); err != nil {
			continue
		}
		if strings.TrimSpace(auth.ID) != "" {
			return auth
		}
	}
	return securityOpsAuthorization{}
}

// authorizationLetterInput 把平台既有的授權記錄轉成授權書輸入。
func (h *SecurityOpsHandler) authorizationLetterInput(project *database.Project, auth securityOpsAuthorization) authletter.Input {
	in := authletter.Input{
		DocumentID: auth.ID,
		ClientName: "",
		ProjectID:  project.ID,
	}
	if !project.UpdatedAt.IsZero() {
		in.IssuedAt = project.UpdatedAt
	}
	if len(auth.TargetPatterns) > 0 {
		in.Patterns = auth.TargetPatterns
	}
	if len(auth.Operations) > 0 {
		in.Operations = auth.Operations
	}
	if !auth.ValidFrom.IsZero() {
		in.ValidFrom = auth.ValidFrom
	}
	if !auth.ValidUntil.IsZero() {
		in.ValidUntil = auth.ValidUntil
	}
	in.ClientApprover = auth.ApprovedBy
	in.SourceAttested = auth.Attested
	in.SourceRunID = auth.SourceRunID
	in.Inherited = auth.Inherited
	in.InheritedAt = auth.InheritedAt
	// 授權依據：這份授權書轉錄自哪一筆記錄、誰確認的、何時確認的。
	in.Basis = authorizationBasis(auth, h.now())
	return in
}

// mergeAuthorizationLetterQuery 把 query 上的委託方資料合併進輸入。
//
// 空值不覆蓋既有值：GET 路徑已經從授權記錄帶出授權人與編號，不該被空的 query 洗掉。
func mergeAuthorizationLetterQuery(c *gin.Context, in authletter.Input) authletter.Input {
	assign := func(target *string, key string) {
		if value := strings.TrimSpace(c.Query(key)); value != "" {
			*target = value
		}
	}
	assign(&in.ClientName, "clientName")
	assign(&in.ClientTaxID, "clientTaxId")
	assign(&in.ClientAddress, "clientAddress")
	assign(&in.ClientApprover, "clientApprover")
	assign(&in.ClientApproverRole, "clientApproverRole")
	assign(&in.ClientContact, "clientContact")
	assign(&in.VendorName, "vendorName")
	assign(&in.VendorTaxID, "vendorTaxId")
	assign(&in.VendorAddress, "vendorAddress")
	assign(&in.VendorLead, "vendorLead")
	assign(&in.VendorReference, "vendorReference")
	assign(&in.Objective, "objective")
	assign(&in.DocumentID, "documentId")
	return in
}

// applyEngagementVendor 套用平台設定裡的乙方（受託方）資料。
func applyEngagementVendor(in *authletter.Input, h *SecurityOpsHandler) {
	if h == nil || h.config == nil {
		return
	}
	eng := h.config.Engagement
	if strings.TrimSpace(in.VendorName) == "" {
		in.VendorName = eng.VendorName
	}
	if strings.TrimSpace(in.VendorTaxID) == "" {
		in.VendorTaxID = eng.VendorTaxID
	}
	if strings.TrimSpace(in.VendorAddress) == "" {
		in.VendorAddress = eng.VendorAddress
	}
	if strings.TrimSpace(in.VendorLead) == "" {
		in.VendorLead = eng.VendorLead
	}
	if strings.TrimSpace(in.VendorReference) == "" {
		in.VendorReference = eng.VendorReference
	}
}
