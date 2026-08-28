FROM node:24-alpine AS frontend-builder

WORKDIR /frontend
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim

WORKDIR /app
COPY . .
COPY --from=frontend-builder /frontend/dist /app/frontend/dist
RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && pip install --no-cache-dir .

ENV NFL_FIDOS_ENV=production
ENV NFL_FIDOS_AUTH_SECRET_FILE=/run/secrets/nfl_fidos_auth_secret
ENV NFL_FIDOS_HOST=0.0.0.0
ENV NFL_FIDOS_PORT=8080
ENV NFL_FIDOS_DATABASE=/var/lib/nfl-fidos/nfl_fidos.sqlite3
ENV NFL_FIDOS_FFMPEG=ffmpeg
ENV NFL_FIDOS_FFPROBE=ffprobe
ENV NFL_FIDOS_OBSERVABILITY_PATH=/var/lib/nfl-fidos/observability.jsonl
VOLUME ["/var/lib/nfl-fidos"]
EXPOSE 8080
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=3)"
CMD ["nfl-fidos-server"]
