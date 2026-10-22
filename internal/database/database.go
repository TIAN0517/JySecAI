package database

import (
	"database/sql"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"time"

	"crypto/rand"
	"strconv"

	"github.com/google/uuid"
	_ "github.com/mattn/go-sqlite3"
	"go.uber.org/zap"
)

const (
	// WAL 允許並行讀，但同一時間只有一個寫者。連線池過大時，並行寫入會在
	// DEFERRED 交易升級寫鎖時立刻失敗，busy_timeout 來不及生效。
	sqliteMaxOpenConns  = 8
	sqliteMaxIdleConns  = 4
	sqliteBusyTimeoutMS = 30000
	// 以页为单位的自动 checkpoint 触发阈值（默认 1000 页，约 4MB @ 4KB/page）。
	sqliteWALAutoCheckpointPages = 1000
	// 控制 WAL 目标上限，避免异常场景持续膨胀（256MB）。
	sqliteJournalSizeLimitBytes = 256 * 1024 * 1024
	// 定时执行 PASSIVE checkpoint，平滑推进 WAL 回收。
	sqlitePassiveCheckpointInterval = 300 * time.Second
)

// sqliteOpenDSN 在 Begin 時就預留寫鎖。DEFERRED 升級可能不走 busy_timeout 而直接失敗。
func sqliteOpenDSN(path string) string {
	return fmt.Sprintf("%s?_journal_mode=WAL&_foreign_keys=1&_busy_timeout=%d&_synchronous=NORMAL&_txlock=immediate", path, sqliteBusyTimeoutMS)
}

// configureDBPool 设置 SQLite 连接池参数，提升并发稳定性
func configureDBPool(db *sql.DB) {
	// SQLite 同一时间只允许一个写入者；过高连接数会放大锁竞争和 WAL 回收延迟。
	db.SetMaxOpenConns(sqliteMaxOpenConns)
	db.SetMaxIdleConns(sqliteMaxIdleConns)
	db.SetConnMaxLifetime(30 * time.Minute)
}

// configureSQLitePragmas 调整 WAL 回收行为，降低 -wal 文件长期膨胀风险。
func configureSQLitePragmas(db *sql.DB) error {
	if _, err := db.Exec(fmt.Sprintf("PRAGMA wal_autocheckpoint=%d", sqliteWALAutoCheckpointPages)); err != nil {
		return fmt.Errorf("设置 wal_autocheckpoint 失败: %w", err)
	}
	if _, err := db.Exec(fmt.Sprintf("PRAGMA journal_size_limit=%d", sqliteJournalSizeLimitBytes)); err != nil {
		return fmt.Errorf("设置 journal_size_limit 失败: %w", err)
	}
	return nil
}

// DB 数据库连接
type DB struct {
	*sql.DB
	logger                   *zap.Logger
	conversationArtifactsDir string
	einoPlantaskBaseDir      string // skills_dir + plantask_rel_dir (per-conversation subdirs)
	einoCheckpointBaseDir    string // checkpoint_dir root (per-conversation subdirs)
	einoReductionRootDir     string // reduction_root_dir or default tmp/reduction (conversations/<id> subdirs)
	einoWorkspaceRootDir     string // workspace_root_dir or default tmp/workspace (projects|conversations/<id> subdirs)
	checkpointLoopName       string
	checkpointStop           chan struct{}
	checkpointDone           chan struct{}
	closeOnce                sync.Once
	closeErr                 error
	vulnerabilityWriteMu     sync.Mutex
	vulnerabilityCreatedHook func(*Vulnerability)
	credentialCipher         *credentialCipher
}

// startPassiveCheckpointLoop 启动后台 PASSIVE checkpoint 循环。
func (db *DB) startPassiveCheckpointLoop(name string) {
	if sqlitePassiveCheckpointInterval <= 0 || db == nil || db.DB == nil {
		return
	}
	db.checkpointLoopName = strings.TrimSpace(name)
	db.checkpointStop = make(chan struct{})
	db.checkpointDone = make(chan struct{})

	go func() {
		defer close(db.checkpointDone)
		ticker := time.NewTicker(sqlitePassiveCheckpointInterval)
		defer ticker.Stop()

		// 启动后先尝试一次，尽快回收已有 WAL 堆积。
		db.runPassiveCheckpoint("startup")
		for {
			select {
			case <-db.checkpointStop:
				return
			case <-ticker.C:
				db.runPassiveCheckpoint("ticker")
			}
		}
	}()
}

// runPassiveCheckpoint 执行一次 PRAGMA wal_checkpoint(PASSIVE)。
func (db *DB) runPassiveCheckpoint(trigger string) {
	if db == nil || db.DB == nil {
		return
	}
	startAt := time.Now()
	var busy, logFrames, checkpointed int
	err := db.QueryRow("PRAGMA wal_checkpoint(PASSIVE)").Scan(&busy, &logFrames, &checkpointed)
	if db.logger == nil {
		return
	}
	fields := []zap.Field{
		zap.String("db", db.checkpointLoopName),
		zap.String("trigger", trigger),
		zap.Int("busy", busy),
		zap.Int("log_frames", logFrames),
		zap.Int("checkpointed_frames", checkpointed),
		zap.Int64("elapsed_ms", time.Since(startAt).Milliseconds()),
	}
	if err != nil {
		db.logger.Warn("SQLite PASSIVE checkpoint 完成（失败）",
			append(fields, zap.Error(err))...,
		)
		return
	}
	if busy > 0 {
		db.logger.Debug("SQLite PASSIVE checkpoint 完成（部分推进）", fields...)
		return
	}
	db.logger.Debug("SQLite PASSIVE checkpoint 完成（成功）", fields...)
}

// NewDB 创建数据库连接
func NewDB(dbPath string, logger *zap.Logger) (*DB, error) {
	credentialCipher, err := newCredentialCipher(dbPath)
	if err != nil {
		return nil, fmt.Errorf("初始化凭证加密失败: %w", err)
	}
	db, err := sql.Open("sqlite3", sqliteOpenDSN(dbPath))
	if err != nil {
		return nil, fmt.Errorf("打开数据库失败: %w", err)
	}

	configureDBPool(db)

	if err := db.Ping(); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("连接数据库失败: %w", err)
	}
	if err := configureSQLitePragmas(db); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("配置数据库 PRAGMA 失败: %w", err)
	}

	database := &DB{
		DB:               db,
		logger:           logger,
		credentialCipher: credentialCipher,
	}
	// Keep conversation-scoped artifacts near database files, so cleanup can follow conversation lifecycle.
	baseDir := filepath.Join(filepath.Dir(dbPath), "conversation_artifacts")
	if mkErr := os.MkdirAll(baseDir, 0o755); mkErr == nil {
		database.conversationArtifactsDir = baseDir
	} else if logger != nil {
		logger.Warn("创建 conversation artifacts 目录失败", zap.String("dir", baseDir), zap.Error(mkErr))
	}

	// 初始化表
	if err := database.initTables(); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("初始化表失败: %w", err)
	}
	if err := database.migrateLegacyToolGuardBlocks(); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("迁移历史安全拦截记录失败: %w", err)
	}
	if err := database.migrateCredentialEncryption(); err != nil {
		_ = db.Close()
		return nil, fmt.Errorf("迁移数据库凭证加密失败: %w", err)
	}
	database.startPassiveCheckpointLoop("conversations")

	return database, nil
}

// WorkspaceRootDir returns the agent workspace root directory
// (agent.workspace_root_dir; empty means the built-in tmp/workspace default).
func (db *DB) WorkspaceRootDir() string {
	return db.einoWorkspaceRootDir
}

// SetEinoConversationDirs configures best-effort filesystem cleanup on DeleteConversation.
// plantaskBase is skills_root/plantask_rel (no conversation id); checkpointBase is checkpoint_dir root.
// reductionRoot is reduction_root_dir from config; empty uses tmp/reduction (conversation-scoped subdirs only).
// workspaceRoot is agent.workspace_root_dir from config; empty uses tmp/workspace.
func (db *DB) SetEinoConversationDirs(plantaskBase, checkpointBase, reductionRoot, workspaceRoot string) {
	if db == nil {
		return
	}
	db.einoPlantaskBaseDir = strings.TrimSpace(plantaskBase)
	db.einoCheckpointBaseDir = strings.TrimSpace(checkpointBase)
	db.einoReductionRootDir = strings.TrimSpace(reductionRoot)
	db.einoWorkspaceRootDir = strings.TrimSpace(workspaceRoot)
}

