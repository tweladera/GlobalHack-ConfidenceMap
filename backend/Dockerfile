FROM python:3.12-slim

# Copy uv binary from official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Install dependencies using the lockfile (reproducible builds)
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application source
COPY confidence_map/ confidence_map/

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "confidence_map.main:app", \
     "--host", "0.0.0.0", "--port", "8000"]
