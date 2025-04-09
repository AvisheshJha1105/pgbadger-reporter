FROM python:3.11-slim

LABEL maintainer="avishesh.jha@gmail.com"
LABEL description="pgBadger + PDF report generator with S3 upload"

RUN apt-get update && apt-get install -y \
    pgbadger \
    wkhtmltopdf \
    libpq-dev \
    build-essential \
    curl \
    unzip \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir -r requirements.txt

RUN mkdir -p /tmp/rds_downloaded_logs/error \
             /tmp/rds_downloaded_logs/report \
             /tmp/rds_downloaded_logs/pdf_report

ENTRYPOINT ["python", "script.py"]
CMD ["--help"]