// initTables 初始化数据库表
func (db *DB) initTables() error {
	// 创建对话表（last_react_input / last_react_output 存「代理消息轨迹」JSON 与助手摘要，列名保留以兼容已有库）
	createConversationsTable := `
	CREATE TABLE IF NOT EXISTS conversations (
		id TEXT PRIMARY KEY,
		title TEXT NOT NULL,
		created_at DATETIME NOT NULL,
		updated_at DATETIME NOT NULL,
		role_name TEXT NOT NULL DEFAULT '默认',
		agent_mode TEXT NOT NULL DEFAULT 'eino_single',
		last_react_input TEXT,
		last_react_output TEXT
	);`

	// 创建消息表
	createMessagesTable := `
	CREATE TABLE IF NOT EXISTS messages (
		id TEXT PRIMARY KEY,
		conversation_id TEXT NOT NULL,
		role TEXT NOT NULL,
		content TEXT NOT NULL,
		mcp_execution_ids TEXT,
		created_at DATETIME NOT NULL,
		updated_at DATETIME NOT NULL,
		FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
	);`

	// 创建过程详情表
	createProcessDetailsTable := `
	CREATE TABLE IF NOT EXISTS process_details (
		id TEXT PRIMARY KEY,
		message_id TEXT NOT NULL,
		conversation_id TEXT NOT NULL,
		event_type TEXT NOT NULL,
		message TEXT,
		data TEXT,
		created_at DATETIME NOT NULL,
		FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
		FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
	);`

	// 创建模型 Token 用量表：process_details 负责时间线回放，本表负责结构化聚合统计。
	createModelTokenUsageTable := `
	CREATE TABLE IF NOT EXISTS model_token_usage (
		id TEXT PRIMARY KEY,
		process_detail_id TEXT NOT NULL UNIQUE,
		message_id TEXT NOT NULL,
		conversation_id TEXT NOT NULL,
		project_id TEXT,
		source TEXT NOT NULL DEFAULT '',
		orchestration TEXT NOT NULL DEFAULT '',
		reason TEXT NOT NULL DEFAULT '',
		model TEXT NOT NULL DEFAULT '',
		model_calls INTEGER NOT NULL DEFAULT 0,
		prompt_tokens INTEGER NOT NULL DEFAULT 0,
		completion_tokens INTEGER NOT NULL DEFAULT 0,
		total_tokens INTEGER NOT NULL DEFAULT 0,
		cached_tokens INTEGER NOT NULL DEFAULT 0,
		reasoning_tokens INTEGER NOT NULL DEFAULT 0,
		created_at DATETIME NOT NULL,
		updated_at DATETIME NOT NULL,
		FOREIGN KEY (process_detail_id) REFERENCES process_details(id) ON DELETE CASCADE,
		FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE,
		FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
		FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
	);`

	// 创建工具执行记录表
	createToolExecutionsTable := `
	CREATE TABLE IF NOT EXISTS tool_executions (
		id TEXT PRIMARY KEY,
		tool_name TEXT NOT NULL,
		arguments TEXT NOT NULL,
		status TEXT NOT NULL,
		result TEXT,
		error TEXT,
		start_time DATETIME NOT NULL,
		end_time DATETIME,
		duration_ms INTEGER,
		partial_output TEXT,
		partial_output_bytes INTEGER NOT NULL DEFAULT 0,
		partial_output_truncated INTEGER NOT NULL DEFAULT 0,
		partial_output_updated_at DATETIME,
		owner_user_id TEXT,
		conversation_id TEXT,
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
	);`

	// 创建工具统计表
	createToolStatsTable := `
	CREATE TABLE IF NOT EXISTS tool_stats (
		tool_name TEXT PRIMARY KEY,
		total_calls INTEGER NOT NULL DEFAULT 0,
		success_calls INTEGER NOT NULL DEFAULT 0,
		failed_calls INTEGER NOT NULL DEFAULT 0,
		last_call_time DATETIME,
		updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
	);`

	// 创建Skills统计表
	createSkillStatsTable := `
	CREATE TABLE IF NOT EXISTS skill_stats (
		skill_name TEXT PRIMARY KEY,
		total_calls INTEGER NOT NULL DEFAULT 0,
		success_calls INTEGER NOT NULL DEFAULT 0,
		failed_calls INTEGER NOT NULL DEFAULT 0,
		last_call_time DATETIME,
		updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
	);`

	// 创建攻击链节点表
	createAttackChainNodesTable := `
	CREATE TABLE IF NOT EXISTS attack_chain_nodes (
		id TEXT PRIMARY KEY,
		conversation_id TEXT NOT NULL,
		node_type TEXT NOT NULL,
		node_name TEXT NOT NULL,
		tool_execution_id TEXT,
		metadata TEXT,
		risk_score INTEGER DEFAULT 0,
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
		FOREIGN KEY (tool_execution_id) REFERENCES tool_executions(id) ON DELETE SET NULL
	);`

	// 创建攻击链边表
	createAttackChainEdgesTable := `
	CREATE TABLE IF NOT EXISTS attack_chain_edges (
		id TEXT PRIMARY KEY,
		conversation_id TEXT NOT NULL,
		source_node_id TEXT NOT NULL,
		target_node_id TEXT NOT NULL,
		edge_type TEXT NOT NULL,
		weight INTEGER DEFAULT 1,
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE,
		FOREIGN KEY (source_node_id) REFERENCES attack_chain_nodes(id) ON DELETE CASCADE,
		FOREIGN KEY (target_node_id) REFERENCES attack_chain_nodes(id) ON DELETE CASCADE
	);`

	// 创建知识检索日志表（保留在会话数据库中，因为有外键关联）
	createKnowledgeRetrievalLogsTable := `
	CREATE TABLE IF NOT EXISTS knowledge_retrieval_logs (
		id TEXT PRIMARY KEY,
		conversation_id TEXT,
		message_id TEXT,
		query TEXT NOT NULL,
		risk_type TEXT,
		retrieved_items TEXT,
		created_at DATETIME NOT NULL,
		FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL,
		FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE SET NULL
	);`

	// 机器人会话绑定表（用于跨重启保持「平台+租户+用户」到 conversation 的映射）
	createRobotUserSessionsTable := `
	CREATE TABLE IF NOT EXISTS robot_user_sessions (
		session_key TEXT PRIMARY KEY,
		conversation_id TEXT NOT NULL,
		role_name TEXT NOT NULL DEFAULT '默认',
		agent_mode TEXT NOT NULL DEFAULT 'eino_single',
		updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE CASCADE
	);`

	// 创建项目表
	createProjectsTable := `
	CREATE TABLE IF NOT EXISTS projects (
		id TEXT PRIMARY KEY,
		name TEXT NOT NULL,
		description TEXT,
		scope_json TEXT,
		status TEXT NOT NULL DEFAULT 'active',
		pinned INTEGER NOT NULL DEFAULT 0,
		created_at DATETIME NOT NULL,
		updated_at DATETIME NOT NULL
	);`

	// 创建项目事实表（黑板）
	createProjectFactsTable := `
	CREATE TABLE IF NOT EXISTS project_facts (
		id TEXT PRIMARY KEY,
		project_id TEXT NOT NULL,
		fact_key TEXT NOT NULL,
		category TEXT NOT NULL DEFAULT 'note',
		summary TEXT NOT NULL DEFAULT '',
		body TEXT,
		confidence TEXT NOT NULL DEFAULT 'tentative',
		source_conversation_id TEXT,
		source_message_id TEXT,
		pinned INTEGER NOT NULL DEFAULT 0,
		related_vulnerability_id TEXT,
		created_at DATETIME NOT NULL,
		updated_at DATETIME NOT NULL,
		FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
		UNIQUE(project_id, fact_key)
	);`

	// 项目事实关系边（黑板 DAG）
	createProjectFactEdgesTable := `
	CREATE TABLE IF NOT EXISTS project_fact_edges (
		id TEXT PRIMARY KEY,
		project_id TEXT NOT NULL,
		source_fact_key TEXT NOT NULL,
		target_fact_key TEXT NOT NULL,
		edge_type TEXT NOT NULL,
		confidence TEXT NOT NULL DEFAULT 'tentative',
		source_conversation_id TEXT,
		created_at DATETIME NOT NULL,
		updated_at DATETIME NOT NULL,
		FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
		UNIQUE(project_id, source_fact_key, target_fact_key, edge_type)
	);`

	// 创建漏洞表
	createVulnerabilitiesTable := `
	CREATE TABLE IF NOT EXISTS vulnerabilities (
		id TEXT PRIMARY KEY,
		conversation_id TEXT,
		conversation_tag TEXT,
		task_tag TEXT,
		title TEXT NOT NULL,
		description TEXT,
		severity TEXT NOT NULL,
		status TEXT NOT NULL DEFAULT 'open',
		confidence INTEGER NOT NULL DEFAULT 0,
		vulnerability_type TEXT,
		target TEXT,
		preconditions TEXT,
		reproduction_steps TEXT,
		evidence TEXT,
		impact TEXT,
		recommendation TEXT,
		retest_notes TEXT,
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		project_id TEXT,
		FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
	);`

	// 漏洞分流執行紀錄。一次執行一列，proposal_json 存 AI 的完整建議。
	// 分流本身不動 vulnerabilities.status，套用是另一次明確的動作。
	createVulnerabilityTriageRunsTable := `
	CREATE TABLE IF NOT EXISTS vulnerability_triage_runs (
		id TEXT PRIMARY KEY,
		scope_label TEXT NOT NULL DEFAULT '',
		scope_json TEXT NOT NULL DEFAULT '',
		examined INTEGER NOT NULL DEFAULT 0,
		group_count INTEGER NOT NULL DEFAULT 0,
		merged_count INTEGER NOT NULL DEFAULT 0,
		headline TEXT NOT NULL DEFAULT '',
		summary TEXT NOT NULL DEFAULT '',
		proposal_json TEXT NOT NULL DEFAULT '{}',
		model TEXT NOT NULL DEFAULT '',
		created_by TEXT NOT NULL DEFAULT '',
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		applied_at DATETIME,
		applied_by TEXT NOT NULL DEFAULT '',
		applied_count INTEGER NOT NULL DEFAULT 0
	);`

	createAssetsTable := `
	CREATE TABLE IF NOT EXISTS assets (
		id TEXT PRIMARY KEY,
		dedup_key TEXT NOT NULL UNIQUE, project_id TEXT,
		host TEXT NOT NULL DEFAULT '', ip TEXT NOT NULL DEFAULT '', port INTEGER NOT NULL DEFAULT 0,
		domain TEXT NOT NULL DEFAULT '', protocol TEXT NOT NULL DEFAULT '', title TEXT NOT NULL DEFAULT '',
		server TEXT NOT NULL DEFAULT '', country TEXT NOT NULL DEFAULT '', province TEXT NOT NULL DEFAULT '', city TEXT NOT NULL DEFAULT '',
		responsible_person TEXT NOT NULL DEFAULT '', department TEXT NOT NULL DEFAULT '', business_system TEXT NOT NULL DEFAULT '',
		environment TEXT NOT NULL DEFAULT '', criticality TEXT NOT NULL DEFAULT '',
		source TEXT NOT NULL DEFAULT 'manual', source_query TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'active',
		vulnerability_count INTEGER NOT NULL DEFAULT 0, risk_score INTEGER NOT NULL DEFAULT 0, risk_level TEXT NOT NULL DEFAULT 'unassessed',
		tags_json TEXT NOT NULL DEFAULT '[]', first_seen_at DATETIME NOT NULL, last_seen_at DATETIME NOT NULL,
		created_at DATETIME NOT NULL, updated_at DATETIME NOT NULL, owner_user_id TEXT,
		FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE SET NULL
	);`

	createVulnerabilityAlertSubscriptionsTable := `
	CREATE TABLE IF NOT EXISTS vulnerability_alert_subscriptions (
		user_id TEXT PRIMARY KEY,
		enabled INTEGER NOT NULL DEFAULT 0,
		min_severity TEXT NOT NULL DEFAULT 'high',
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (user_id) REFERENCES rbac_users(id) ON DELETE CASCADE
	);`
	createVulnerabilityAlertDeliveriesTable := `
	CREATE TABLE IF NOT EXISTS vulnerability_alert_deliveries (
		id INTEGER PRIMARY KEY AUTOINCREMENT,
		vulnerability_id TEXT NOT NULL,
		user_id TEXT NOT NULL,
		platform TEXT NOT NULL,
		external_user_id TEXT NOT NULL,
		status TEXT NOT NULL DEFAULT 'pending',
		attempts INTEGER NOT NULL DEFAULT 0,
		next_attempt_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		last_error TEXT NOT NULL DEFAULT '',
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		UNIQUE(vulnerability_id, platform, external_user_id),
		FOREIGN KEY (vulnerability_id) REFERENCES vulnerabilities(id) ON DELETE CASCADE,
		FOREIGN KEY (user_id) REFERENCES rbac_users(id) ON DELETE CASCADE
	);`

	// 创建批量任务队列表
	createBatchTaskQueuesTable := `
	CREATE TABLE IF NOT EXISTS batch_task_queues (
		id TEXT PRIMARY KEY,
		title TEXT,
		role TEXT,
		agent_mode TEXT NOT NULL DEFAULT 'eino_single',
		schedule_mode TEXT NOT NULL DEFAULT 'manual',
		cron_expr TEXT,
		next_run_at DATETIME,
		schedule_enabled INTEGER NOT NULL DEFAULT 1,
		last_schedule_trigger_at DATETIME,
		last_schedule_error TEXT,
		last_run_error TEXT,
		project_id TEXT,
		concurrency INTEGER NOT NULL DEFAULT 1,
		status TEXT NOT NULL,
		created_at DATETIME NOT NULL,
		started_at DATETIME,
		completed_at DATETIME,
		current_index INTEGER NOT NULL DEFAULT 0
	);`

	// 创建批量任务表
	createBatchTasksTable := `
	CREATE TABLE IF NOT EXISTS batch_tasks (
		id TEXT PRIMARY KEY,
		queue_id TEXT NOT NULL,
		message TEXT NOT NULL,
		conversation_id TEXT,
		status TEXT NOT NULL,
		started_at DATETIME,
		completed_at DATETIME,
		error TEXT,
		result TEXT,
		FOREIGN KEY (queue_id) REFERENCES batch_task_queues(id) ON DELETE CASCADE
	);`

	// 创建 WebShell 连接表
	createWebshellConnectionsTable := `
	CREATE TABLE IF NOT EXISTS webshell_connections (
		id TEXT PRIMARY KEY,
		project_id TEXT,
		url TEXT NOT NULL,
		password TEXT NOT NULL DEFAULT '',
		type TEXT NOT NULL DEFAULT 'php',
		method TEXT NOT NULL DEFAULT 'post',
		cmd_param TEXT NOT NULL DEFAULT '',
		remark TEXT NOT NULL DEFAULT '',
		encoding TEXT NOT NULL DEFAULT '',
		os TEXT NOT NULL DEFAULT '',
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
	);`

	// 创建 WebShell 连接扩展状态表（前端工作区/终端状态持久化）
	createWebshellConnectionStatesTable := `
	CREATE TABLE IF NOT EXISTS webshell_connection_states (
		connection_id TEXT PRIMARY KEY,
		state_json TEXT NOT NULL DEFAULT '{}',
		updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (connection_id) REFERENCES webshell_connections(id) ON DELETE CASCADE
	);`

	// ========================================================================
	// C2 模块（监听器 / 会话 / 任务 / 文件 / 事件 / Malleable Profile）
	// ========================================================================
	createC2ListenersTable := `
	CREATE TABLE IF NOT EXISTS c2_listeners (
		id TEXT PRIMARY KEY,
		project_id TEXT,
		name TEXT NOT NULL,
		type TEXT NOT NULL,
		bind_host TEXT NOT NULL DEFAULT '127.0.0.1',
		bind_port INTEGER NOT NULL,
		profile_id TEXT,
		encryption_key TEXT NOT NULL DEFAULT '',
		implant_token TEXT NOT NULL DEFAULT '',
		status TEXT NOT NULL DEFAULT 'stopped',
		config_json TEXT NOT NULL DEFAULT '{}',
		remark TEXT NOT NULL DEFAULT '',
		owner_user_id TEXT,
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		started_at DATETIME,
		last_error TEXT
	);`

	createC2SessionsTable := `
	CREATE TABLE IF NOT EXISTS c2_sessions (
		id TEXT PRIMARY KEY,
		listener_id TEXT NOT NULL,
		implant_uuid TEXT NOT NULL UNIQUE,
		hostname TEXT,
		username TEXT,
		os TEXT,
		arch TEXT,
		pid INTEGER DEFAULT 0,
		process_name TEXT,
		is_admin INTEGER DEFAULT 0,
		internal_ip TEXT,
		external_ip TEXT,
		user_agent TEXT,
		sleep_seconds INTEGER NOT NULL DEFAULT 5,
		jitter_percent INTEGER NOT NULL DEFAULT 0,
		status TEXT NOT NULL DEFAULT 'active',
		first_seen_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		last_check_in DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		metadata_json TEXT DEFAULT '{}',
		note TEXT NOT NULL DEFAULT '',
		FOREIGN KEY (listener_id) REFERENCES c2_listeners(id) ON DELETE CASCADE
	);`

	createC2TasksTable := `
	CREATE TABLE IF NOT EXISTS c2_tasks (
		id TEXT PRIMARY KEY,
		session_id TEXT NOT NULL,
		task_type TEXT NOT NULL,
		payload_json TEXT NOT NULL DEFAULT '{}',
		status TEXT NOT NULL DEFAULT 'queued',
		result_text TEXT,
		result_blob_path TEXT,
		error TEXT,
		source TEXT NOT NULL DEFAULT 'manual',
		conversation_id TEXT,
		approval_status TEXT,
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		sent_at DATETIME,
		started_at DATETIME,
		completed_at DATETIME,
		duration_ms INTEGER DEFAULT 0,
		FOREIGN KEY (session_id) REFERENCES c2_sessions(id) ON DELETE CASCADE
	);`

	createC2FilesTable := `
	CREATE TABLE IF NOT EXISTS c2_files (
		id TEXT PRIMARY KEY,
		session_id TEXT NOT NULL,
		task_id TEXT,
		direction TEXT NOT NULL,
		remote_path TEXT NOT NULL,
		local_path TEXT NOT NULL,
		size_bytes INTEGER DEFAULT 0,
		sha256 TEXT,
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (session_id) REFERENCES c2_sessions(id) ON DELETE CASCADE
	);`

	createC2EventsTable := `
	CREATE TABLE IF NOT EXISTS c2_events (
		id TEXT PRIMARY KEY,
		level TEXT NOT NULL DEFAULT 'info',
		category TEXT NOT NULL,
		session_id TEXT,
		task_id TEXT,
		message TEXT NOT NULL,
		data_json TEXT,
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
	);`

	createAuditLogsTable := `
	CREATE TABLE IF NOT EXISTS audit_logs (
		id TEXT PRIMARY KEY,
		created_at DATETIME NOT NULL,
		level TEXT NOT NULL DEFAULT 'info',
		category TEXT NOT NULL,
		action TEXT NOT NULL,
		result TEXT NOT NULL,
		actor TEXT NOT NULL DEFAULT 'admin',
		session_hint TEXT,
		client_ip TEXT,
		user_agent TEXT,
		resource_type TEXT,
		resource_id TEXT,
		message TEXT NOT NULL,
		detail_json TEXT
	);`

	createC2ProfilesTable := `
	CREATE TABLE IF NOT EXISTS c2_profiles (
		id TEXT PRIMARY KEY,
		name TEXT NOT NULL UNIQUE,
		user_agent TEXT,
		uris_json TEXT NOT NULL DEFAULT '[]',
		request_headers_json TEXT,
		response_headers_json TEXT,
		body_template TEXT,
		jitter_min_ms INTEGER DEFAULT 0,
		jitter_max_ms INTEGER DEFAULT 0,
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
)`

	createXssPayloadsTable := `CREATE TABLE IF NOT EXISTS xss_payloads (
		id            INTEGER PRIMARY KEY AUTOINCREMENT,
		token         TEXT NOT NULL UNIQUE,
		name          TEXT,
		type          TEXT DEFAULT 'image',
		payload       TEXT NOT NULL,
		config        TEXT,
		project_id    TEXT,
		enabled       INTEGER DEFAULT 1,
		description   TEXT,
		domain        TEXT,
		domain_only   INTEGER DEFAULT 0,
		dns_exfil_domain TEXT,
		script        TEXT DEFAULT '',
		one_time     INTEGER NOT NULL DEFAULT 0,
		expires_at   DATETIME,
		consumed_at  DATETIME,
		created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
		updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
		created_by    TEXT,
		owner_user_id TEXT
	)`

	createXssCapturesTable := `CREATE TABLE IF NOT EXISTS xss_captures (
		id            INTEGER PRIMARY KEY AUTOINCREMENT,
		payload_id    INTEGER NOT NULL REFERENCES xss_payloads(id) ON DELETE CASCADE,
		token         TEXT NOT NULL,
		cookie        TEXT NOT NULL,
		url           TEXT,
		domain        TEXT,
		user_agent    TEXT,
		ip            TEXT,
		extra         TEXT,
		created_at    DATETIME DEFAULT CURRENT_TIMESTAMP
	)`

	createXssConfigTable := `CREATE TABLE IF NOT EXISTS xss_config (
		config_key    TEXT PRIMARY KEY,
		config_value  TEXT,
		updated_at    DATETIME DEFAULT CURRENT_TIMESTAMP
	)`

	createWorkflowDefinitionsTable := `
	CREATE TABLE IF NOT EXISTS workflow_definitions (
		id TEXT PRIMARY KEY,
		name TEXT NOT NULL,
		description TEXT,
		version INTEGER NOT NULL DEFAULT 1,
		graph_json TEXT NOT NULL,
		enabled INTEGER NOT NULL DEFAULT 1,
		created_at DATETIME NOT NULL,
		updated_at DATETIME NOT NULL
	);`

	createWorkflowRunsTable := `
	CREATE TABLE IF NOT EXISTS workflow_runs (
		id TEXT PRIMARY KEY,
		workflow_id TEXT NOT NULL,
		workflow_version INTEGER NOT NULL DEFAULT 1,
		conversation_id TEXT,
		project_id TEXT,
		role_id TEXT,
		status TEXT NOT NULL,
		input_json TEXT,
		output_json TEXT,
		error TEXT,
		pending_hitl_node_id TEXT,
		pending_hitl_json TEXT,
		started_at DATETIME NOT NULL,
		finished_at DATETIME,
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
	);`

	createWorkflowNodeRunsTable := `
	CREATE TABLE IF NOT EXISTS workflow_node_runs (
		id TEXT PRIMARY KEY,
		run_id TEXT NOT NULL,
		node_id TEXT NOT NULL,
		status TEXT NOT NULL,
		input_json TEXT,
		output_json TEXT,
		error TEXT,
		started_at DATETIME NOT NULL,
		finished_at DATETIME,
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		FOREIGN KEY (run_id) REFERENCES workflow_runs(id) ON DELETE CASCADE
	);`

	createWorkflowPackageInspectionsTable := `
	CREATE TABLE IF NOT EXISTS workflow_package_inspections (
		id TEXT PRIMARY KEY, package_hash TEXT NOT NULL, manifest_json TEXT NOT NULL,
		workflow_payload_json TEXT NOT NULL, inspection_json TEXT NOT NULL,
		source_workflow_id TEXT NOT NULL, source_revision INTEGER NOT NULL,
		source_content_hash TEXT NOT NULL, source_graph_hash TEXT NOT NULL,
		local_conflict_state TEXT NOT NULL CHECK (local_conflict_state IN ('none','identical','id_conflict')),
		local_workflow_id TEXT, local_content_hash TEXT, local_graph_hash TEXT,
		created_by TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'ready' CHECK (status IN ('ready','consumed','expired')),
		created_at DATETIME NOT NULL, expires_at DATETIME NOT NULL, consumed_at DATETIME
	);`
	createWorkflowPackageImportsTable := `
	CREATE TABLE IF NOT EXISTS workflow_package_imports (
		id TEXT PRIMARY KEY, inspection_id TEXT NOT NULL, request_hash TEXT NOT NULL,
		idempotency_key TEXT NOT NULL, actor_user_id TEXT NOT NULL,
		action TEXT NOT NULL CHECK (action IN ('create','keep_existing','overwrite','rename')),
		source_workflow_id TEXT NOT NULL, target_workflow_id TEXT NOT NULL, resulting_workflow_id TEXT,
		result TEXT NOT NULL CHECK (result IN ('created','overwritten','renamed','kept_existing','skipped_identical','failed')),
		error_code TEXT, error_message TEXT, created_at DATETIME NOT NULL, applied_at DATETIME,
		FOREIGN KEY (inspection_id) REFERENCES workflow_package_inspections(id)
	);`

	// 创建索引
	createIndexes := `
	CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);
	CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at);
	CREATE INDEX IF NOT EXISTS idx_process_details_message_id ON process_details(message_id);
	CREATE INDEX IF NOT EXISTS idx_process_details_conversation_id ON process_details(conversation_id);
	CREATE INDEX IF NOT EXISTS idx_model_token_usage_created_at ON model_token_usage(created_at);
	CREATE INDEX IF NOT EXISTS idx_model_token_usage_conversation ON model_token_usage(conversation_id);
	CREATE INDEX IF NOT EXISTS idx_model_token_usage_project ON model_token_usage(project_id);
	CREATE INDEX IF NOT EXISTS idx_model_token_usage_model ON model_token_usage(model);
	CREATE INDEX IF NOT EXISTS idx_tool_executions_tool_name ON tool_executions(tool_name);
	CREATE INDEX IF NOT EXISTS idx_tool_executions_start_time ON tool_executions(start_time);
	CREATE INDEX IF NOT EXISTS idx_tool_executions_status ON tool_executions(status);
	CREATE INDEX IF NOT EXISTS idx_chain_nodes_conversation ON attack_chain_nodes(conversation_id);
	CREATE INDEX IF NOT EXISTS idx_chain_edges_conversation ON attack_chain_edges(conversation_id);
	CREATE INDEX IF NOT EXISTS idx_chain_edges_source ON attack_chain_edges(source_node_id);
	CREATE INDEX IF NOT EXISTS idx_chain_edges_target ON attack_chain_edges(target_node_id);
	CREATE INDEX IF NOT EXISTS idx_knowledge_retrieval_logs_conversation ON knowledge_retrieval_logs(conversation_id);
	CREATE INDEX IF NOT EXISTS idx_knowledge_retrieval_logs_message ON knowledge_retrieval_logs(message_id);
	CREATE INDEX IF NOT EXISTS idx_knowledge_retrieval_logs_created_at ON knowledge_retrieval_logs(created_at);
	CREATE INDEX IF NOT EXISTS idx_robot_user_sessions_updated_at ON robot_user_sessions(updated_at);
	CREATE INDEX IF NOT EXISTS idx_conversations_pinned ON conversations(pinned);
	CREATE INDEX IF NOT EXISTS idx_vulnerabilities_conversation_id ON vulnerabilities(conversation_id);
	CREATE INDEX IF NOT EXISTS idx_vulnerabilities_conversation_tag ON vulnerabilities(conversation_tag);
	CREATE INDEX IF NOT EXISTS idx_vulnerabilities_task_tag ON vulnerabilities(task_tag);
	CREATE INDEX IF NOT EXISTS idx_vulnerabilities_severity ON vulnerabilities(severity);
	CREATE INDEX IF NOT EXISTS idx_vulnerabilities_status ON vulnerabilities(status);
	CREATE INDEX IF NOT EXISTS idx_vulnerabilities_project_status ON vulnerabilities(project_id, status);
	CREATE INDEX IF NOT EXISTS idx_vulnerabilities_conversation_status ON vulnerabilities(conversation_id, status);
	CREATE INDEX IF NOT EXISTS idx_vulnerabilities_created_at ON vulnerabilities(created_at);
	CREATE INDEX IF NOT EXISTS idx_assets_last_seen ON assets(last_seen_at);
	CREATE INDEX IF NOT EXISTS idx_assets_last_scan ON assets(last_scan_at);
	CREATE INDEX IF NOT EXISTS idx_assets_ip ON assets(ip);
	CREATE INDEX IF NOT EXISTS idx_assets_domain ON assets(domain);
	CREATE INDEX IF NOT EXISTS idx_assets_status ON assets(status);
	CREATE INDEX IF NOT EXISTS idx_assets_owner ON assets(owner_user_id);
	CREATE INDEX IF NOT EXISTS idx_assets_project ON assets(project_id);
	CREATE INDEX IF NOT EXISTS idx_assets_vulnerability_count ON assets(vulnerability_count);
	CREATE INDEX IF NOT EXISTS idx_assets_risk_score ON assets(risk_score);
	CREATE INDEX IF NOT EXISTS idx_assets_risk_level ON assets(risk_level);
	CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
	CREATE INDEX IF NOT EXISTS idx_projects_updated_at ON projects(updated_at);
	CREATE INDEX IF NOT EXISTS idx_project_facts_project_id ON project_facts(project_id);
	CREATE INDEX IF NOT EXISTS idx_project_facts_confidence ON project_facts(confidence);
	CREATE INDEX IF NOT EXISTS idx_project_facts_related_vuln ON project_facts(related_vulnerability_id);
	CREATE INDEX IF NOT EXISTS idx_project_fact_edges_project ON project_fact_edges(project_id);
	CREATE INDEX IF NOT EXISTS idx_project_fact_edges_source ON project_fact_edges(project_id, source_fact_key);
	CREATE INDEX IF NOT EXISTS idx_project_fact_edges_target ON project_fact_edges(project_id, target_fact_key);
	CREATE INDEX IF NOT EXISTS idx_conversations_project_id ON conversations(project_id);
	CREATE INDEX IF NOT EXISTS idx_vulnerabilities_project_id ON vulnerabilities(project_id);
	CREATE INDEX IF NOT EXISTS idx_batch_tasks_queue_id ON batch_tasks(queue_id);
	CREATE INDEX IF NOT EXISTS idx_batch_task_queues_created_at ON batch_task_queues(created_at);
	CREATE INDEX IF NOT EXISTS idx_batch_task_queues_title ON batch_task_queues(title);
	CREATE INDEX IF NOT EXISTS idx_webshell_connections_created_at ON webshell_connections(created_at);
	CREATE INDEX IF NOT EXISTS idx_webshell_connections_project_id ON webshell_connections(project_id);
	CREATE INDEX IF NOT EXISTS idx_webshell_connection_states_updated_at ON webshell_connection_states(updated_at);
	CREATE INDEX IF NOT EXISTS idx_c2_listeners_created_at ON c2_listeners(created_at);
	CREATE INDEX IF NOT EXISTS idx_c2_listeners_project_id ON c2_listeners(project_id);
	CREATE INDEX IF NOT EXISTS idx_c2_listeners_status ON c2_listeners(status);
	CREATE INDEX IF NOT EXISTS idx_c2_sessions_listener ON c2_sessions(listener_id);
	CREATE INDEX IF NOT EXISTS idx_c2_sessions_status ON c2_sessions(status);
	CREATE INDEX IF NOT EXISTS idx_c2_sessions_last_check_in ON c2_sessions(last_check_in);
	CREATE INDEX IF NOT EXISTS idx_c2_tasks_session ON c2_tasks(session_id);
	CREATE INDEX IF NOT EXISTS idx_c2_tasks_status ON c2_tasks(status);
	CREATE INDEX IF NOT EXISTS idx_c2_tasks_created_at ON c2_tasks(created_at);
	CREATE INDEX IF NOT EXISTS idx_c2_tasks_conversation ON c2_tasks(conversation_id);
	CREATE INDEX IF NOT EXISTS idx_c2_files_session ON c2_files(session_id);
	CREATE INDEX IF NOT EXISTS idx_c2_events_created_at ON c2_events(created_at);
	CREATE INDEX IF NOT EXISTS idx_c2_events_category ON c2_events(category);
	CREATE INDEX IF NOT EXISTS idx_c2_events_session ON c2_events(session_id);
	CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
	CREATE INDEX IF NOT EXISTS idx_audit_logs_category ON audit_logs(category);
	CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs(action);
	CREATE INDEX IF NOT EXISTS idx_audit_logs_result ON audit_logs(result);
	CREATE INDEX IF NOT EXISTS idx_workflow_definitions_updated_at ON workflow_definitions(updated_at);
	CREATE INDEX IF NOT EXISTS idx_workflow_definitions_enabled ON workflow_definitions(enabled);
	CREATE INDEX IF NOT EXISTS idx_workflow_runs_workflow ON workflow_runs(workflow_id);
	CREATE INDEX IF NOT EXISTS idx_workflow_runs_conversation ON workflow_runs(conversation_id);
	CREATE INDEX IF NOT EXISTS idx_workflow_runs_status ON workflow_runs(status);
	CREATE INDEX IF NOT EXISTS idx_workflow_node_runs_run ON workflow_node_runs(run_id);
	CREATE INDEX IF NOT EXISTS idx_workflow_package_inspections_creator_expiry ON workflow_package_inspections(created_by, expires_at);
	CREATE UNIQUE INDEX IF NOT EXISTS uq_workflow_package_imports_actor_key ON workflow_package_imports(actor_user_id, idempotency_key);
	CREATE UNIQUE INDEX IF NOT EXISTS uq_workflow_package_imports_inspection_success ON workflow_package_imports(inspection_id) WHERE result IN ('created','overwritten','renamed','kept_existing','skipped_identical');
	CREATE INDEX IF NOT EXISTS idx_xss_payloads_token ON xss_payloads(token);
	CREATE INDEX IF NOT EXISTS idx_xss_captures_payload_id ON xss_captures(payload_id);
	CREATE INDEX IF NOT EXISTS idx_xss_captures_created_at ON xss_captures(created_at);
	CREATE INDEX IF NOT EXISTS idx_xss_captures_token ON xss_captures(token);
	`

	if _, err := db.Exec(createConversationsTable); err != nil {
		return fmt.Errorf("创建conversations表失败: %w", err)
	}

	if _, err := db.Exec(createMessagesTable); err != nil {
		return fmt.Errorf("创建messages表失败: %w", err)
	}

	if _, err := db.Exec(createProcessDetailsTable); err != nil {
		return fmt.Errorf("创建process_details表失败: %w", err)
	}

	if _, err := db.Exec(createModelTokenUsageTable); err != nil {
		return fmt.Errorf("创建model_token_usage表失败: %w", err)
	}

	if _, err := db.Exec(createToolExecutionsTable); err != nil {
		return fmt.Errorf("创建tool_executions表失败: %w", err)
	}

	if _, err := db.Exec(createToolStatsTable); err != nil {
		return fmt.Errorf("创建tool_stats表失败: %w", err)
	}

	if _, err := db.Exec(createSkillStatsTable); err != nil {
		return fmt.Errorf("创建skill_stats表失败: %w", err)
	}

	if _, err := db.Exec(createAttackChainNodesTable); err != nil {
		return fmt.Errorf("创建attack_chain_nodes表失败: %w", err)
	}

	if _, err := db.Exec(createAttackChainEdgesTable); err != nil {
		return fmt.Errorf("创建attack_chain_edges表失败: %w", err)
	}

	if _, err := db.Exec(createKnowledgeRetrievalLogsTable); err != nil {
		return fmt.Errorf("创建knowledge_retrieval_logs表失败: %w", err)
	}

	if _, err := db.Exec(createRobotUserSessionsTable); err != nil {
		return fmt.Errorf("创建robot_user_sessions表失败: %w", err)
	}
	if err := db.migrateRobotUserSessionsTable(); err != nil {
		return fmt.Errorf("迁移robot_user_sessions表失败: %w", err)
	}

	if _, err := db.Exec(createProjectsTable); err != nil {
		return fmt.Errorf("创建projects表失败: %w", err)
	}

	if _, err := db.Exec(createProjectFactsTable); err != nil {
		return fmt.Errorf("创建project_facts表失败: %w", err)
	}

	if _, err := db.Exec(createProjectFactEdgesTable); err != nil {
		return fmt.Errorf("创建project_fact_edges表失败: %w", err)
	}

	if _, err := db.Exec(createVulnerabilitiesTable); err != nil {
		return fmt.Errorf("创建vulnerabilities表失败: %w", err)
	}
	if _, err := db.Exec(createVulnerabilityTriageRunsTable); err != nil {
		return fmt.Errorf("创建vulnerability_triage_runs表失败: %w", err)
	}
	if _, err := db.Exec(createAssetsTable); err != nil {
		return fmt.Errorf("创建assets表失败: %w", err)
	}
	if err := db.migrateAssetsTable(); err != nil {
		return fmt.Errorf("迁移assets表失败: %w", err)
	}

	if _, err := db.Exec(createBatchTaskQueuesTable); err != nil {
		return fmt.Errorf("创建batch_task_queues表失败: %w", err)
	}

	if _, err := db.Exec(createBatchTasksTable); err != nil {
		return fmt.Errorf("创建batch_tasks表失败: %w", err)
	}

	if _, err := db.Exec(createWebshellConnectionsTable); err != nil {
		return fmt.Errorf("创建webshell_connections表失败: %w", err)
	}

	if _, err := db.Exec(createWebshellConnectionStatesTable); err != nil {
		return fmt.Errorf("创建webshell_connection_states表失败: %w", err)
	}

	if _, err := db.Exec(createAuditLogsTable); err != nil {
		return fmt.Errorf("创建audit_logs表失败: %w", err)
	}

	if err := db.initRBACTables(); err != nil {
		return fmt.Errorf("创建RBAC表失败: %w", err)
	}
	if _, err := db.Exec(createVulnerabilityAlertSubscriptionsTable); err != nil {
		return fmt.Errorf("创建漏洞提醒订阅表失败: %w", err)
	}
	if _, err := db.Exec(createVulnerabilityAlertDeliveriesTable); err != nil {
		return fmt.Errorf("创建漏洞提醒投递表失败: %w", err)
	}

	for tableName, ddl := range map[string]string{
		"workflow_definitions":         createWorkflowDefinitionsTable,
		"workflow_runs":                createWorkflowRunsTable,
		"workflow_node_runs":           createWorkflowNodeRunsTable,
		"workflow_package_inspections": createWorkflowPackageInspectionsTable,
		"workflow_package_imports":     createWorkflowPackageImportsTable,
	} {
		if _, err := db.Exec(ddl); err != nil {
			return fmt.Errorf("创建%s表失败: %w", tableName, err)
		}
	}

	for tableName, ddl := range map[string]string{
		"c2_listeners": createC2ListenersTable,
		"c2_sessions":  createC2SessionsTable,
		"c2_tasks":     createC2TasksTable,
		"c2_files":     createC2FilesTable,
		"c2_events":    createC2EventsTable,
		"c2_profiles":  createC2ProfilesTable,
		"xss_payloads": createXssPayloadsTable,
		"xss_captures": createXssCapturesTable,
		"xss_config":   createXssConfigTable,
	} {
		if _, err := db.Exec(ddl); err != nil {
			return fmt.Errorf("创建%s表失败: %w", tableName, err)
		}
	}

	if _, err := db.Exec(createSecurityOpsRunsTable); err != nil {
		return fmt.Errorf("创建security_ops_runs表失败: %w", err)
	}

	// 为已有表添加新字段（如果不存在）- 必须在创建索引之前
	if err := db.migrateConversationsTable(); err != nil {
		db.logger.Warn("迁移conversations表失败", zap.Error(err))
		// 不返回错误，允许继续运行
	}

	if err := db.migrateMessagesTable(); err != nil {
		db.logger.Warn("迁移messages表失败", zap.Error(err))
		// 不返回错误，允许继续运行
	}

	if err := db.migrateBatchTaskQueuesTable(); err != nil {
		db.logger.Warn("迁移batch_task_queues表失败", zap.Error(err))
		// 不返回错误，允许继续运行
	}
	if err := db.migrateVulnerabilitiesTable(); err != nil {
		db.logger.Warn("迁移vulnerabilities表失败", zap.Error(err))
		// 不返回错误，允许继续运行
	}
	if err := db.migrateVulnerabilitiesConversationFK(); err != nil {
		db.logger.Warn("迁移vulnerabilities会话外键失败", zap.Error(err))
	}

	if err := db.migrateProjectsTable(); err != nil {
		db.logger.Warn("迁移projects相关表失败", zap.Error(err))
	}
	if err := db.dropProjectFactVersionsTable(); err != nil {
		db.logger.Warn("清理project_fact_versions表失败", zap.Error(err))
	}

	if err := db.migrateWebshellConnectionsTable(); err != nil {
		db.logger.Warn("迁移webshell_connections表失败", zap.Error(err))
		// 不返回错误，允许继续运行
	}
	if err := db.migrateC2ListenersTable(); err != nil {
		db.logger.Warn("迁移c2_listeners表失败", zap.Error(err))
	}
	if err := db.migrateXssPayloadsTable(); err != nil {
		return fmt.Errorf("迁移 xss_payloads 表失败: %w", err)
	}
	if err := db.migrateXssCapturesTable(); err != nil {
		return fmt.Errorf("迁移 xss_captures 表失败: %w", err)
	}
	if err := db.migrateWorkflowRunsTable(); err != nil {
		db.logger.Warn("迁移workflow_runs表失败", zap.Error(err))
	}
	if err := db.migrateToolExecutionsPartialOutputColumns(); err != nil {
		db.logger.Warn("迁移tool_executions partial output字段失败", zap.Error(err))
	}
	if err := db.migrateRBACOwnershipColumns(); err != nil {
		db.logger.Warn("迁移RBAC资源归属字段失败", zap.Error(err))
	}

	if _, err := db.Exec(createIndexes); err != nil {
		return fmt.Errorf("创建索引失败: %w", err)
	}

	if err := db.BackfillModelTokenUsageFromProcessDetails(); err != nil {
		return fmt.Errorf("回填模型Token用量失败: %w", err)
	}
	db.logger.Debug("数据库表初始化完成")
	return nil
}

