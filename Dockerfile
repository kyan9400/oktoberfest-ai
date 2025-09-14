# ===== Oktoberfest AI – Docker =====
FROM python:3.11-slim

# Prevent apt from asking questions
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_NO_CACHE_DIR=1 \
    PYTHONUNBUFFERED=1

# System deps (for some HF models / pandas)
RUN apt-get update && apt-get install -y --no-install-recommends \
      git curl ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first for better build caching
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip && pip install -r /app/requirements.txt

# Copy the rest of the project
COPY . /app

# Default command runs a quick offline smoke test
# You can override this with: docker run  -- python oktoberfest_analyzer.py --source news 
ENTRYPOINT ["python", "oktoberfest_analyzer.py"]
CMD ["--source", "sample"]
