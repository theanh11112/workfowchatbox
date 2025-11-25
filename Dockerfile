FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1

# Cài đặt curl cho healthcheck
RUN apt-get update && apt-get install -y curl && apt-get clean

# Copy requirements và cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code từ thư mục app
COPY app/ .

# Tạo thư mục logs
RUN mkdir -p logs

EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/api/v1/health || exit 1

CMD ["python", "main.py"]