func (db *DB) migrateRobotUserSessionsTable() error {
	var count int
	if err := db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('robot_user_sessions') WHERE name='agent_mode'").Scan(&count); err != nil {
		return err
	}
	if count == 0 {
		_, err := db.Exec("ALTER TABLE robot_user_sessions ADD COLUMN agent_mode TEXT NOT NULL DEFAULT 'eino_single'")
		return err
	}
	return nil
}

func (db *DB) migrateToolExecutionsPartialOutputColumns() error {
	for _, col := range []struct {
		name string
		stmt string
	}{
		{"partial_output", "ALTER TABLE tool_executions ADD COLUMN partial_output TEXT"},
		{"partial_output_bytes", "ALTER TABLE tool_executions ADD COLUMN partial_output_bytes INTEGER NOT NULL DEFAULT 0"},
		{"partial_output_truncated", "ALTER TABLE tool_executions ADD COLUMN partial_output_truncated INTEGER NOT NULL DEFAULT 0"},
		{"partial_output_updated_at", "ALTER TABLE tool_executions ADD COLUMN partial_output_updated_at DATETIME"},
	} {
		if err := db.addColumnIfMissing("tool_executions", col.name, col.stmt); err != nil {
			return err
		}
	}
	return nil
}

// migrateAssetsTable keeps databases created by the first asset-management release compatible.
func (db *DB) migrateAssetsTable() error {
	columns := []struct {
		name string
		ddl  string
	}{
		{"project_id", "ALTER TABLE assets ADD COLUMN project_id TEXT"},
		{"last_scan_at", "ALTER TABLE assets ADD COLUMN last_scan_at DATETIME"},
		{"last_scan_conversation_id", "ALTER TABLE assets ADD COLUMN last_scan_conversation_id TEXT NOT NULL DEFAULT ''"},
		{"last_scan_queue_id", "ALTER TABLE assets ADD COLUMN last_scan_queue_id TEXT NOT NULL DEFAULT ''"},
		{"last_scan_task_id", "ALTER TABLE assets ADD COLUMN last_scan_task_id TEXT NOT NULL DEFAULT ''"},
		{"responsible_person", "ALTER TABLE assets ADD COLUMN responsible_person TEXT NOT NULL DEFAULT ''"},
		{"department", "ALTER TABLE assets ADD COLUMN department TEXT NOT NULL DEFAULT ''"},
		{"business_system", "ALTER TABLE assets ADD COLUMN business_system TEXT NOT NULL DEFAULT ''"},
		{"environment", "ALTER TABLE assets ADD COLUMN environment TEXT NOT NULL DEFAULT ''"},
		{"criticality", "ALTER TABLE assets ADD COLUMN criticality TEXT NOT NULL DEFAULT ''"},
		{"vulnerability_count", "ALTER TABLE assets ADD COLUMN vulnerability_count INTEGER NOT NULL DEFAULT 0"},
		{"risk_score", "ALTER TABLE assets ADD COLUMN risk_score INTEGER NOT NULL DEFAULT 0"},
		{"risk_level", "ALTER TABLE assets ADD COLUMN risk_level TEXT NOT NULL DEFAULT 'unassessed'"},
	}
	for _, column := range columns {
		var count int
		if err := db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('assets') WHERE name=?", column.name).Scan(&count); err != nil {
			return err
		}
		if count == 0 {
			if _, err := db.Exec(column.ddl); err != nil {
				return err
			}
		}
	}
	return nil
}

