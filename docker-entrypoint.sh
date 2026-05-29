#!/bin/sh
set -eu

mkdir -p /app/app/generated /app/app/data

if id appuser >/dev/null 2>&1; then
  chown -R appuser:appuser /app/app/generated /app/app/data 2>/dev/null || true
  exec su appuser -s /bin/sh -c "$*"
fi

exec "$@"
