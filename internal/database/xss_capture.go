package database

import (
	"database/sql"
	"encoding/json"
	"fmt"
	"strings"
	"time"

	"github.com/google/uuid"
)

// XSSPayload 投出的一段窃密载荷：脚本 + 投递元信息。script 中已内嵌收割地址与共享密钥。
type XSSPayload struct {
	ID             string    `json:"id"`
	CallbackToken  string    `json:"-"`
	Enabled        int       `json:"enabled"`
	Domain         string    `json:"domain"`
	DomainOnly     int       `json:"domain_only"`
	OwnerUserID    string    `json:"owner_user_id,omitempty"`
	ProjectID      string    `json:"project_id,omitempty"`
	ConversationID string    `json:"conversation_id,omitempty"`
	Name           string    `json:"name"`
	SourceURL      string    `json:"source_url,omitempty"`
	Script         string    `json:"script"`
	Status         string    `json:"status"` // armed / fired / expired
	CreatedBy      string    `json:"created_by,omitempty"`
	CreatedAt      time.Time `json:"created_at"`
	UpdatedAt      time.Time `json:"updated_at"`
}

// XSSCapture 一次收割结果：Cookie / localStorage / sessionStorage / URL 片段 / UA。
type XSSCapture struct {
	ID             string            `json:"id"`
	PayloadID      string            `json:"payload_id,omitempty"`
	ProjectID      string            `json:"project_id,omitempty"`
	ConversationID string            `json:"conversation_id,omitempty"`
	Status         string            `json:"status"` // new / seized / analyzed / ignored
	SourceURL      string            `json:"source_url"`
	PageTitle      string            `json:"page_title,omitempty"`
	UserAgent      string            `json:"user_agent,omitempty"`
	ClientIP       string            `json:"client_ip,omitempty"`
	URLFragment    string            `json:"url_fragment,omitempty"`
	Cookies        []XSSCookie       `json:"cookies"`
	LocalStorage   map[string]string `json:"local_storage"`
	SessionStorage map[string]string `json:"session_storage"`
	APIKeys        map[string]string `json:"api_keys,omitempty"`
	SeizedAt       *time.Time        `json:"seized_at,omitempty"`
	CreatedAt      time.Time         `json:"created_at"`
	UpdatedAt      time.Time         `json:"updated_at"`
}

// XSSCookie 一条被收割的 Cookie（不含 HttpOnly：浏览器不会把它暴露给 document.cookie）。
type XSSCookie struct {
	Name     string `json:"name"`
	Value    string `json:"value"`
	Domain   string `json:"domain,omitempty"`
	Path     string `json:"path,omitempty"`
	Secure   *bool  `json:"secure,omitempty"`
	HttpOnly *bool  `json:"http_only,omitempty"`
}

// XSSListFilter 列表/统计共用的筛选条件。
type XSSListFilter struct {
	ProjectID      string
	ConversationID string
	PayloadID      string
	Status         string
}

// appendXSSWhere 拼接 xss 通用查询条件（表名由调用方提供）。
func (f XSSListFilter) appendXSSWhere(query string, args []interface{}, table string) (string, []interface{}) {
	if f.ProjectID != "" {
		query += fmt.Sprintf(" AND %s.project_id = ?", table)
		args = append(args, f.ProjectID)
	}
	if f.ConversationID != "" {
		query += fmt.Sprintf(" AND %s.conversation_id = ?", table)
		args = append(args, f.ConversationID)
	}
	if f.PayloadID != "" {
		query += fmt.Sprintf(" AND %s.payload_id = ?", table)
		args = append(args, f.PayloadID)
	}
	if f.Status != "" {
		query += fmt.Sprintf(" AND %s.status = ?", table)
		args = append(args, f.Status)
	}
	return query, args
}