// migrateMessagesTable 迁移 messages 表，补充 updated_at 字段。
// 语义：updated_at 表示该条消息最后一次被写入/更新的时间（例如助手占位消息在任务结束时更新正文）。
func (db *DB) migrateMessagesTable() error {
	var count int
	err := db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('messages') WHERE name='updated_at'").Scan(&count)
	if err != nil {
		// 如果查询失败，尝试添加字段
		if _, addErr := db.Exec("ALTER TABLE messages ADD COLUMN updated_at DATETIME"); addErr != nil {
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				return fmt.Errorf("添加 messages.updated_at 字段失败: %w", addErr)
			}
		}
	} else if count == 0 {
		if _, err := db.Exec("ALTER TABLE messages ADD COLUMN updated_at DATETIME"); err != nil {
			errMsg := strings.ToLower(err.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				return fmt.Errorf("添加 messages.updated_at 字段失败: %w", err)
			}
		}
	}

	// 回填已有数据：让 updated_at 至少等于 created_at，避免前端出现空/当前时间回退。
	_, _ = db.Exec("UPDATE messages SET updated_at = created_at WHERE updated_at IS NULL OR updated_at = ''")

	// reasoning_content：DeepSeek 思考模式 + 工具调用续跑；与 last_react_input 互补，供消息表回退路径回放
	var rcColCount int
	errRC := db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('messages') WHERE name='reasoning_content'").Scan(&rcColCount)
	if errRC != nil {
		if _, addErr := db.Exec("ALTER TABLE messages ADD COLUMN reasoning_content TEXT"); addErr != nil {
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				return fmt.Errorf("添加 messages.reasoning_content 字段失败: %w", addErr)
			}
		}
	} else if rcColCount == 0 {
		if _, err := db.Exec("ALTER TABLE messages ADD COLUMN reasoning_content TEXT"); err != nil {
			errMsg := strings.ToLower(err.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				return fmt.Errorf("添加 messages.reasoning_content 字段失败: %w", err)
			}
		}
	}
	return nil
}

