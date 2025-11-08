# Stage 1: Build dependencies (optional)
FROM python:3.10-alpine AS builder

WORKDIR /app
COPY requirements.txt .

RUN apk add --no-cache gcc musl-dev libffi-dev openssl-dev \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM python:3.10-alpine

WORKDIR /app
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY . .

CMD ["python", "bot.py"]
