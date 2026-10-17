FROM node:24-bookworm-slim@sha256:d6aa754f16b3197301076f047b5def2f02ea1dbbc2ca920407d46d7ec7f87b20 AS web
WORKDIR /build
COPY frontend/package*.json ./
RUN --mount=type=secret,id=build_ca \
    if [ -f /run/secrets/build_ca ]; then export NODE_EXTRA_CA_CERTS=/run/secrets/build_ca; fi; \
    npm ci --no-audit --no-fund
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258 AS dependencies
WORKDIR /build
RUN --mount=type=secret,id=build_ca \
    if [ -f /run/secrets/build_ca ]; then export PIP_CERT=/run/secrets/build_ca; fi; \
    pip install --no-cache-dir uv==0.12.23
COPY pyproject.toml uv.lock ./
RUN uv export --locked --no-dev --no-emit-project --format requirements-txt --output-file requirements.txt > /dev/null
RUN --mount=type=secret,id=build_ca \
    if [ -f /run/secrets/build_ca ]; then export PIP_CERT=/run/secrets/build_ca; fi; \
    pip install --no-cache-dir --require-hashes --prefix=/install -r requirements.txt

FROM python:3.12-slim-bookworm@sha256:34386ef0cb081344d7ec1c103ba398e6e9f64e9ab3a1509accc92a4e24a07258
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 HOST=0.0.0.0 CRICKET_DB_PATH=/var/lib/cricket/arena.sqlite3
WORKDIR /app
RUN groupadd --gid 10001 cricket && useradd --uid 10001 --gid cricket --no-create-home cricket \
    && mkdir -p /var/lib/cricket && chown cricket:cricket /var/lib/cricket
COPY --from=dependencies /install /usr/local
COPY --chown=10001:10001 backend/ ./backend/
COPY --from=web --chown=10001:10001 /build/dist ./frontend/dist/
USER 10001:10001
EXPOSE 8000
HEALTHCHECK --interval=20s --timeout=5s --start-period=30s --retries=3 \
    CMD python -c "import os,urllib.request;urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('PORT','8000')+'/api/health',timeout=4)"
CMD ["python","-m","backend"]