// migrateConversationsTable 迁移conversations表，添加新字段
func (db *DB) migrateConversationsTable() error {
	// 检查last_react_input字段是否存在
	var count int
	err := db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('conversations') WHERE name='last_react_input'").Scan(&count)
	if err != nil {
		// 如果查询失败，尝试添加字段
		if _, addErr := db.Exec("ALTER TABLE conversations ADD COLUMN last_react_input TEXT"); addErr != nil {
			// 如果字段已存在，忽略错误（SQLite错误信息可能不同）
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加last_react_input字段失败", zap.Error(addErr))
			}
		}
	} else if count == 0 {
		// 字段不存在，添加它
		if _, err := db.Exec("ALTER TABLE conversations ADD COLUMN last_react_input TEXT"); err != nil {
			db.logger.Warn("添加last_react_input字段失败", zap.Error(err))
		}
	}

	// 检查last_react_output字段是否存在
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('conversations') WHERE name='last_react_output'").Scan(&count)
	if err != nil {
		// 如果查询失败，尝试添加字段
		if _, addErr := db.Exec("ALTER TABLE conversations ADD COLUMN last_react_output TEXT"); addErr != nil {
			// 如果字段已存在，忽略错误
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加last_react_output字段失败", zap.Error(addErr))
			}
		}
	} else if count == 0 {
		// 字段不存在，添加它
		if _, err := db.Exec("ALTER TABLE conversations ADD COLUMN last_react_output TEXT"); err != nil {
			db.logger.Warn("添加last_react_output字段失败", zap.Error(err))
		}
	}

	// 检查pinned字段是否存在
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('conversations') WHERE name='pinned'").Scan(&count)
	if err != nil {
		// 如果查询失败，尝试添加字段
		if _, addErr := db.Exec("ALTER TABLE conversations ADD COLUMN pinned INTEGER DEFAULT 0"); addErr != nil {
			// 如果字段已存在，忽略错误
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加pinned字段失败", zap.Error(addErr))
			}
		}
	} else if count == 0 {
		// 字段不存在，添加它
		if _, err := db.Exec("ALTER TABLE conversations ADD COLUMN pinned INTEGER DEFAULT 0"); err != nil {
			db.logger.Warn("添加pinned字段失败", zap.Error(err))
		}
	}

	// 检查 webshell_connection_id 字段是否存在（WebShell AI 助手对话关联）
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('conversations') WHERE name='webshell_connection_id'").Scan(&count)
	if err != nil {
		if _, addErr := db.Exec("ALTER TABLE conversations ADD COLUMN webshell_connection_id TEXT"); addErr != nil {
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加webshell_connection_id字段失败", zap.Error(addErr))
			}
		}
	} else if count == 0 {
		if _, err := db.Exec("ALTER TABLE conversations ADD COLUMN webshell_connection_id TEXT"); err != nil {
			db.logger.Warn("添加webshell_connection_id字段失败", zap.Error(err))
		}
	}

	// 检查 role_name 字段是否存在（对话绑定的业务角色，用于历史任务切换时恢复角色上下文）
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('conversations') WHERE name='role_name'").Scan(&count)
	if err != nil {
		if _, addErr := db.Exec("ALTER TABLE conversations ADD COLUMN role_name TEXT NOT NULL DEFAULT '默认'"); addErr != nil {
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加role_name字段失败", zap.Error(addErr))
			}
		}
	} else if count == 0 {
		if _, err := db.Exec("ALTER TABLE conversations ADD COLUMN role_name TEXT NOT NULL DEFAULT '默认'"); err != nil {
			db.logger.Warn("添加role_name字段失败", zap.Error(err))
		}
	}

	// 检查 agent_mode 字段是否存在（对话绑定的执行模式，用于历史任务切换时恢复对话模式）
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('conversations') WHERE name='agent_mode'").Scan(&count)
	if err != nil {
		if _, addErr := db.Exec("ALTER TABLE conversations ADD COLUMN agent_mode TEXT NOT NULL DEFAULT 'eino_single'"); addErr != nil {
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加agent_mode字段失败", zap.Error(addErr))
			}
		}
	} else if count == 0 {
		if _, err := db.Exec("ALTER TABLE conversations ADD COLUMN agent_mode TEXT NOT NULL DEFAULT 'eino_single'"); err != nil {
			db.logger.Warn("添加agent_mode字段失败", zap.Error(err))
		}
	}

	return nil
}

// migrateBatchTaskQueuesTable 迁移batch_task_queues表，补充新字段
func (db *DB) migrateBatchTaskQueuesTable() error {
	// 检查title字段是否存在
	var count int
	err := db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('batch_task_queues') WHERE name='title'").Scan(&count)
	if err != nil {
		// 如果查询失败，尝试添加字段
		if _, addErr := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN title TEXT"); addErr != nil {
			// 如果字段已存在，忽略错误
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加title字段失败", zap.Error(addErr))
			}
		}
	} else if count == 0 {
		// 字段不存在，添加它
		if _, err := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN title TEXT"); err != nil {
			db.logger.Warn("添加title字段失败", zap.Error(err))
		}
	}

	// 检查role字段是否存在
	var roleCount int
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('batch_task_queues') WHERE name='role'").Scan(&roleCount)
	if err != nil {
		// 如果查询失败，尝试添加字段
		if _, addErr := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN role TEXT"); addErr != nil {
			// 如果字段已存在，忽略错误
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加role字段失败", zap.Error(addErr))
			}
		}
	} else if roleCount == 0 {
		// 字段不存在，添加它
		if _, err := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN role TEXT"); err != nil {
			db.logger.Warn("添加role字段失败", zap.Error(err))
		}
	}

	// 检查agent_mode字段是否存在
	var agentModeCount int
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('batch_task_queues') WHERE name='agent_mode'").Scan(&agentModeCount)
	if err != nil {
		if _, addErr := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN agent_mode TEXT NOT NULL DEFAULT 'eino_single'"); addErr != nil {
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加agent_mode字段失败", zap.Error(addErr))
			}
		}
	} else if agentModeCount == 0 {
		if _, err := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN agent_mode TEXT NOT NULL DEFAULT 'eino_single'"); err != nil {
			db.logger.Warn("添加agent_mode字段失败", zap.Error(err))
		}
	}

	// 检查schedule_mode字段是否存在
	var scheduleModeCount int
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('batch_task_queues') WHERE name='schedule_mode'").Scan(&scheduleModeCount)
	if err != nil {
		if _, addErr := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN schedule_mode TEXT NOT NULL DEFAULT 'manual'"); addErr != nil {
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加schedule_mode字段失败", zap.Error(addErr))
			}
		}
	} else if scheduleModeCount == 0 {
		if _, err := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN schedule_mode TEXT NOT NULL DEFAULT 'manual'"); err != nil {
			db.logger.Warn("添加schedule_mode字段失败", zap.Error(err))
		}
	}

	// 检查cron_expr字段是否存在
	var cronExprCount int
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('batch_task_queues') WHERE name='cron_expr'").Scan(&cronExprCount)
	if err != nil {
		if _, addErr := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN cron_expr TEXT"); addErr != nil {
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加cron_expr字段失败", zap.Error(addErr))
			}
		}
	} else if cronExprCount == 0 {
		if _, err := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN cron_expr TEXT"); err != nil {
			db.logger.Warn("添加cron_expr字段失败", zap.Error(err))
		}
	}

	// 检查next_run_at字段是否存在
	var nextRunAtCount int
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('batch_task_queues') WHERE name='next_run_at'").Scan(&nextRunAtCount)
	if err != nil {
		if _, addErr := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN next_run_at DATETIME"); addErr != nil {
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加next_run_at字段失败", zap.Error(addErr))
			}
		}
	} else if nextRunAtCount == 0 {
		if _, err := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN next_run_at DATETIME"); err != nil {
			db.logger.Warn("添加next_run_at字段失败", zap.Error(err))
		}
	}

	// schedule_enabled：0=暂停 Cron 自动调度，1=允许（手工执行不受影响）
	var scheduleEnCount int
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('batch_task_queues') WHERE name='schedule_enabled'").Scan(&scheduleEnCount)
	if err != nil {
		if _, addErr := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN schedule_enabled INTEGER NOT NULL DEFAULT 1"); addErr != nil {
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加schedule_enabled字段失败", zap.Error(addErr))
			}
		}
	} else if scheduleEnCount == 0 {
		if _, err := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN schedule_enabled INTEGER NOT NULL DEFAULT 1"); err != nil {
			db.logger.Warn("添加schedule_enabled字段失败", zap.Error(err))
		}
	}

	var lastTrigCount int
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('batch_task_queues') WHERE name='last_schedule_trigger_at'").Scan(&lastTrigCount)
	if err != nil {
		if _, addErr := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN last_schedule_trigger_at DATETIME"); addErr != nil {
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加last_schedule_trigger_at字段失败", zap.Error(addErr))
			}
		}
	} else if lastTrigCount == 0 {
		if _, err := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN last_schedule_trigger_at DATETIME"); err != nil {
			db.logger.Warn("添加last_schedule_trigger_at字段失败", zap.Error(err))
		}
	}

	var lastSchedErrCount int
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('batch_task_queues') WHERE name='last_schedule_error'").Scan(&lastSchedErrCount)
	if err != nil {
		if _, addErr := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN last_schedule_error TEXT"); addErr != nil {
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加last_schedule_error字段失败", zap.Error(addErr))
			}
		}
	} else if lastSchedErrCount == 0 {
		if _, err := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN last_schedule_error TEXT"); err != nil {
			db.logger.Warn("添加last_schedule_error字段失败", zap.Error(err))
		}
	}

	var lastRunErrCount int
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('batch_task_queues') WHERE name='last_run_error'").Scan(&lastRunErrCount)
	if err != nil {
		if _, addErr := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN last_run_error TEXT"); addErr != nil {
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加last_run_error字段失败", zap.Error(addErr))
			}
		}
	} else if lastRunErrCount == 0 {
		if _, err := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN last_run_error TEXT"); err != nil {
			db.logger.Warn("添加last_run_error字段失败", zap.Error(err))
		}
	}

	var projectIDCount int
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('batch_task_queues') WHERE name='project_id'").Scan(&projectIDCount)
	if err != nil {
		if _, addErr := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN project_id TEXT"); addErr != nil {
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加batch_task_queues.project_id字段失败", zap.Error(addErr))
			}
		}
	} else if projectIDCount == 0 {
		if _, err := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN project_id TEXT"); err != nil {
			db.logger.Warn("添加batch_task_queues.project_id字段失败", zap.Error(err))
		}
	}

	var concurrencyCount int
	err = db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('batch_task_queues') WHERE name='concurrency'").Scan(&concurrencyCount)
	if err != nil {
		if _, addErr := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN concurrency INTEGER NOT NULL DEFAULT 1"); addErr != nil {
			errMsg := strings.ToLower(addErr.Error())
			if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
				db.logger.Warn("添加batch_task_queues.concurrency字段失败", zap.Error(addErr))
			}
		}
	} else if concurrencyCount == 0 {
		if _, err := db.Exec("ALTER TABLE batch_task_queues ADD COLUMN concurrency INTEGER NOT NULL DEFAULT 1"); err != nil {
			db.logger.Warn("添加batch_task_queues.concurrency字段失败", zap.Error(err))
		}
	}

	return nil
}

