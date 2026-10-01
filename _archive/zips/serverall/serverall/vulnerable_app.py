#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vulnerable Web Application - For Local Testing & Demonstration
包含多种真实漏洞用于演示
"""

from flask import Flask, request, render_template_string, jsonify
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'test_db.sqlite'

def init_db():
    """Initialize database with test data"""
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
    
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            username TEXT,
            password TEXT,
            email TEXT,
            credit_card TEXT
        )
    ''')
    
    # Insert test data
    cursor.execute("INSERT INTO users VALUES (1, 'admin', 'admin123', 'admin@test.com', '4532-1234-5678-9999')")
    cursor.execute("INSERT INTO users VALUES (2, 'user1', 'pass123', 'user1@test.com', '4111-1111-1111-1111')")
    cursor.execute("INSERT INTO users VALUES (3, 'user2', 'secret456', 'user2@test.com', '5555-5555-5555-4444')")
    
    conn.commit()
    conn.close()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Home page"""
    html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>⚡ 赛博朋克安全测试平台</title>
        <style>
            body {
                background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
                color: #00ff41;
                font-family: 'Courier New', monospace;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: rgba(0, 0, 0, 0.8);
                border: 1px solid #00ff41;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 0 20px rgba(0, 255, 65, 0.3);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            .header h1 {
                font-size: 2.5em;
                margin: 0;
                text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41;
                animation: glow 2s ease-in-out infinite alternate;
            }
            .subtitle {
                color: #00d4ff;
                font-size: 1.2em;
                margin-top: 10px;
            }
            .menu {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-top: 40px;
            }
            .menu-item {
                background: rgba(0, 255, 65, 0.1);
                border: 1px solid #00ff41;
                border-radius: 8px;
                padding: 20px;
                text-align: center;
                text-decoration: none;
                color: #00ff41;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
            }
            .menu-item:hover {
                background: rgba(0, 255, 65, 0.2);
                transform: translateY(-5px);
                box-shadow: 0 0 15px rgba(0, 255, 65, 0.5);
            }
            .menu-item::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(0, 255, 65, 0.2), transparent);
                transition: left 0.5s;
            }
            .menu-item:hover::before {
                left: 100%;
            }
            .menu-title {
                font-size: 1.3em;
                font-weight: bold;
                margin-bottom: 10px;
                color: #00d4ff;
            }
            .menu-desc {
                font-size: 0.9em;
                color: #66ff99;
            }
            .status {
                text-align: center;
                margin-top: 30px;
                padding: 15px;
                background: rgba(255, 0, 128, 0.1);
                border: 1px solid #ff0080;
                border-radius: 5px;
            }
            .status-text {
                color: #ff0080;
                font-weight: bold;
            }
            @keyframes glow {
                from { text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41; }
                to { text-shadow: 0 0 20px #00ff41, 0 0 30px #00ff41, 0 0 40px #00ff41; }
            }
            .terminal {
                background: rgba(0, 0, 0, 0.9);
                border: 1px solid #00ff41;
                border-radius: 5px;
                padding: 15px;
                margin-top: 20px;
                font-family: 'Courier New', monospace;
                color: #00ff41;
            }
            .terminal::before {
                content: "root@cyber-test:~# ";
                color: #ff0080;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚡ 赛博朋克安全测试平台</h1>
                <div class="subtitle">探索数字世界的脆弱边界</div>
            </div>
            
            <div class="status">
                <div class="status-text">🚨 系统状态: 在线 | 安全等级: 测试模式</div>
            </div>
            
            <div class="menu">
                <a href="/search" class="menu-item">
                    <div class="menu-title">💾 SQL注入攻击</div>
                    <div class="menu-desc">测试数据库安全漏洞</div>
                </a>
                <a href="/comment" class="menu-item">
                    <div class="menu-title">🌐 XSS跨站脚本</div>
                    <div class="menu-desc">客户端脚本注入测试</div>
                </a>
                <a href="/api/users" class="menu-item">
                    <div class="menu-title">🔓 API数据泄露</div>
                    <div class="menu-desc">信息泄露漏洞检测</div>
                </a>
            </div>
            
            <div class="terminal">
                系统已启动 | 端口:5000 | 准备接收测试载荷...
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route('/search')
def search():
    """SQL Injection Vulnerability"""
    query = request.args.get('q', '')
    
    html = """
    <h1>用户搜索 (存在SQL注入漏洞)</h1>
    <form method="GET">
        <input type="text" name="q" value="%s" placeholder="输入用户名">
        <input type="submit" value="搜索">
    </form>
    <hr>
    """ % query
    
    if query:
        try:
            # VULNERABLE: Direct SQL concatenation
            conn = get_db()
            sql = "SELECT * FROM users WHERE username LIKE '%" + query + "%'"
            print(f"[DEBUG] SQL Query: {sql}")
            
            cursor = conn.cursor()
            cursor.execute(sql)
            results = cursor.fetchall()
            conn.close()
            
            if results:
                html += "<h2>搜索结果:</h2><table border='1'>"
                for row in results:
                    html += f"<tr><td>{row['id']}</td><td>{row['username']}</td><td>{row['email']}</td></tr>"
                html += "</table>"
            else:
                html += "<p>未找到结果</p>"
        except Exception as e:
            html += f"<p><b>错误:</b> {str(e)}</p>"
    
    return render_template_string(html)

@app.route('/comment')
def comment():
    """XSS Vulnerability"""
    msg = request.args.get('msg', '')
    
    html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>🌐 XSS跨站脚本测试</title>
        <style>
            body {
                background: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
                color: #00ff41;
                font-family: 'Courier New', monospace;
                margin: 0;
                padding: 20px;
                min-height: 100vh;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: rgba(0, 0, 0, 0.8);
                border: 1px solid #00ff41;
                border-radius: 10px;
                padding: 30px;
                box-shadow: 0 0 20px rgba(0, 255, 65, 0.3);
            }
            .header {
                text-align: center;
                margin-bottom: 30px;
            }
            .header h1 {
                font-size: 2.2em;
                margin: 0;
                text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41;
                animation: glow 2s ease-in-out infinite alternate;
            }
            .warning {
                background: rgba(255, 0, 128, 0.1);
                border: 1px solid #ff0080;
                border-radius: 5px;
                padding: 15px;
                margin: 20px 0;
                color: #ff0080;
            }
            .form-group {
                margin-bottom: 20px;
            }
            textarea {
                width: 100%;
                height: 120px;
                background: rgba(0, 0, 0, 0.7);
                border: 1px solid #00ff41;
                border-radius: 5px;
                color: #00ff41;
                font-family: 'Courier New', monospace;
                padding: 10px;
                font-size: 14px;
                resize: vertical;
            }
            textarea:focus {
                outline: none;
                box-shadow: 0 0 10px rgba(0, 255, 65, 0.5);
            }
            input[type="submit"] {
                background: linear-gradient(45deg, #00ff41, #00d4ff);
                border: none;
                border-radius: 5px;
                color: #000;
                padding: 12px 30px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            input[type="submit"]:hover {
                transform: translateY(-2px);
                box-shadow: 0 5px 15px rgba(0, 255, 65, 0.4);
            }
            .comments {
                margin-top: 30px;
                border-top: 1px solid #00ff41;
                padding-top: 20px;
            }
            .comment {
                background: rgba(0, 255, 65, 0.1);
                border: 1px solid #00ff41;
                border-radius: 5px;
                padding: 15px;
                margin-bottom: 15px;
                position: relative;
                overflow: hidden;
            }
            .comment::before {
                content: '💬';
                position: absolute;
                left: -10px;
                top: 50%;
                transform: translateY(-50%);
                color: #00d4ff;
            }
            @keyframes glow {
                from { text-shadow: 0 0 10px #00ff41, 0 0 20px #00ff41; }
                to { text-shadow: 0 0 20px #00ff41, 0 0 30px #00ff41, 0 0 40px #00ff41; }
            }
            .back-btn {
                display: inline-block;
                background: rgba(255, 0, 128, 0.2);
                border: 1px solid #ff0080;
                border-radius: 5px;
                padding: 10px 20px;
                color: #ff0080;
                text-decoration: none;
                margin-bottom: 20px;
                transition: all 0.3s ease;
            }
            .back-btn:hover {
                background: rgba(255, 0, 128, 0.3);
                transform: translateY(-2px);
            }
        </style>
    </head>
    <body>
        <div class="container">
            <a href="/" class="back-btn">← 返回主界面</a>
            
            <div class="header">
                <h1>🌐 XSS跨站脚本测试</h1>
            </div>
            
            <div class="warning">
                ⚠️ <strong>警告:</strong> 此页面存在XSS漏洞，请谨慎测试！
            </div>
            
            <div class="form-group">
                <form method="GET">
                    <textarea name="msg" placeholder="在此输入XSS载荷进行测试...\n例如: &lt;script&gt;alert('XSS')&lt;/script&gt;\n&lt;img src=x onerror=alert('XSS')&gt;">%s</textarea>
                    <br><br>
                    <input type="submit" value="🚀 执行测试">
                </form>
            </div>
            
            <div class="comments">
                <h3>💬 测试结果:</h3>
    """ % msg
    
    if msg:
        # VULNERABLE: No sanitization
        html += f"""
                <div class="comment">
                    {msg}
                </div>
        """
    else:
        html += """
                <div style="color: #66ff99; text-align: center; padding: 20px;">
                    等待测试数据...
                </div>
        """
    
    html += """
            </div>
        </div>
    </body>
    </html>
    """
    
    return render_template_string(html)

@app.route('/api/users')
def api_users():
    """API Endpoint - Information Disclosure"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, username, email, credit_card FROM users")
    users = cursor.fetchall()
    conn.close()
    
    # Returns all user data including credit cards
    return jsonify([dict(row) for row in users])

@app.route('/api/users/<int:user_id>')
def api_user(user_id):
    """API Endpoint - IDOR Vulnerability"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    
    if user:
        return jsonify(dict(user))
    else:
        return jsonify({"error": "User not found"}), 404

@app.route('/xss_collect')
def xss_collect():
    """XSS数据收集端点"""
    html = """
    <h1>XSS数据收集</h1>
    <p>此端点用于收集XSS攻击数据</p>
    <p>访问 /collect 端点提交XSS测试数据</p>
    """
    return render_template_string(html)

@app.route('/collect', methods=['POST'])
def collect():
    """收集XSS测试数据"""
    try:
        data = request.get_json()
        if data:
            print(f"[XSS DATA] {data}")
            return jsonify({"status": "success", "message": "数据已收集"})
        else:
            return jsonify({"status": "error", "message": "无效数据"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({"status": "running", "version": "1.0"})

if __name__ == '__main__':
    print("[*] Initializing vulnerable database...")
    init_db()
    print("[+] Database initialized with test data")
    print("[*] Starting vulnerable web application on http://localhost:5000")
    app.run(debug=True, port=5000, host='127.0.0.1')
