# syntax=docker/dockerfile:1.7

FROM node:24-bookworm-slim AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY tsconfig.json ./
COPY src ./src
RUN npm run build && npm prune --omit=dev

FROM node:24-bookworm-slim AS control-plane
ENV NODE_ENV=production \
    JYSEC_HOST=0.0.0.0 \
    JYSEC_PORT=8787
WORKDIR /app
COPY --from=build --chown=node:node /app/package.json /app/package-lock.json ./
COPY --from=build --chown=node:node /app/node_modules ./node_modules
COPY --from=build --chown=node:node /app/dist ./dist
COPY --chown=node:node public ./public
COPY --chown=node:node migrations ./migrations
USER node
EXPOSE 8787
HEALTHCHECK --interval=20s --timeout=4s --start-period=15s --retries=5 \
  CMD ["node", "-e", "fetch('http://127.0.0.1:8787/healthz').then(r=>{if(!r.ok)process.exit(1)}).catch(()=>process.exit(1))"]
CMD ["node", "dist/main.js"]

FROM python:3.13-slim-bookworm AS worker
ARG STRIX_VERSION=1.5.3
ENV NODE_ENV=production \
    PYTHONUNBUFFERED=1 \
    PATH=/opt/strix/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates passwd tini \
    && rm -rf /var/lib/apt/lists/* \
    && python -m venv /opt/strix \
    && /opt/strix/bin/pip install --no-cache-dir "strix-agent==${STRIX_VERSION}" \
    && groupadd --gid 10001 jysec \
    && useradd --uid 10001 --gid 10001 --create-home --shell /usr/sbin/nologin jysec \
    && mkdir -p /app /var/lib/jysec/runs \
    && chown -R jysec:jysec /app /var/lib/jysec
COPY --from=build /usr/local/bin/node /usr/local/bin/node
WORKDIR /app
COPY --from=build --chown=jysec:jysec /app/package.json /app/package-lock.json ./
COPY --from=build --chown=jysec:jysec /app/node_modules ./node_modules
COPY --from=build --chown=jysec:jysec /app/dist ./dist
USER jysec
ENTRYPOINT ["tini", "--"]
CMD ["node", "dist/worker/main.js"]
