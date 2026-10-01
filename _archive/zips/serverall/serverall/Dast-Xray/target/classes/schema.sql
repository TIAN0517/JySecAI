-- Dast-Xray H2数据库初始化脚本

-- 创建工具设置表
CREATE TABLE IF NOT EXISTS toolsetting (
    id VARCHAR(50) PRIMARY KEY,
    xraypath VARCHAR(255) DEFAULT '/usr/local/bin/xray',
    crawlergopath VARCHAR(255) DEFAULT '/usr/local/bin/crawlergo',
    chromepath VARCHAR(255) DEFAULT '/usr/bin/google-chrome'
);

-- 创建用户表
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(50) PRIMARY KEY,
    username VARCHAR(100) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

-- 创建任务表
CREATE TABLE IF NOT EXISTS tasks (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url VARCHAR(1000) NOT NULL,
    output VARCHAR(2000),
    format VARCHAR(50) DEFAULT 'json',
    status INTEGER DEFAULT 0,
    xyport VARCHAR(50),
    crawlerid VARCHAR(100),
    createuser VARCHAR(100),
    createtime TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source INTEGER DEFAULT 1,
    groupId VARCHAR(100),
    webhookid VARCHAR(100)
);

-- 创建任务报告表
CREATE TABLE IF NOT EXISTS task_report (
    id INTEGER AUTO_INCREMENT PRIMARY KEY,
    task_id BIGINT NOT NULL,
    report_path VARCHAR(1000) NOT NULL,
    create_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status INTEGER DEFAULT 1,
    source INTEGER DEFAULT 1,
    name VARCHAR(255),
    url VARCHAR(1000),
    groupId VARCHAR(100),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- 创建API密钥表
CREATE TABLE IF NOT EXISTS apisecret (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    apiSecret VARCHAR(255) NOT NULL UNIQUE,
    status INTEGER DEFAULT 1
);

-- 创建WebHook配置表
CREATE TABLE IF NOT EXISTS webhook (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    webhookurl VARCHAR(1000) NOT NULL,
    secret VARCHAR(255)
);

-- 插入默认数据 (使用MERGE避免重复)
MERGE INTO toolsetting (id, xraypath, crawlergopath, chromepath) KEY (id)
VALUES ('default', '/usr/local/bin/xray', '/usr/local/bin/crawlergo', '/usr/bin/google-chrome');

-- 插入默认管理员用户 (密码: Ss520520@@)
INSERT INTO users (id, username, password)
VALUES ('admin', 'admin', '29060b04c2974e430c23bef014664087');