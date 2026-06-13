FROM python:3.9-slim

# 安装系统级依赖
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 先只复制 requirements.txt，这样如果不改依赖，缓存就不会失效，速度更快
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 再复制你的代码
COPY . .

CMD ["python", "main.py"]
