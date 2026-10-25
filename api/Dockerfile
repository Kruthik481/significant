FROM python:3.13-slim
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy PYTHONUNBUFFERED=1
COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev
COPY app ./app
RUN useradd --create-home appuser
USER appuser
EXPOSE 8300
CMD /app/.venv/bin/uvicorn --factory app.main:app_from_env --host 0.0.0.0 --port ${PORT:-8300}
