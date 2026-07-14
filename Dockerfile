FROM python:3.11-slim

WORKDIR /app

COPY . .

LABEL org.opencontainers.image.source="https://github.com/houcem58/aml-fraud-detection-platform"
LABEL org.opencontainers.image.description="AML Fraud Detection Platform — Showcase"
LABEL org.opencontainers.image.licenses="Apache-2.0"

CMD ["python", "demo/examples/01_single_transaction.py"]
