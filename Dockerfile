# syntax=docker/dockerfile:1
FROM python:3.12-slim

LABEL org.opencontainers.image.title="sharepoint-mcp" \
    org.opencontainers.image.description="MCP Server for Microsoft SharePoint" \
    org.opencontainers.image.version="1.0.0" \
    org.opencontainers.image.source="https://github.com/ravikant1918/sharepoint-mcp" \
    org.opencontainers.image.licenses="MIT"

# ---------- system deps ----------
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# ---------- non-root user ----------
RUN useradd --create-home --shell /bin/bash mcp
USER mcp
WORKDIR /home/mcp/app

# ---------- python deps ----------
COPY --chown=mcp:mcp pyproject.toml ./
COPY --chown=mcp:mcp src/ ./src/

RUN pip install --no-cache-dir --user -e .

ENV PATH="/home/mcp/.local/bin:$PATH"

# ---------- runtime config ----------
# TRANSPORT: stdio | http   (default: http for Docker)
ENV TRANSPORT=http
ENV HTTP_HOST=0.0.0.0
ENV HTTP_PORT=8000
ENV LOG_FORMAT=json
ENV LOG_LEVEL=INFO

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "-m", "mcp_sharepoint"]