// migrateProjectsTable 迁移 projects / conversations / vulnerabilities 的项目关联字段。
func (db *DB) migrateProjectsTable() error {
	for _, col := range []struct {
		table string
		name  string
		stmt  string
	}{
		{"conversations", "project_id", "ALTER TABLE conversations ADD COLUMN project_id TEXT REFERENCES projects(id) ON DELETE SET NULL"},
		{"vulnerabilities", "project_id", "ALTER TABLE vulnerabilities ADD COLUMN project_id TEXT"},
	} {
		var count int
		err := db.QueryRow("SELECT COUNT(*) FROM pragma_table_info(?) WHERE name=?", col.table, col.name).Scan(&count)
		if err != nil {
			if _, addErr := db.Exec(col.stmt); addErr != nil {
				errMsg := strings.ToLower(addErr.Error())
				if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
					db.logger.Warn("添加字段失败", zap.String("table", col.table), zap.String("field", col.name), zap.Error(addErr))
				}
			}
			continue
		}
		if count == 0 {
			if _, addErr := db.Exec(col.stmt); addErr != nil {
				db.logger.Warn("添加字段失败", zap.String("table", col.table), zap.String("field", col.name), zap.Error(addErr))
			}
		}
	}
	return nil
}

// dropProjectFactVersionsTable 移除已废弃的事实版本归档表。
func (db *DB) dropProjectFactVersionsTable() error {
	_, err := db.Exec(`DROP TABLE IF EXISTS project_fact_versions`)
	return err
}

// migrateVulnerabilitiesConversationFK 将 vulnerabilities.conversation_id 外键改为 ON DELETE SET NULL，删除对话时保留漏洞记录。
func (db *DB) migrateVulnerabilitiesConversationFK() error {
	ok, err := vulnerabilitiesConversationFKOnDeleteSetNull(db.DB)
	if err != nil {
		return err
	}
	if ok {
		return nil
	}

	tx, err := db.Begin()
	if err != nil {
		return fmt.Errorf("开启事务失败: %w", err)
	}
	defer func() { _ = tx.Rollback() }()

	const createNew = `
	CREATE TABLE vulnerabilities_new (
		id TEXT PRIMARY KEY,
		conversation_id TEXT,
		conversation_tag TEXT,
		task_tag TEXT,
		title TEXT NOT NULL,
		description TEXT,
		severity TEXT NOT NULL,
		status TEXT NOT NULL DEFAULT 'open',
		confidence INTEGER NOT NULL DEFAULT 0,
		vulnerability_type TEXT,
		target TEXT,
		preconditions TEXT,
		reproduction_steps TEXT,
		evidence TEXT,
		impact TEXT,
		recommendation TEXT,
		retest_notes TEXT,
		created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
		project_id TEXT,
		FOREIGN KEY (conversation_id) REFERENCES conversations(id) ON DELETE SET NULL
	);`
	if _, err := tx.Exec(createNew); err != nil {
		return fmt.Errorf("创建 vulnerabilities_new 失败: %w", err)
	}

	const copyRows = `
	INSERT INTO vulnerabilities_new (
		id, conversation_id, conversation_tag, task_tag, title, description,
		severity, status, vulnerability_type, target, preconditions, reproduction_steps,
		evidence, impact, recommendation, retest_notes,
		created_at, updated_at, project_id
	)
	SELECT
		id, conversation_id, conversation_tag, task_tag, title, description,
		severity, status, vulnerability_type, target,
		COALESCE(preconditions, ''), COALESCE(reproduction_steps, ''),
		COALESCE(evidence, ''), impact, recommendation, COALESCE(retest_notes, ''),
		created_at, updated_at, project_id
	FROM vulnerabilities;`
	if _, err := tx.Exec(copyRows); err != nil {
		return fmt.Errorf("复制 vulnerabilities 数据失败: %w", err)
	}

	// 這張表是整張重建的，所以後來新增的欄位必須在這裡一起搬過去 ——
	// 否則 migrateVulnerabilitiesTable 剛加的 confidence 會被無聲洗掉，
	// 表現成「遷移有跑過、欄位卻不存在」，而且只在舊資料庫上發生，新庫看不出來。
	// 來源表可能還沒有 confidence，用 pragma 決定要不要搬，兩種情況都安全。
	for _, name := range []string{"confidence"} {
		var count int
		if err := tx.QueryRow("SELECT COUNT(*) FROM pragma_table_info('vulnerabilities') WHERE name=?", name).Scan(&count); err != nil || count == 0 {
			continue
		}
		stmt := fmt.Sprintf(
			`UPDATE vulnerabilities_new SET %s = COALESCE((SELECT v.%s FROM vulnerabilities v WHERE v.id = vulnerabilities_new.id), 0)`,
			name, name,
		)
		if _, err := tx.Exec(stmt); err != nil {
			return fmt.Errorf("搬迁 vulnerabilities.%s 失败: %w", name, err)
		}
	}
	if _, err := tx.Exec(`DROP TABLE vulnerabilities`); err != nil {
		return fmt.Errorf("删除旧 vulnerabilities 表失败: %w", err)
	}
	if _, err := tx.Exec(`ALTER TABLE vulnerabilities_new RENAME TO vulnerabilities`); err != nil {
		return fmt.Errorf("重命名 vulnerabilities 表失败: %w", err)
	}

	indexes := []string{
		`CREATE INDEX IF NOT EXISTS idx_vulnerabilities_conversation_id ON vulnerabilities(conversation_id)`,
		`CREATE INDEX IF NOT EXISTS idx_vulnerabilities_conversation_tag ON vulnerabilities(conversation_tag)`,
		`CREATE INDEX IF NOT EXISTS idx_vulnerabilities_task_tag ON vulnerabilities(task_tag)`,
		`CREATE INDEX IF NOT EXISTS idx_vulnerabilities_severity ON vulnerabilities(severity)`,
		`CREATE INDEX IF NOT EXISTS idx_vulnerabilities_status ON vulnerabilities(status)`,
		`CREATE INDEX IF NOT EXISTS idx_vulnerabilities_project_status ON vulnerabilities(project_id, status)`,
		`CREATE INDEX IF NOT EXISTS idx_vulnerabilities_conversation_status ON vulnerabilities(conversation_id, status)`,
		`CREATE INDEX IF NOT EXISTS idx_vulnerabilities_created_at ON vulnerabilities(created_at)`,
		`CREATE INDEX IF NOT EXISTS idx_vulnerabilities_project_id ON vulnerabilities(project_id)`,
	}
	for _, stmt := range indexes {
		if _, err := tx.Exec(stmt); err != nil {
			return fmt.Errorf("重建 vulnerabilities 索引失败: %w", err)
		}
	}

	if err := tx.Commit(); err != nil {
		return fmt.Errorf("提交 vulnerabilities 外键迁移失败: %w", err)
	}
	db.logger.Info("vulnerabilities 表已迁移：删除对话时保留漏洞记录")
	return nil
}

func vulnerabilitiesConversationFKOnDeleteSetNull(db *sql.DB) (bool, error) {
	rows, err := db.Query(`PRAGMA foreign_key_list(vulnerabilities)`)
	if err != nil {
		return false, err
	}
	defer rows.Close()

	found := false
	for rows.Next() {
		var id, seq int
		var table, from, to, onUpdate, onDelete, match string
		if err := rows.Scan(&id, &seq, &table, &from, &to, &onUpdate, &onDelete, &match); err != nil {
			return false, err
		}
		if from == "conversation_id" {
			found = true
			if !strings.EqualFold(onDelete, "SET NULL") {
				return false, nil
			}
		}
	}
	if err := rows.Err(); err != nil {
		return false, err
	}
	return found, nil
}

// migrateVulnerabilitiesTable 迁移 vulnerabilities 表，补充标签字段
func (db *DB) migrateVulnerabilitiesTable() error {
	columns := []struct {
		name string
		stmt string
	}{
		{name: "conversation_tag", stmt: "ALTER TABLE vulnerabilities ADD COLUMN conversation_tag TEXT"},
		{name: "task_tag", stmt: "ALTER TABLE vulnerabilities ADD COLUMN task_tag TEXT"},
		{name: "project_id", stmt: "ALTER TABLE vulnerabilities ADD COLUMN project_id TEXT"},
		{name: "preconditions", stmt: "ALTER TABLE vulnerabilities ADD COLUMN preconditions TEXT"},
		{name: "reproduction_steps", stmt: "ALTER TABLE vulnerabilities ADD COLUMN reproduction_steps TEXT"},
		{name: "evidence", stmt: "ALTER TABLE vulnerabilities ADD COLUMN evidence TEXT"},
		{name: "retest_notes", stmt: "ALTER TABLE vulnerabilities ADD COLUMN retest_notes TEXT"},
		// 證據可信度（0-100）。既有資料一律回填 0 = 未設定。
		// 刻意不回填任何預設信心值：0 讓 UI 與報告能誠實顯示「未評分」，
		// 而不是讓幾百筆沒有 confidence 來源的舊紀錄看起來像通過了閘門。
		{name: "confidence", stmt: "ALTER TABLE vulnerabilities ADD COLUMN confidence INTEGER NOT NULL DEFAULT 0"},
	}

	for _, col := range columns {
		var count int
		err := db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('vulnerabilities') WHERE name=?", col.name).Scan(&count)
		if err != nil {
			if _, addErr := db.Exec(col.stmt); addErr != nil {
				errMsg := strings.ToLower(addErr.Error())
				if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
					db.logger.Warn("添加vulnerabilities字段失败", zap.String("field", col.name), zap.Error(addErr))
				}
			}
			continue
		}
		if count == 0 {
			if _, addErr := db.Exec(col.stmt); addErr != nil {
				db.logger.Warn("添加vulnerabilities字段失败", zap.String("field", col.name), zap.Error(addErr))
			}
		}
	}
	return nil
}

