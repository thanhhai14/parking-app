FROM python:3.10-slim

WORKDIR /app

# Copy requirements and install using Aliyun PyPI mirror
COPY requirements.txt .
RUN pip install --no-cache-dir -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt

# Copy source code
COPY . .

# Environment variables with defaults
ENV APP_PORT=8000

# Expose port
EXPOSE 8000

# Start command
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${APP_PORT}"]
