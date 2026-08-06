# Step 1: Download Python Linux base image (Debian slim)
FROM python:3.11-slim

# Set environment variables for unbuffered logging & HuggingFace cache
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/app/.cache/huggingface

WORKDIR /app

# Step 2: Install system Linux dependencies (build-essential, libpq-dev, etc.)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Step 3: Copy requirements.txt
COPY requirements.txt .

# Step 4: Install all Python dependencies (numpy, scikit-learn, sentence-transformers, etc.)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Pre-cache the sentence-transformers model inside the reusable image layer
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"

# Step 5: Copy project source code into container
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Step 6: Entrypoint command for running FastAPI with Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
