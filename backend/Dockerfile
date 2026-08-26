# Production image for the 机加工报价辅助 backend.
#
# Deploy shape (MVP): ONE process. Do not raise --workers, do not run a second
# replica. Startup recovery marks leftover 已上传 / 分级中 / 提取中 as 提取失败;
# a second live process would have those jobs stolen out from under it.
#
# Build from this directory: `docker build -t quote-assistant-api .`

FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:0.8.15 /uv /usr/local/bin/uv

WORKDIR /app

COPY pyproject.toml uv.lock alembic.ini ./
COPY alembic ./alembic
COPY src ./src
COPY scripts ./scripts

RUN chmod +x scripts/run-production.sh \
    && uv sync --frozen --no-dev

ENV PYTHONPATH=/app/src
ENV QA_APP_ENV=production
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8000

# No --reload. workers stay 1 (see scripts/run-production.sh).
CMD ["sh", "scripts/run-production.sh"]
