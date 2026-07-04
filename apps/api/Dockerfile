# syntax=docker/dockerfile:1
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# curl powers the container healthcheck; build-essential compiles any wheels.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt ./
RUN pip install --upgrade pip && pip install -r requirements.txt

COPY . .

# Run as a non-root user.
RUN useradd --create-home --uid 10001 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=5 \
    CMD curl -fsS http://localhost:${PORT:-8000}/health || exit 1

# Default: serve the API. Shell form so ${PORT} (injected by hosts like Render)
# is honored, falling back to 8000 for local/compose use. The compose `migrate`
# service overrides this with `alembic upgrade head`, and the `worker` service
# with the Celery command.
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
