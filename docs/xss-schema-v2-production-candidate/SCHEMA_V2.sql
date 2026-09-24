-- Rich Schema v2. Fresh databases only. Parent projects/conversations tables are initialized by NewDB.
CREATE TABLE IF NOT EXISTS xss_payloads (
 id TEXT PRIMARY KEY, project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
 conversation_id TEXT REFERENCES conversations(id) ON DELETE SET NULL,
 name TEXT NOT NULL DEFAULT '', source_url TEXT NOT NULL DEFAULT '', script TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'armed', created_by TEXT,
 created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
 callback_token TEXT, enabled INTEGER NOT NULL DEFAULT 1, domain TEXT NOT NULL DEFAULT '',
 domain_only INTEGER NOT NULL DEFAULT 0, owner_user_id TEXT
);
CREATE TABLE IF NOT EXISTS xss_captures (
 id TEXT PRIMARY KEY, payload_id TEXT REFERENCES xss_payloads(id) ON DELETE SET NULL,
 project_id TEXT REFERENCES projects(id) ON DELETE SET NULL,
 conversation_id TEXT REFERENCES conversations(id) ON DELETE SET NULL,
 status TEXT NOT NULL DEFAULT 'new', source_url TEXT NOT NULL DEFAULT '', page_title TEXT NOT NULL DEFAULT '',
 user_agent TEXT NOT NULL DEFAULT '', client_ip TEXT NOT NULL DEFAULT '', url_fragment TEXT NOT NULL DEFAULT '',
 cookies_json TEXT NOT NULL DEFAULT '{}', local_storage_json TEXT NOT NULL DEFAULT '{}',
 session_storage_json TEXT NOT NULL DEFAULT '{}', api_keys_json TEXT NOT NULL DEFAULT '{}',
 seized_at DATETIME, created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP, updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);
