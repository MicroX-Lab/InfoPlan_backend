FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（Node.js 用于 XHS 签名脚本）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 环境变量
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 5001

CMD ["gunicorn", "-c", "gunicorn.conf.py", "run:app"]
