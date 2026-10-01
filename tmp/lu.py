import sqlite3
c=sqlite3.connect(r'C:\Users\Administrator\Desktop\JySecAI\data\conversations.db')
print(c.execute('select username, enabled, is_builtin from rbac_users').fetchall())