// appendXSSAccessFilter 项目/会话级 RBAC 可见性过滤（与漏洞一致：项目/会话 owner 或资源指派可见）。
// resourceType 为 rbAC 资源类型（如 "xss_payload" / "xss_capture"），对应 AssignResourceToUser 使用的类型名。
func appendXSSAccessFilter(query string, args []interface{}, access RBACListAccess, table, resourceType string) (string, []interface{}) {
	if table != "xss_payloads" && table != "xss_captures" {
		return query + " AND 0=1", args
	}
	user := strings.TrimSpace(access.UserID)
	if user == "" {
		return query + " AND 0=1", args
	}
	if access.Scope == RBACScopeAll {
		return query, args
	}
	if access.Scope != RBACScopeOwn && access.Scope != RBACScopeAssigned {
		return query + " AND 0=1", args
	}
	var terms []string
	add := func(expr string) { terms = append(terms, expr); args = append(args, user) }
	own := access.Scope == RBACScopeOwn
	if table == "xss_payloads" && own {
		add("COALESCE(NULLIF(" + table + ".owner_user_id,'')," + table + ".created_by)=?")
	}
	add("EXISTS (SELECT 1 FROM rbac_resource_assignments ra WHERE ra.user_id=? AND ra.resource_type=" + quoted(resourceType) + " AND ra.resource_id=" + table + ".id)")
	parent := func(alias string) {
		if own {
			add("EXISTS (SELECT 1 FROM projects p WHERE p.id=" + alias + ".project_id AND p.owner_user_id=?)")
			add("EXISTS (SELECT 1 FROM conversations c WHERE c.id=" + alias + ".conversation_id AND c.owner_user_id=?)")
			add("EXISTS (SELECT 1 FROM conversations c JOIN projects p ON p.id=c.project_id WHERE c.id=" + alias + ".conversation_id AND p.owner_user_id=?)")
		}
		add("EXISTS (SELECT 1 FROM rbac_resource_assignments ra WHERE ra.user_id=? AND ((ra.resource_type='project' AND ra.resource_id=" + alias + ".project_id) OR (ra.resource_type='conversation' AND ra.resource_id=" + alias + ".conversation_id)))")
		add("EXISTS (SELECT 1 FROM conversations c JOIN rbac_resource_assignments ra ON ra.resource_id=c.project_id AND ra.resource_type='project' WHERE c.id=" + alias + ".conversation_id AND ra.user_id=?)")
	}
	parent(table)
	if table == "xss_captures" {
		sub, subArgs := appendXSSAccessFilter("SELECT 1 FROM xss_payloads WHERE xss_payloads.id=xss_captures.payload_id", nil, access, "xss_payloads", "xss_payload")
		terms = append(terms, "EXISTS ("+sub+")")
		args = append(args, subArgs...)
	}
	return query + " AND (" + strings.Join(terms, " OR ") + ")", args
}

func quoted(s string) string {
	return "'" + strings.ReplaceAll(s, "'", "''") + "'"
}

// UserCanAccessXSS 检查某条载荷/收割记录是否对用户可见（与列表过滤同一规则）。
func (db *DB) UserCanAccessXSS(access RBACListAccess, table, resourceType, id string) bool {
	if (table != "xss_payloads" || resourceType != "xss_payload") && (table != "xss_captures" || resourceType != "xss_capture") {
		return false
	}
	q, args := appendXSSAccessFilter("SELECT 1 FROM "+table+" WHERE id = ?", []interface{}{id}, access, table, resourceType)
	var one int
	if err := db.QueryRow(q, args...).Scan(&one); err != nil {
		return false
	}
	return true
}

func (db *DB) xssResolveProjectID(conversationID string) string {
	if strings.TrimSpace(conversationID) == "" {
		return ""
	}
	pid, err := db.GetConversationProjectID(conversationID)
	if err != nil {
		return ""
	}
	return strings.TrimSpace(pid)
}

