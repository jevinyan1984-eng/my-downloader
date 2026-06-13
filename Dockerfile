# 使用基础 Python 镜像
FROM python:3.9-slim

# 安装系统依赖（FFmpeg 和 yt-dlp 需要）
RUN apt-get update && apt-get install -y ffmpeg

# 设置工作目录
WORKDIR /app

# 复制所有文件到工作目录
COPY . .

# 安装 Python 依赖
RUN pip install -r requirements.txt

# 设置启动命令 (Render 需要通过端口 8080 访问)
CMD ["python", "main.py"]
