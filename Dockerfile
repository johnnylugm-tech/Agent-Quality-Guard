# Agent Quality Guard - Dockerfile

FROM python:3.11-slim

# 設置工作目錄
WORKDIR /app

# 複製依賴文件
COPY requirements.txt .

# 安裝依賴
RUN pip install --no-cache-dir -r requirements.txt

# 複製應用程序
COPY src/ ./src/

# 創建數據目錄
RUN mkdir -p data reports

# 安裝預設
ENV PYTHONPATH=/app

# 啟動命令
CMD ["python", "src/main.py"]

# 或者啟動 API Server
# CMD ["python", "-c", "from src.api_server import run_server; run_server()"]
