# Build context: repository root (see docker/asr-inference/README.md).
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        ffmpeg \
        python3.11 \
        python3.11-venv \
        python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && ln -sf /usr/bin/python3.11 /usr/local/bin/python \
    && ln -sf /usr/bin/pip3 /usr/local/bin/pip

WORKDIR /app

COPY backend/pyproject.toml backend/README.md ./
COPY backend/app ./app

# CUDA-enabled PyTorch for faster-whisper on GPU nodes (P7-003).
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cu124 \
    "torch>=2.2.0" "torchaudio>=2.2.0" \
    && pip install --no-cache-dir . \
    && pip install --no-cache-dir nvidia-ml-py

ENV HOST=0.0.0.0
ENV PORT=8081
ENV LOG_FORMAT=json
ENV ASR_BACKEND=faster_whisper
ENV ASR_DEVICE=cuda
ENV ASR_COMPUTE_TYPE=float16

EXPOSE 8081

CMD ["python", "-m", "app.asr_inference.main"]
