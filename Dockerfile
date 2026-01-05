# =============================
# Stage 1: Builder
# =============================
FROM alpine:3.23 AS builder

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apk add --no-cache \
    python3 \
    py3-pip \
    build-base \
    libffi-dev \
    musl-dev

# Create venv
RUN python3 -m venv /venv
ENV PATH="/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# =============================
# Stage 2: Runtime
# =============================
FROM alpine:3.23

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/venv/bin:$PATH"

RUN apk add --no-cache \
    python3 \
    libffi \
    busybox \
    netcat-openbsd \
    wget \
    logger

# Copy only the virtualenv
COPY --from=builder /venv /venv

# Copy app source
COPY --from=builder /app /app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5000
ENTRYPOINT ["/entrypoint.sh"]
