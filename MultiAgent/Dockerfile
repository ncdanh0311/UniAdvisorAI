# ===================================================
# Dockerfile cho Streamlit Multi-Agent Dashboard
# Container: streamlit-agent-container
# ===================================================

FROM python:3.11-slim

WORKDIR /app

# Cài đặt các gói hệ thống cần thiết
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements và cài đặt dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ mã nguồn MultiAgent
COPY . .

# Mở cổng Streamlit
EXPOSE 8501

# Thiết lập biến môi trường cho Python
ENV PYTHONUNBUFFERED=1

# Kiểm tra trạng thái container (Healthcheck)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
  CMD curl -f http://localhost:8501/_stcore/health || exit 1

# Khởi chạy ứng dụng Streamlit
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