// CreateXSSPayload 存储一段新载荷。
func (db *DB) CreateXSSPayload(p *XSSPayload) (*XSSPayload, error) {
	if p.ID == "" {
		p.ID = uuid.New().String()
	}
	if p.Status == "" {
		p.Status = "armed"
	}
	now := time.Now()
	if p.CreatedAt.IsZero() {
		p.CreatedAt = now
	}
	p.UpdatedAt = now
	if p.ProjectID == "" {
		p.ProjectID = db.xssResolveProjectID(p.ConversationID)
	}
	_, err := db.Exec(`
		INSERT INTO xss_payloads (id, project_id, conversation_id, name, source_url, script, status, created_by, created_at, updated_at, callback_token, enabled, domain, domain_only, owner_user_id)
		VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		p.ID, nullIfEmpty(p.ProjectID), nullIfEmpty(p.ConversationID), p.Name, p.SourceURL, p.Script, p.Status, nullIfEmpty(p.CreatedBy), p.CreatedAt, p.UpdatedAt, nullIfEmpty(p.CallbackToken), p.Enabled, p.Domain, p.DomainOnly, nullIfEmpty(p.OwnerUserID),
	)
	if err != nil {
		return nil, fmt.Errorf("创建XSS载荷失败: %w", err)
	}
	return p, nil
}

// GetXSSPayload 获取载荷详情。
func (db *DB) GetXSSPayload(id string) (*XSSPayload, error) {
	var p XSSPayload
	err := db.QueryRow(`
		SELECT id, COALESCE(project_id,''), COALESCE(conversation_id,''), name, source_url, script, status, COALESCE(created_by,''), created_at, updated_at, COALESCE(callback_token,''), enabled, domain, domain_only, COALESCE(owner_user_id,'')
		FROM xss_payloads WHERE id = ?`, id).
		Scan(&p.ID, &p.ProjectID, &p.ConversationID, &p.Name, &p.SourceURL, &p.Script, &p.Status, &p.CreatedBy, &p.CreatedAt, &p.UpdatedAt, &p.CallbackToken, &p.Enabled, &p.Domain, &p.DomainOnly, &p.OwnerUserID)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, err
		}
		return nil, fmt.Errorf("获取XSS载荷失败: %w", err)
	}
	return &p, nil
}

// ListXSSPayloads 分页列出载荷（按创建时间倒序）。
func (db *DB) ListXSSPayloads(filter XSSListFilter, access RBACListAccess, offset, limit int) ([]*XSSPayload, int, error) {
	query := ` FROM xss_payloads WHERE 1=1`
	args := []interface{}{}
	query, args = filter.appendXSSWhere(query, args, "xss_payloads")
	query, args = appendXSSAccessFilter(query, args, access, "xss_payloads", "xss_payload")

	total := 0
	if err := db.QueryRow("SELECT COUNT(*)"+query, args...).Scan(&total); err != nil {
		return nil, 0, fmt.Errorf("统计XSS载荷失败: %w", err)
	}

	if limit <= 0 {
		limit = 50
	}
	if offset < 0 {
		offset = 0
	}
	rows, err := db.Query(`SELECT id, COALESCE(project_id,''), COALESCE(conversation_id,''), name, source_url, script, status, COALESCE(created_by,''), created_at, updated_at, COALESCE(callback_token,''), enabled, domain, domain_only, COALESCE(owner_user_id,'')`+
		query+` ORDER BY xss_payloads.created_at DESC LIMIT ? OFFSET ?`,
		append(args, limit, offset)...)
	if err != nil {
		return nil, 0, fmt.Errorf("查询XSS载荷失败: %w", err)
	}
	defer rows.Close()

	out := []*XSSPayload{}
	for rows.Next() {
		var p XSSPayload
		if err := rows.Scan(&p.ID, &p.ProjectID, &p.ConversationID, &p.Name, &p.SourceURL, &p.Script, &p.Status, &p.CreatedBy, &p.CreatedAt, &p.UpdatedAt, &p.CallbackToken, &p.Enabled, &p.Domain, &p.DomainOnly, &p.OwnerUserID); err != nil {
			return nil, 0, err
		}
		out = append(out, &p)
	}
	return out, total, rows.Err()
}

// MarkXSSPayloadFired 将载荷标记为已触发（命中收割不归零，仅记录状态供审计）。
func (db *DB) MarkXSSPayloadFired(id string) error {
	_, err := db.Exec(`UPDATE xss_payloads SET status = 'fired', updated_at = ? WHERE id = ? AND status <> 'fired'`, time.Now(), id)
	if err != nil {
		return fmt.Errorf("更新XSS载荷状态失败: %w", err)
	}
	return nil
}

// DeleteXSSPayload 删除载荷（关联收割记录 payload_id 置空）。
func (db *DB) DeleteXSSPayload(id string) error {
	if _, err := db.Exec(`DELETE FROM xss_payloads WHERE id = ?`, id); err != nil {
		return fmt.Errorf("删除XSS载荷失败: %w", err)
	}
	return nil
}

// CreateXSSCapture 写入一次收割。dedupKey 为空时不做去重。
type xssExecer interface {
	Exec(string, ...interface{}) (sql.Result, error)
}

func (db *DB) CreateXSSCapture(c *XSSCapture) (*XSSCapture, error) {
	return db.createXSSCapture(db.DB, c)
}
func (db *DB) PersistXSSCallback(c *XSSCapture) (*XSSCapture, error) {
	tx, err := db.Begin()
	if err != nil {
		return nil, err
	}
	defer tx.Rollback()
	row, err := db.createXSSCapture(tx, c)
	if err != nil {
		return nil, err
	}
	if _, err = tx.Exec("UPDATE xss_payloads SET status='fired', updated_at=? WHERE id=?", time.Now(), c.PayloadID); err != nil {
		return nil, err
	}
	if err = tx.Commit(); err != nil {
		return nil, err
	}
	return row, nil
}
func (db *DB) createXSSCapture(exec xssExecer, c *XSSCapture) (*XSSCapture, error) {
	if c.ID == "" {
		c.ID = uuid.New().String()
	}
	if c.Status == "" {
		c.Status = "new"
	}
	now := time.Now()
	if c.CreatedAt.IsZero() {
		c.CreatedAt = now
	}
	c.UpdatedAt = now
	cookiesJSON, _ := json.Marshal(c.Cookies)
	localJSON, _ := json.Marshal(c.LocalStorage)
	sessionJSON, _ := json.Marshal(c.SessionStorage)
	apiJSON, _ := json.Marshal(c.APIKeys)

	_, err := exec.Exec(`
		INSERT INTO xss_captures (
			id, payload_id, project_id, conversation_id, status, source_url, page_title, user_agent, client_ip,
			url_fragment, cookies_json, local_storage_json, session_storage_json, api_keys_json,
			seized_at, created_at, updated_at
		) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)`,
		c.ID, nullIfEmpty(c.PayloadID), nullIfEmpty(c.ProjectID), nullIfEmpty(c.ConversationID), c.Status,
		c.SourceURL, c.PageTitle, c.UserAgent, c.ClientIP, c.URLFragment,
		string(cookiesJSON), string(localJSON), string(sessionJSON), string(apiJSON),
		c.SeizedAt, c.CreatedAt, c.UpdatedAt,
	)
	if err != nil {
		return nil, fmt.Errorf("创建XSS收割记录失败: %w", err)
	}
	return c, nil
}

// GetXSSCapture 获取收割详情。
func (db *DB) GetXSSCapture(id string) (*XSSCapture, error) {
	var c XSSCapture
	var cookiesJSON, localJSON, sessionJSON, apiJSON string
	var seizedAt sql.NullTime
	err := db.QueryRow(`
		SELECT id, COALESCE(payload_id,''), COALESCE(project_id,''), COALESCE(conversation_id,''), status, source_url, page_title, user_agent, client_ip,
			url_fragment, cookies_json, local_storage_json, session_storage_json, api_keys_json, seized_at, created_at, updated_at
		FROM xss_captures WHERE id = ?`, id).
		Scan(&c.ID, &c.PayloadID, &c.ProjectID, &c.ConversationID, &c.Status, &c.SourceURL, &c.PageTitle, &c.UserAgent, &c.ClientIP,
			&c.URLFragment, &cookiesJSON, &localJSON, &sessionJSON, &apiJSON, &seizedAt, &c.CreatedAt, &c.UpdatedAt)
	if err != nil {
		if err == sql.ErrNoRows {
			return nil, err
		}
		return nil, fmt.Errorf("获取XSS收割记录失败: %w", err)
	}
	c.Cookies = []XSSCookie{}
	c.LocalStorage = map[string]string{}
	c.SessionStorage = map[string]string{}
	if cookiesJSON != "{}" && cookiesJSON != "null" {
		if err := json.Unmarshal([]byte(cookiesJSON), &c.Cookies); err != nil {
			return nil, fmt.Errorf("invalid stored cookies JSON")
		}
	}
	if err := json.Unmarshal([]byte(localJSON), &c.LocalStorage); err != nil {
		return nil, fmt.Errorf("invalid stored capture metadata")
	}
	if err := json.Unmarshal([]byte(sessionJSON), &c.SessionStorage); err != nil {
		return nil, fmt.Errorf("invalid stored capture metadata")
	}
	if err := json.Unmarshal([]byte(apiJSON), &c.APIKeys); err != nil {
		return nil, fmt.Errorf("invalid stored capture metadata")
	}
	if seizedAt.Valid {
		c.SeizedAt = &seizedAt.Time
	}
	return &c, nil
}

// ListXSSCaptures 分页列出收割记录（按创建时间倒序）。
func (db *DB) ListXSSCaptures(filter XSSListFilter, access RBACListAccess, offset, limit int) ([]*XSSCapture, int, error) {
	query := ` FROM xss_captures WHERE 1=1`
	args := []interface{}{}
	query, args = filter.appendXSSWhere(query, args, "xss_captures")
	query, args = appendXSSAccessFilter(query, args, access, "xss_captures", "xss_capture")

	total := 0
	if err := db.QueryRow("SELECT COUNT(*)"+query, args...).Scan(&total); err != nil {
		return nil, 0, fmt.Errorf("统计XSS收割记录失败: %w", err)
	}

	if limit <= 0 {
		limit = 50
	}
	if offset < 0 {
		offset = 0
	}
	rows, err := db.Query(`SELECT id, COALESCE(payload_id,''), COALESCE(project_id,''), COALESCE(conversation_id,''), status, source_url, page_title, user_agent, client_ip,
			url_fragment, cookies_json, local_storage_json, session_storage_json, api_keys_json, seized_at, created_at, updated_at`+
		query+` ORDER BY xss_captures.created_at DESC LIMIT ? OFFSET ?`,
		append(args, limit, offset)...)
	if err != nil {
		return nil, 0, fmt.Errorf("查询XSS收割记录失败: %w", err)
	}
	defer rows.Close()

	out := []*XSSCapture{}
	for rows.Next() {
		var c XSSCapture
		var cookiesJSON, localJSON, sessionJSON, apiJSON string
		var seizedAt sql.NullTime
		if err := rows.Scan(&c.ID, &c.PayloadID, &c.ProjectID, &c.ConversationID, &c.Status, &c.SourceURL, &c.PageTitle, &c.UserAgent, &c.ClientIP,
			&c.URLFragment, &cookiesJSON, &localJSON, &sessionJSON, &apiJSON, &seizedAt, &c.CreatedAt, &c.UpdatedAt); err != nil {
			return nil, 0, err
		}
		c.Cookies = []XSSCookie{}
		c.LocalStorage = map[string]string{}
		c.SessionStorage = map[string]string{}
		if cookiesJSON != "{}" && cookiesJSON != "null" {
			if err := json.Unmarshal([]byte(cookiesJSON), &c.Cookies); err != nil {
				return nil, 0, fmt.Errorf("invalid stored cookies JSON")
			}
		}
		if err := json.Unmarshal([]byte(localJSON), &c.LocalStorage); err != nil {
			return nil, 0, fmt.Errorf("invalid stored capture metadata")
		}
		if err := json.Unmarshal([]byte(sessionJSON), &c.SessionStorage); err != nil {
			return nil, 0, fmt.Errorf("invalid stored capture metadata")
		}
		if err := json.Unmarshal([]byte(apiJSON), &c.APIKeys); err != nil {
			return nil, 0, fmt.Errorf("invalid stored capture metadata")
		}
		if seizedAt.Valid {
			c.SeizedAt = &seizedAt.Time
		}
		out = append(out, &c)
	}
	return out, total, rows.Err()
}

// UpdateXSSCaptureStatus 更新收割记录状态（new→seized 等，记录接管时间）。
func (db *DB) UpdateXSSCaptureStatus(id, status string) error {
	status = strings.TrimSpace(strings.ToLower(status))
	valid := map[string]bool{"new": true, "seized": true, "analyzed": true, "ignored": true}
	if !valid[status] {
		return fmt.Errorf("非法收割状态: %q", status)
	}
	now := time.Now()
	seizedClause := ""
	args := []interface{}{now, status, id}
	if status == "seized" {
		seizedClause = ", seized_at = COALESCE(seized_at, ?)"
		args = []interface{}{now, now, status, id}
	}
	_, err := db.Exec("UPDATE xss_captures SET updated_at = ?"+seizedClause+", status = ? WHERE id = ?", args...)
	if err != nil {
		return fmt.Errorf("更新XSS收割状态失败: %w", err)
	}
	return nil
}

// DeleteXSSCapture 删除收割记录。
func (db *DB) DeleteXSSCapture(id string) error {
	if _, err := db.Exec(`DELETE FROM xss_captures WHERE id = ?`, id); err != nil {
		return fmt.Errorf("删除XSS收割记录失败: %w", err)
	}
	return nil
}
