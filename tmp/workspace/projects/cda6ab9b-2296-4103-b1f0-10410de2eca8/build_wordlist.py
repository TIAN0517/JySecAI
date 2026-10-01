paths = []
# Common admin/config
common = """
admin admin.php admin/ administrator administrator/ administrator/index.php
wp-login.php wp-admin/ login.php login/ logon.php signin.php
config config.php config.yml .env .env.local .git/ .git/config .svn/
api/ api/v1/ api/v2/ api/health api/info swagger ui swagger-ui.html
docs/ docs api-docs redoc
actuator actuator/health actuator/env actuator/beans actuator/mappings actuator/trace
backup/ backups/ backup.zip site.zip db.sql dump.sql
phpmyadmin pma phpMyAdmin mysql/
.git/ .svn/ .DS_Store robots.txt sitemap.xml
server-status server-info info.php info.php phplist
dashboard/ panel/ control/ controlpanel/ manage/
static/ assets/ media/ templates/ modules/ plugins/ components/
install/ installation/ setup/ debug/ test/
.bak .backup sql .tar.gz .zip .rar
config.inc.php configuration.php wp-config.php database.php
xmlrpc.php feed rss atom
.npmrc .dockerenv docker-compose.yml Dockerfile
.env.production .env.example production.env staging.env
.htaccess .htpasswd
web.config webconfig
backup.php adminer.php
phpinfo.php test.php debug.php error.log access.log
security.txt .well-known/ .well-known/security.txt
console/ phpinfo information.php
"""
for p in common.split():
    if p and p not in paths: paths.append(p)
# api-endpoints from dirsearchplus
try:
    for line in open('/root/dirsearchplus/db/api-endpoints.txt'):
        p = line.strip()
        if p and p not in paths: paths.append(p)
except: pass
# Joomla-specific
joomla = """
index.php?option=com_content&
modules/ templates/ language/ plugins/
components/com_users/ components/com_contact/
installation/
"""
open('dirb_wordlist.txt','w').write('\n'.join(paths))
print("wordlist entries:", len(paths))
