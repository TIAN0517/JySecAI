# JySecAI SSL Certificates Directory

Place your SSL/TLS certificate and private key files here for Nginx gateway TLS termination:

- `jysecai.crt` — TLS certificate chain (e.g. Cloudflare Origin Cert or Let's Encrypt fullchain)
- `jysecai.key` — TLS private key

Mounted automatically into `/etc/nginx/ssl/` in Docker Compose (`compose.jysec.yml`).

## Quick Self-Signed Certificate Generation (Dev/Testing):
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout deploy/ssl/jysecai.key \
  -out deploy/ssl/jysecai.crt \
  -subj "/CN=jysecai.local"
```
