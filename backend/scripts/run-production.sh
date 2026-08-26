#!/bin/sh
# Production entry. Single process only — stranded recovery assumes no other
# worker still owns in-flight 零件图 jobs. Do not add --reload or --workers N.
set -eu

cd "$(dirname "$0")/.."

uv run alembic upgrade head
exec uv run uvicorn quote_assistant.interface.http.app:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 1
