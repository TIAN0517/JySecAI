# Dast-Xray PostgreSQL 配置指南

## 📋 当前配置状态

### ✅ 已完成配置
- **数据库驱动**：PostgreSQL 42.3.8 驱动已添加
- **连接配置**：已配置用户名、密码和数据库名
- **分页插件**：已设置为PostgreSQL方言

### 🔧 连接配置信息
```
数据库类型：PostgreSQL
主机地址：localhost (已从postgresql修改)
端口：5432
数据库名：bossjy
用户名：lstjks
密码：Ss520520@@
```

## 🚨 连接问题诊断

### 当前错误
```
java.net.UnknownHostException: postgresql
```

### 解决方案

#### 方案1：使用localhost（已应用）
如果PostgreSQL安装在本地：
```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/bossjy
```

#### 方案2：使用具体IP地址
如果PostgreSQL在其他服务器：
```yaml
spring:
  datasource:
    url: jdbc:postgresql://<服务器IP>:5432/bossjy
```

#### 方案3：配置hosts文件
如果要继续使用`postgresql`主机名：
1. 编辑 `C:\Windows\System32\drivers\etc\hosts`
2. 添加：`127.0.0.1 postgresql`

## 🔍 连接测试步骤

### 1. 确认PostgreSQL服务状态
```bash
# Windows服务检查
services.msc

# 或命令行检查
net start postgresql-x64-14
```

### 2. 测试数据库连接
```sql
-- 使用psql命令行工具
psql -h localhost -p 5432 -U lstjks -d bossjy

-- 或使用pgAdmin等GUI工具
```

### 3. 检查防火墙设置
确保5432端口已开放：
```bash
# Windows防火墙
netsh advfirewall firewall add rule name="PostgreSQL" dir=in action=allow protocol=TCP localport=5432
```

## 🗄️ 数据库初始化

### 创建数据库（如果不存在）
```sql
CREATE DATABASE bossjy;
CREATE USER lstjks WITH PASSWORD 'Ss520520@@';
GRANT ALL PRIVILEGES ON DATABASE bossjy TO lstjks;
```

### 验证表结构
系统会自动使用`schema.sql`创建必要的表：
- `users` - 用户表
- `tasks` - 任务表
- `task_report` - 任务报告表
- `toolsetting` - 工具设置表
- `apisecret` - API密钥表
- `webhook` - WebHook配置表

## 🚀 启动应用

### 重新构建项目
```bash
cd "C:\Users\Administrator\desktop\serverall\Dast-Xray"
mvn clean package -DskipTests
```

### 启动Spring Boot应用
```bash
mvn spring-boot:run
```

## 🌐 访问应用

### 前端地址
- http://localhost:9531/

### 后端API
- http://localhost:8090/api/

### 默认登录信息
- 用户名：admin
- 密码：admin123admin

## 🔧 故障排除

### 常见问题

1. **连接超时**
   - 检查PostgreSQL服务是否运行
   - 确认端口5432是否被占用

2. **认证失败**
   - 验证用户名和密码
   - 检查用户权限设置

3. **数据库不存在**
   - 创建bossjy数据库
   - 检查用户是否有创建权限

### 调试模式
启用详细日志：
```yaml
logging:
  level:
    org.postgresql: DEBUG
    com.zaxxer.hikari: DEBUG
```

## 📞 技术支持

如遇到问题，请检查：
1. PostgreSQL服务状态
2. 网络连接
3. 防火墙设置
4. 用户权限配置

配置完成后，Dast-Xray将成功连接到PostgreSQL数据库并开始工作。