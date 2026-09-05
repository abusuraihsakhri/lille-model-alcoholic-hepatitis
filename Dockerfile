FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default: run single calculation example. Override for API server or other commands.
CMD ["python", "cli.py", "single", "--age", "50", "--albumin-day0", "3.0", \
     "--bilirubin-day0", "15.0", "--bilirubin-day7", "10.0", "--creatinine", "1.0"]
