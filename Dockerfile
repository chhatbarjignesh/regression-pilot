FROM python:3.11-slim

WORKDIR /app

# Install system deps for Playwright
RUN apt-get update && apt-get install -y \
    curl wget gnupg nodejs npm \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install -e ".[dev]" && playwright install chromium --with-deps

COPY . .

EXPOSE 8000
CMD ["python", "-m", "agent.cli", "serve", "--host", "0.0.0.0", "--port", "8000"]
