/**
 * 内置工具名称常量
 * 所有前端代码中使用内置工具名称的地方都应该使用这些常量，而不是硬编码字符串
 * 
 * 注意：这些常量与后端的 internal/mcp/builtin/constants.go 保持完全一致
 */

// 内置工具名称常量
const BuiltinTools = {
    // 漏洞管理工具
    RECORD_VULNERABILITY: 'record_vulnerability',
    LIST_VULNERABILITIES: 'list_vulnerabilities',
    GET_VULNERABILITY: 'get_vulnerability',
    GENERATE_POC_DRAFT: 'generate_poc_draft',

    // 资产管理工具
    CREATE_ASSET: 'create_asset',
    GET_ASSET: 'get_asset',
    QUERY_ASSETS: 'query_assets',
    UPDATE_ASSET: 'update_asset',
    DELETE_ASSET: 'delete_asset',
    COMPLETE_ASSET_SCAN: 'complete_asset_scan',

    // 项目黑板（事实）工具
    UPSERT_PROJECT_FACT: 'upsert_project_fact',
    GET_PROJECT_FACT: 'get_project_fact',
    LIST_PROJECT_FACTS: 'list_project_facts',
    SEARCH_PROJECT_FACTS: 'search_project_facts',
    DEPRECATE_PROJECT_FACT: 'deprecate_project_fact',
    RESTORE_PROJECT_FACT: 'restore_project_fact',

    // 知识库工具
    LIST_KNOWLEDGE_RISK_TYPES: 'list_knowledge_risk_types',
    SEARCH_KNOWLEDGE_BASE: 'search_knowledge_base',

    // 视觉分析
    ANALYZE_IMAGE: 'analyze_image',

    // 长耗时工具执行控制
    GET_TOOL_EXECUTION: 'get_tool_execution',
    WAIT_TOOL_EXECUTION: 'wait_tool_execution',
    CANCEL_TOOL_EXECUTION: 'cancel_tool_execution',

    // WebShell 助手工具
    WEBSHELL_EXEC: 'webshell_exec',
    WEBSHELL_FILE_LIST: 'webshell_file_list',
    WEBSHELL_FILE_READ: 'webshell_file_read',
    WEBSHELL_FILE_WRITE: 'webshell_file_write',

    // WebShell 连接管理工具
    MANAGE_WEBSHELL_LIST: 'manage_webshell_list',
    MANAGE_WEBSHELL_ADD: 'manage_webshell_add',
    MANAGE_WEBSHELL_UPDATE: 'manage_webshell_update',
    MANAGE_WEBSHELL_DELETE: 'manage_webshell_delete',
    MANAGE_WEBSHELL_TEST: 'manage_webshell_test',

    // 批量任务队列
    BATCH_TASK_LIST: 'batch_task_list',
    BATCH_TASK_GET: 'batch_task_get',
    BATCH_TASK_CREATE: 'batch_task_create',
    BATCH_TASK_START: 'batch_task_start',
    BATCH_TASK_RERUN: 'batch_task_rerun',
    BATCH_TASK_PAUSE: 'batch_task_pause',
    BATCH_TASK_DELETE: 'batch_task_delete',
    BATCH_TASK_UPDATE_METADATA: 'batch_task_update_metadata',
    BATCH_TASK_UPDATE_SCHEDULE: 'batch_task_update_schedule',
    BATCH_TASK_SCHEDULE_ENABLED: 'batch_task_schedule_enabled',
    BATCH_TASK_ADD_TASK: 'batch_task_add_task',
    BATCH_TASK_UPDATE_TASK: 'batch_task_update_task',
    BATCH_TASK_REMOVE_TASK: 'batch_task_remove_task',

    // C2 工具集
    C2_LISTENER: 'c2_listener',
    C2_SESSION: 'c2_session',
    C2_TASK: 'c2_task',
    C2_TASK_MANAGE: 'c2_task_manage',
    C2_PAYLOAD: 'c2_payload',
    C2_EVENT: 'c2_event',
    C2_PROFILE: 'c2_profile',
    C2_FILE: 'c2_file',

    // 暴露面哨兵工具
    SENTINEL_SCAN: 'sentinel_scan',
    GET_SENTINEL_SCAN: 'get_sentinel_scan',
    SENTINEL_SYNC_ASSETS: 'sentinel_sync_assets',
    SENTINEL_SYNC_VULNERABILITIES: 'sentinel_sync_vulnerabilities',

    // POC / EXP 在线弱验证工具
    VERIFY_POC: 'verify_poc'
};

// 检查是否是内置工具
function isBuiltinTool(toolName) {
    return Object.values(BuiltinTools).includes(toolName);
}

// 获取所有内置工具名称列表
function getAllBuiltinTools() {
    return Object.values(BuiltinTools);
}