// migrateWebshellConnectionsTable 迁移 webshell_connections 表，补充新字段
func (db *DB) migrateWebshellConnectionsTable() error {
	columns := []struct {
		name string
		stmt string
	}{
		{name: "project_id", stmt: "ALTER TABLE webshell_connections ADD COLUMN project_id TEXT"},
		{name: "encoding", stmt: "ALTER TABLE webshell_connections ADD COLUMN encoding TEXT NOT NULL DEFAULT ''"},
		{name: "os", stmt: "ALTER TABLE webshell_connections ADD COLUMN os TEXT NOT NULL DEFAULT ''"},
	}

	for _, col := range columns {
		var count int
		err := db.QueryRow("SELECT COUNT(*) FROM pragma_table_info('webshell_connections') WHERE name=?", col.name).Scan(&count)
		if err != nil {
			if _, addErr := db.Exec(col.stmt); addErr != nil {
				errMsg := strings.ToLower(addErr.Error())
				if !strings.Contains(errMsg, "duplicate column") && !strings.Contains(errMsg, "already exists") {
					db.logger.Warn("添加webshell_connections字段失败", zap.String("field", col.name), zap.Error(addErr))
				}
			}
			continue
		}
		if count == 0 {
			if _, addErr := db.Exec(col.stmt); addErr != nil {
				db.logger.Warn("添加webshell_connections字段失败", zap.String("field", col.name), zap.Error(addErr))
			}
		}
	}
	return nil
}

func (db *DB) migrateC2ListenersTable() error {
	return db.addColumnIfMissing("c2_listeners", "project_id", "ALTER TABLE c2_listeners ADD COLUMN project_id TEXT")
}

// NewKnowledgeDB 创建知识库数据库连接（只包含知识库相关的表）
func NewKnowledgeDB(dbPath string, logger *zap.Logger) (*DB, error) {
	sqlDB, err := sql.Open("sqlite3", sqliteOpenDSN(dbPath))
	if err != nil {
		return nil, fmt.Errorf("打开知识库数据库失败: %w", err)
	}

	configureDBPool(sqlDB)

	if err := sqlDB.Ping(); err != nil {
		_ = sqlDB.Close()
		return nil, fmt.Errorf("连接知识库数据库失败: %w", err)
	}
	if err := configureSQLitePragmas(sqlDB); err != nil {
		_ = sqlDB.Close()
		return nil, fmt.Errorf("配置知识库数据库 PRAGMA 失败: %w", err)
	}

	database := &DB{
		DB:     sqlDB,
		logger: logger,
	}

	// 初始化知识库表
	if err := database.initKnowledgeTables(); err != nil {
		_ = sqlDB.Close()
		return nil, fmt.Errorf("初始化知识库表失败: %w", err)
	}
	database.startPassiveCheckpointLoop("knowledge")

	return database, nil
}

// initKnowledgeTables 初始化知识库数据库表（只包含知识库相关的表）
func (db *DB) initKnowledgeTables() error {
	// 创建知识库项表
	createKnowledgeBaseItemsTable := `
	CREATE TABLE IF NOT EXISTS knowledge_base_items (
		id TEXT PRIMARY KEY,
		category TEXT NOT NULL,
		title TEXT NOT NULL,
		file_path TEXT NOT NULL,
		content TEXT,
		created_at DATETIME NOT NULL,
		updated_at DATETIME NOT NULL
	);`

	// 创建知识库向量表
	createKnowledgeEmbeddingsTable := `
	CREATE TABLE IF NOT EXISTS knowledge_embeddings (
		id TEXT PRIMARY KEY,
		item_id TEXT NOT NULL,
		chunk_index INTEGER NOT NULL,
		chunk_text TEXT NOT NULL,
		embedding TEXT NOT NULL,
		sub_indexes TEXT NOT NULL DEFAULT '',
		embedding_model TEXT NOT NULL DEFAULT '',
		embedding_dim INTEGER NOT NULL DEFAULT 0,
		created_at DATETIME NOT NULL,
		FOREIGN KEY (item_id) REFERENCES knowledge_base_items(id) ON DELETE CASCADE
	);`

	// 创建知识检索日志表（在独立知识库数据库中，不使用外键约束，因为conversations和messages表可能不在这个数据库中）
	createKnowledgeRetrievalLogsTable := `
	CREATE TABLE IF NOT EXISTS knowledge_retrieval_logs (
		id TEXT PRIMARY KEY,
		conversation_id TEXT,
		message_id TEXT,
		query TEXT NOT NULL,
		risk_type TEXT,
		retrieved_items TEXT,
		created_at DATETIME NOT NULL
	);`

	// 创建索引
	createIndexes := `
	CREATE INDEX IF NOT EXISTS idx_knowledge_items_category ON knowledge_base_items(category);
	CREATE INDEX IF NOT EXISTS idx_knowledge_embeddings_item_id ON knowledge_embeddings(item_id);
	CREATE INDEX IF NOT EXISTS idx_knowledge_retrieval_logs_conversation ON knowledge_retrieval_logs(conversation_id);
	CREATE INDEX IF NOT EXISTS idx_knowledge_retrieval_logs_message ON knowledge_retrieval_logs(message_id);
	CREATE INDEX IF NOT EXISTS idx_knowledge_retrieval_logs_created_at ON knowledge_retrieval_logs(created_at);
	`

	if _, err := db.Exec(createKnowledgeBaseItemsTable); err != nil {
		return fmt.Errorf("创建knowledge_base_items表失败: %w", err)
	}

	if _, err := db.Exec(createKnowledgeEmbeddingsTable); err != nil {
		return fmt.Errorf("创建knowledge_embeddings表失败: %w", err)
	}

	if _, err := db.Exec(createKnowledgeRetrievalLogsTable); err != nil {
		return fmt.Errorf("创建knowledge_retrieval_logs表失败: %w", err)
	}

	if _, err := db.Exec(createIndexes); err != nil {
		return fmt.Errorf("创建索引失败: %w", err)
	}

	if err := db.migrateKnowledgeEmbeddingsColumns(); err != nil {
		return fmt.Errorf("迁移 knowledge_embeddings 列失败: %w", err)
	}

	db.logger.Info("知识库数据库表初始化完成")
	return nil
}

// migrateKnowledgeEmbeddingsColumns 为已有库补充 sub_indexes、embedding_model、embedding_dim。
func (db *DB) migrateKnowledgeEmbeddingsColumns() error {
	var n int
	if err := db.QueryRow(`SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='knowledge_embeddings'`).Scan(&n); err != nil {
		return err
	}
	if n == 0 {
		return nil
	}
	migrations := []struct {
		col  string
		stmt string
	}{
		{"sub_indexes", `ALTER TABLE knowledge_embeddings ADD COLUMN sub_indexes TEXT NOT NULL DEFAULT ''`},
		{"embedding_model", `ALTER TABLE knowledge_embeddings ADD COLUMN embedding_model TEXT NOT NULL DEFAULT ''`},
		{"embedding_dim", `ALTER TABLE knowledge_embeddings ADD COLUMN embedding_dim INTEGER NOT NULL DEFAULT 0`},
	}
	for _, m := range migrations {
		var colCount int
		q := `SELECT COUNT(*) FROM pragma_table_info('knowledge_embeddings') WHERE name = ?`
		if err := db.QueryRow(q, m.col).Scan(&colCount); err != nil {
			return err
		}
		if colCount > 0 {
			continue
		}
		if _, err := db.Exec(m.stmt); err != nil {
			return err
		}
	}
	return nil
}

// XssPayload represents a stored XSS payload used for cookie harvesting.
type XssPayload struct {
	ID             string
	Token          string
	Name           string
	Type           string
	Payload        string
	Config         []byte
	ProjectID      string
	Enabled        int
	Description    string
	Domain         string
	DomainOnly     int
	DNSExfilDomain string
	OneTime        int
	ExpiresAt      *time.Time
	ConsumedAt     *time.Time
	CreatedAt      time.Time
	UpdatedAt      time.Time
	CreatedBy      string
	OwnerUserID    string
	CaptureCount   int
}

// XssCapture represents a captured cookie / data from an XSS hit.
type XssCapture struct {
	ID        int64
	PayloadID string
	Token     string
	Cookie    string
	URL       string
	Domain    string
	UserAgent string
	IP        string
	Extra     string
	CreatedAt time.Time
}

// xssPayloadIDsAreText reports whether an existing table uses text IDs.
// Production rows are UUIDs. A fresh database still uses INTEGER AUTOINCREMENT.
func (db *DB) xssPayloadIDsAreText() bool {
	var typ string
	err := db.QueryRow(`SELECT type FROM pragma_table_info('xss_payloads') WHERE name = 'id'`).Scan(&typ)
	if err != nil {
		return false
	}
	upper := strings.ToUpper(typ)
	return strings.Contains(upper, "TEXT") || strings.Contains(upper, "CHAR")
}

// CreateXssPayload stores a new XSS payload and returns its database ID.
func (db *DB) CreateXssPayload(p *XssPayload) (string, error) {
	var projectID interface{} = nil
	if p.ProjectID != "" {
		projectID = p.ProjectID
	}
	var ownerUserID interface{} = nil
	if p.OwnerUserID != "" {
		ownerUserID = p.OwnerUserID
	}
	if db.xssPayloadIDsAreText() {
		id := uuid.NewString()
		_, err := db.Exec(
			`INSERT INTO xss_payloads (id, token, name, type, payload, config, project_id, enabled, description, domain, domain_only, dns_exfil_domain, script, one_time, expires_at, created_by, owner_user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?, ?, ?, ?)`,
			id, p.Token, p.Name, p.Type, p.Payload, p.Config, projectID, p.Enabled, p.Description, p.Domain, p.DomainOnly, p.DNSExfilDomain, p.OneTime, p.ExpiresAt, p.CreatedBy, ownerUserID,
		)
		if err != nil {
			return "", err
		}
		p.ID = id
		return id, nil
	}
	result, err := db.Exec(
		`INSERT INTO xss_payloads (token, name, type, payload, config, project_id, enabled, description, domain, domain_only, dns_exfil_domain, script, one_time, expires_at, created_by, owner_user_id) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '', ?, ?, ?, ?)`,
		p.Token, p.Name, p.Type, p.Payload, p.Config, projectID, p.Enabled, p.Description, p.Domain, p.DomainOnly, p.DNSExfilDomain, p.OneTime, p.ExpiresAt, p.CreatedBy, ownerUserID,
	)
	if err != nil {
		return "", err
	}
	n, err := result.LastInsertId()
	if err != nil {
		return "", err
	}
	p.ID = strconv.FormatInt(n, 10)
	return p.ID, nil
}

