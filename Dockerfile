# Multi-stage production build
# Stage 1: Build React frontend
FROM node:20-alpine as frontend-build

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# Stage 2: Production Python backend with built frontend
FROM python:3.12-slim as backend

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

# Set working directory
WORKDIR /app

# Copy uv files first for better caching
COPY pyproject.toml uv.lock ./

# Install only production dependencies
RUN uv sync --frozen --no-cache --no-dev

# Copy backend source code
COPY src/ src/
COPY config/ config/

# Install custom dependencies from submodules (if any exist)
# This step runs after copying source to discover any custom requirements.txt files
RUN find src/custom_tools src/custom_resources -name "requirements.txt" 2>/dev/null | \
    xargs -r -I {} uv pip install -r {} || true

# Copy built frontend static files
COPY --from=frontend-build /app/frontend/dist /app/static

# Expose port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app/src
ENV UV_PROJECT_ENVIRONMENT=/app/.venv
ENV PRODUCTION=true

# Run migrations first, then start app with 2 workers for Fly.io
CMD ["sh", "-c", "cd src/migrations && uv run alembic upgrade head && cd /app && uv run uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 2"]