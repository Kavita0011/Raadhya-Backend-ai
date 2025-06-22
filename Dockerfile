# ---- Base Build Stage ----
FROM python:3.11-slim-bookworm AS build

# System dependencies
RUN apt-get update && apt-get install -y curl build-essential

# Poetry installation
ENV POETRY_HOME="/opt/poetry"
ENV PATH="${POETRY_HOME}/bin:$PATH"
RUN curl -sSL https://install.python-poetry.org | python3 -

# Force Poetry to create .venv inside the project folder
ENV POETRY_VIRTUALENVS_IN_PROJECT=true

# Set working directory
WORKDIR /app

# Copy only dependency files first
COPY pyproject.toml .

# Install dependencies (without dev)
RUN poetry install --no-root --only main

# ---- Production Stage ----
FROM python:3.11-slim-bookworm AS production

ENV POETRY_HOME="/opt/poetry"
ENV PATH="${POETRY_HOME}/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy virtual environment from build stage
COPY --from=build /app/.venv /app/.venv

# Ensure Python uses the venv
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="/app/.venv/bin:$PATH"

# Copy the app source code
COPY backend ./backend
COPY alembic.ini .

# Expose the app port
EXPOSE 8000

# Command to run the FastAPI app
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