// ListXssPayloads returns all XSS payloads, most recent first, with capture counts.
func (db *DB) ListXssPayloads() ([]*XssPayload, error) {
	rows, err := db.Query(`SELECT p.id, COALESCE(p.token,''), COALESCE(p.name,''), COALESCE(p.type,'image'), COALESCE(p.payload,''), COALESCE(p.config,'{}'), COALESCE(p.project_id,''), COALESCE(p.enabled,0), COALESCE(p.description,''), COALESCE(p.domain,''), COALESCE(p.domain_only,0), COALESCE(p.dns_exfil_domain,''), COALESCE(p.one_time,0), p.expires_at, p.consumed_at, p.created_at, p.updated_at, COALESCE(p.created_by,''), COUNT(c.id) as capture_count FROM xss_payloads p LEFT JOIN xss_captures c ON c.payload_id = p.id GROUP BY p.id ORDER BY p.created_at DESC`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var payloads []*XssPayload
	for rows.Next() {
		var p XssPayload
		var configVal []byte
		var nameVal, typeVal, projVal, descVal, domainVal, createdByVal, dnsExfilVal string
		var domainOnlyVal, enabledVal int
		var oneTimeVal int
		var expiresAt, consumedAt sql.NullTime
		var createdAt, updatedAt time.Time
		if err := rows.Scan(&p.ID, &p.Token, &nameVal, &typeVal, &p.Payload, &configVal, &projVal, &enabledVal, &descVal, &domainVal, &domainOnlyVal, &dnsExfilVal, &oneTimeVal, &expiresAt, &consumedAt, &createdAt, &updatedAt, &createdByVal, &p.CaptureCount); err != nil {
			return nil, err
		}
		p.Name = nameVal
		p.Type = typeVal
		p.Config = configVal
		p.ProjectID = projVal
		p.Enabled = enabledVal
		p.Description = descVal
		p.Domain = domainVal
		p.DomainOnly = domainOnlyVal
		p.DNSExfilDomain = dnsExfilVal
		p.OneTime = oneTimeVal
		if expiresAt.Valid {
			p.ExpiresAt = &expiresAt.Time
		}
		if consumedAt.Valid {
			p.ConsumedAt = &consumedAt.Time
		}
		p.CreatedAt = createdAt
		p.UpdatedAt = updatedAt
		p.CreatedBy = createdByVal
		payloads = append(payloads, &p)
	}
	return payloads, rows.Err()
}

// GetXssPayload retrieves a payload by its ID. Production IDs are UUID text.
func (db *DB) GetXssPayload(id string) (*XssPayload, error) {
	var p XssPayload
	var nameVal, typeVal, projVal, descVal, domainVal, createdByVal, dnsExfilVal string
	var domainOnlyVal, enabledVal int
	var oneTimeVal int
	var expiresAt, consumedAt sql.NullTime
	var configVal []byte
	var createdAt, updatedAt time.Time
	var captureCount int
	err := db.QueryRow(
		`SELECT p.id, COALESCE(p.token,''), COALESCE(p.name,''), COALESCE(p.type,'image'), COALESCE(p.payload,''), COALESCE(p.config,'{}'), COALESCE(p.project_id,''), COALESCE(p.enabled,0), COALESCE(p.description,''), COALESCE(p.domain,''), COALESCE(p.domain_only,0), COALESCE(p.dns_exfil_domain,''), COALESCE(p.one_time,0), p.expires_at, p.consumed_at, p.created_at, p.updated_at, COALESCE(p.created_by,''), COUNT(c.id) as capture_count FROM xss_payloads p LEFT JOIN xss_captures c ON c.payload_id = p.id WHERE p.id = ? GROUP BY p.id`,
		id,
	).Scan(&p.ID, &p.Token, &nameVal, &typeVal, &p.Payload, &configVal, &projVal, &enabledVal, &descVal, &domainVal, &domainOnlyVal, &dnsExfilVal, &oneTimeVal, &expiresAt, &consumedAt, &createdAt, &updatedAt, &createdByVal, &captureCount)
	if err != nil {
		return nil, err
	}
	p.Name = nameVal
	p.Type = typeVal
	p.Config = configVal
	p.ProjectID = projVal
	p.Enabled = enabledVal
	p.Description = descVal
	p.Domain = domainVal
	p.DomainOnly = domainOnlyVal
	p.DNSExfilDomain = dnsExfilVal
	p.OneTime = oneTimeVal
	if expiresAt.Valid {
		p.ExpiresAt = &expiresAt.Time
	}
	if consumedAt.Valid {
		p.ConsumedAt = &consumedAt.Time
	}
	p.CreatedAt = createdAt
	p.UpdatedAt = updatedAt
	p.CreatedBy = createdByVal
	p.CaptureCount = captureCount
	return &p, nil
}

// GetXssPayloadByToken retrieves a payload by its token (used by the collector endpoint).
func (db *DB) GetXssPayloadByToken(token string) (*XssPayload, error) {
	var p XssPayload
	var nameVal, typeVal, projVal, descVal, domainVal, createdByVal, dnsExfilVal string
	var domainOnlyVal, enabledVal int
	var oneTimeVal int
	var expiresAt, consumedAt sql.NullTime
	var configVal []byte
	var createdAt, updatedAt time.Time
	err := db.QueryRow(
		`SELECT id, COALESCE(token,''), COALESCE(name,''), COALESCE(type,'image'), COALESCE(payload,''), COALESCE(config,'{}'), COALESCE(project_id,''), COALESCE(enabled,0), COALESCE(description,''), COALESCE(domain,''), COALESCE(domain_only,0), COALESCE(dns_exfil_domain,''), COALESCE(one_time,0), expires_at, consumed_at, created_at, updated_at, COALESCE(created_by,'') FROM xss_payloads WHERE token = ?`,
		token,
	).Scan(&p.ID, &p.Token, &nameVal, &typeVal, &p.Payload, &configVal, &projVal, &enabledVal, &descVal, &domainVal, &domainOnlyVal, &dnsExfilVal, &oneTimeVal, &expiresAt, &consumedAt, &createdAt, &updatedAt, &createdByVal)
	if err != nil {
		return nil, err
	}
	p.Name = nameVal
	p.Type = typeVal
	p.Config = configVal
	p.ProjectID = projVal
	p.Enabled = enabledVal
	p.Description = descVal
	p.Domain = domainVal
	p.DomainOnly = domainOnlyVal
	p.DNSExfilDomain = dnsExfilVal
	p.OneTime = oneTimeVal
	if expiresAt.Valid {
		p.ExpiresAt = &expiresAt.Time
	}
	if consumedAt.Valid {
		p.ConsumedAt = &consumedAt.Time
	}
	p.CreatedAt = createdAt
	p.UpdatedAt = updatedAt
	p.CreatedBy = createdByVal
	return &p, nil
}

// DeleteXssPayload removes a payload and all associated captures.
func (db *DB) DeleteXssPayload(id string) error {
	_, err := db.Exec(`DELETE FROM xss_payloads WHERE id = ?`, id)
	return err
}

// CreateXssCaptureIfAvailable atomically stores a callback only while the
// payload is enabled, unexpired and (for one-time probes) not yet consumed.
// The boolean is false when the callback is no longer eligible.
func (db *DB) CreateXssCaptureIfAvailable(payloadID string, token, cookie, url, domain, userAgent, ip, extra string) (int64, bool, error) {
	tx, err := db.Begin()
	if err != nil {
		return 0, false, err
	}
	defer func() { _ = tx.Rollback() }()

	result, err := tx.Exec(
		`UPDATE xss_payloads SET consumed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND token = ? AND enabled = 1 AND COALESCE(one_time,0) = 1 AND consumed_at IS NULL AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)`,
		payloadID, token,
	)
	if err != nil {
		return 0, false, err
	}
	claimed, err := result.RowsAffected()
	if err != nil {
		return 0, false, err
	}
	if claimed == 0 {
		var reusable int
		err = tx.QueryRow(
			`SELECT 1 FROM xss_payloads WHERE id = ? AND token = ? AND enabled = 1 AND COALESCE(one_time,0) = 0 AND (expires_at IS NULL OR expires_at > CURRENT_TIMESTAMP)`,
			payloadID, token,
		).Scan(&reusable)
		if errors.Is(err, sql.ErrNoRows) {
			return 0, false, nil
		}
		if err != nil {
			return 0, false, err
		}
	}

	result, err = tx.Exec(
		`INSERT INTO xss_captures (payload_id, token, cookie, url, domain, user_agent, ip, extra) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
		payloadID, token, cookie, url, domain, userAgent, ip, extra,
	)
	if err != nil {
		return 0, false, err
	}
	id, err := result.LastInsertId()
	if err != nil {
		return 0, false, err
	}
	if err := tx.Commit(); err != nil {
		return 0, false, err
	}
	return id, true, nil
}

// ListXssCaptures returns all captures, most recent first.
func (db *DB) ListXssCaptures() ([]*XssCapture, error) {
	rows, err := db.Query(`SELECT id, payload_id, token, cookie, url, domain, user_agent, ip, extra, created_at FROM xss_captures ORDER BY created_at DESC`)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var captures []*XssCapture
	for rows.Next() {
		var c XssCapture
		if err := rows.Scan(&c.ID, &c.PayloadID, &c.Token, &c.Cookie, &c.URL, &c.Domain, &c.UserAgent, &c.IP, &c.Extra, &c.CreatedAt); err != nil {
			return nil, err
		}
		captures = append(captures, &c)
	}
	return captures, rows.Err()
}

// ListXssCapturesByPayload returns captures for a specific payload, most recent first.
func (db *DB) ListXssCapturesByPayload(payloadID string) ([]*XssCapture, error) {
	rows, err := db.Query(`SELECT id, payload_id, token, cookie, url, domain, user_agent, ip, extra, created_at FROM xss_captures WHERE payload_id = ? ORDER BY created_at DESC`, payloadID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var captures []*XssCapture
	for rows.Next() {
		var c XssCapture
		if err := rows.Scan(&c.ID, &c.PayloadID, &c.Token, &c.Cookie, &c.URL, &c.Domain, &c.UserAgent, &c.IP, &c.Extra, &c.CreatedAt); err != nil {
			return nil, err
		}
		captures = append(captures, &c)
	}
	return captures, rows.Err()
}

// ListXssCapturesForUser returns captures whose owning payload is visible to
// userID. XSS captures carry the victim's stolen cookie and token, so listing
// them must honour the caller's scope rather than returning the whole table.
// An empty payloadID lists every visible payload; otherwise only that payload.
func (db *DB) ListXssCapturesForUser(userID string, payloadID string) ([]*XssCapture, error) {
	query := `SELECT c.id, c.payload_id, c.token, c.cookie, c.url, c.domain, c.user_agent, c.ip, c.extra, c.created_at
	          FROM xss_captures c
	          JOIN xss_payloads p ON p.id = c.payload_id
	          WHERE (p.owner_user_id = ? OR p.created_by = ?)`
	args := []interface{}{userID, userID}
	if strings.TrimSpace(payloadID) != "" {
		query += ` AND c.payload_id = ?`
		args = append(args, payloadID)
	}
	query += ` ORDER BY c.created_at DESC`
	rows, err := db.Query(query, args...)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var captures []*XssCapture
	for rows.Next() {
		var c XssCapture
		if err := rows.Scan(&c.ID, &c.PayloadID, &c.Token, &c.Cookie, &c.URL, &c.Domain, &c.UserAgent, &c.IP, &c.Extra, &c.CreatedAt); err != nil {
			return nil, err
		}
		captures = append(captures, &c)
	}
	return captures, rows.Err()
}

// GetPayloadCaptureCount returns the number of captures for a given payload.
func (db *DB) GetPayloadCaptureCount(payloadID string) (int, error) {
	var count int
	err := db.QueryRow(`SELECT COUNT(*) FROM xss_captures WHERE payload_id = ?`, payloadID).Scan(&count)
	return count, err
}

// GenerateXssToken generates a 40-char hex token for XSS payloads.
func GenerateXssToken() string {
	b := make([]byte, 20)
	if _, err := rand.Read(b); err != nil {
		return fmt.Sprintf("%x", time.Now().UnixNano())
	}
	return fmt.Sprintf("%x", b)
}

// GenerateXssTokenShort generates a short random hex token for IDs.
func GenerateXssTokenShort() string {
	b := make([]byte, 8)
	if _, err := rand.Read(b); err != nil {
		return fmt.Sprintf("%x", time.Now().UnixNano())
	}
	return fmt.Sprintf("%x", b)
}

// migrateXssPayloadsTable ensures new columns (name, type, config,
// project_id, updated_at) exist on pre-existing XSS databases.
func (db *DB) migrateXssPayloadsTable() error {
	for _, col := range []struct {
		name string
		stmt string
	}{
		{"name", "ALTER TABLE xss_payloads ADD COLUMN name TEXT"},
		{"type", "ALTER TABLE xss_payloads ADD COLUMN type TEXT DEFAULT 'image'"},
		{"config", "ALTER TABLE xss_payloads ADD COLUMN config TEXT"},
		{"project_id", "ALTER TABLE xss_payloads ADD COLUMN project_id TEXT"},
		{"updated_at", "ALTER TABLE xss_payloads ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP"},
		{"owner_user_id", "ALTER TABLE xss_payloads ADD COLUMN owner_user_id TEXT"},
		{"token", "ALTER TABLE xss_payloads ADD COLUMN token TEXT"},
		{"payload", "ALTER TABLE xss_payloads ADD COLUMN payload TEXT"},
		{"enabled", "ALTER TABLE xss_payloads ADD COLUMN enabled INTEGER DEFAULT 1"},
		{"description", "ALTER TABLE xss_payloads ADD COLUMN description TEXT"},
		{"domain", "ALTER TABLE xss_payloads ADD COLUMN domain TEXT"},
		{"domain_only", "ALTER TABLE xss_payloads ADD COLUMN domain_only INTEGER DEFAULT 0"},
		{"dns_exfil_domain", "ALTER TABLE xss_payloads ADD COLUMN dns_exfil_domain TEXT"},
		{"script", "ALTER TABLE xss_payloads ADD COLUMN script TEXT DEFAULT ''"},
		{"one_time", "ALTER TABLE xss_payloads ADD COLUMN one_time INTEGER NOT NULL DEFAULT 0"},
		{"expires_at", "ALTER TABLE xss_payloads ADD COLUMN expires_at DATETIME"},
		{"consumed_at", "ALTER TABLE xss_payloads ADD COLUMN consumed_at DATETIME"},
	} {
		if err := db.addColumnIfMissing("xss_payloads", col.name, col.stmt); err != nil {
			return err
		}
	}
	return nil
}

// migrateXssCapturesTable ensures columns (token, cookie, url, domain, user_agent,
// ip, extra) exist on pre-existing xss_captures tables.
func (db *DB) migrateXssCapturesTable() error {
	for _, col := range []struct {
		name string
		stmt string
	}{
		{"token", "ALTER TABLE xss_captures ADD COLUMN token TEXT"},
		{"cookie", "ALTER TABLE xss_captures ADD COLUMN cookie TEXT"},
		{"url", "ALTER TABLE xss_captures ADD COLUMN url TEXT"},
		{"domain", "ALTER TABLE xss_captures ADD COLUMN domain TEXT"},
		{"user_agent", "ALTER TABLE xss_captures ADD COLUMN user_agent TEXT"},
		{"ip", "ALTER TABLE xss_captures ADD COLUMN ip TEXT"},
		{"extra", "ALTER TABLE xss_captures ADD COLUMN extra TEXT"},
	} {
		if err := db.addColumnIfMissing("xss_captures", col.name, col.stmt); err != nil {
			return err
		}
	}
	return nil
}

// Close 关闭数据库连接
func (db *DB) Close() error {
	if db == nil {
		return nil
	}
	db.closeOnce.Do(func() {
		if db.checkpointStop != nil {
			close(db.checkpointStop)
			if db.checkpointDone != nil {
				<-db.checkpointDone
			}
		}
		if db.DB != nil {
			db.closeErr = db.DB.Close()
		}
	})
	return db.closeErr
}
