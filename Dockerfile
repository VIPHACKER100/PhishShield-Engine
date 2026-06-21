FROM python:3.11-slim as builder

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y --no-install-recommends gcc python3-dev && rm -rf /var/lib/apt/lists/*

# Install Python deps into wheels
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Final Stage
FROM python:3.11-slim

WORKDIR /app

COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .

RUN pip install --no-cache /wheels/*

# Download NLTK data at build time
RUN python -c "import nltk; nltk.download('punkt'); nltk.download('punkt_tab'); nltk.download('stopwords')"

# Copy project
COPY . .

# Generate dataset & train models during build (optional - can be skipped with --target=base)
ARG TRAIN_MODELS=true
RUN if [ "$TRAIN_MODELS" = "true" ]; then python scripts/train_pipeline.py --generate --fast; fi

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run
CMD ["uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
