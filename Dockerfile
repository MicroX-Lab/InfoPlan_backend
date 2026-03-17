FROM python:3.11-slim

WORKDIR /app

# 安装 Node.js（预编译二进制，不需要编译，秒装）
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl xz-utils \
    && curl -fsSL https://nodejs.org/dist/v20.18.0/node-v20.18.0-linux-x64.tar.xz \
       | tar -xJ -C /usr/local --strip-components=1 \
    && apt-get purge -y xz-utils \
    && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

# 安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/ --trusted-host mirrors.aliyun.com

# 复制项目文件
COPY . .

# 环境变量
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

EXPOSE 5001

CMD ["gunicorn", "-c", "gunicorn.conf.py", "run:app"]
