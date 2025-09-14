# syntax=docker/dockerfile:1.6
FROM python:3.11-slim

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DEFAULT_TIMEOUT=180 \
    HF_HUB_DISABLE_SYMLINKS_WARNING=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
      git curl ca-certificates build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.docker.txt /app/requirements.txt

# Allow sgmllib3k to build from sdist; keep wheels for the rest + PyTorch CPU index
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m pip install --upgrade pip && \
    pip install --no-binary=sgmllib3k sgmllib3k && \
    pip install --prefer-binary \
      --extra-index-url https://download.pytorch.org/whl/cpu \
      -r /app/requirements.txt

COPY . /app

ENTRYPOINT ["python","oktoberfest_analyzer.py"]
CMD ["--source","sample","--model","oliverguhr/german-sentiment-bert"]
