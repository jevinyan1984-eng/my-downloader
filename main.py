from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os

app = Flask(__name__)

# 配置 CORS：只允许你的 GitHub Pages 域名访问，防止浏览器拦截
# 请把下面的 URL 换成你实际的 GitHub Pages 域名
CORS(app, origins=["https://jevinyan1984-eng.github.io"])

@app.route('/download', methods=['POST'])
def download():
    # 1. 安全校验：检查 Referer
    # 只有来自你自己的网页的请求才被允许
    referer = request.headers.get('Referer', '')
    if 'jevinyan1984-eng.github.io' not in referer:
        return jsonify({"error": "Unauthorized access"}), 403
    
    # 2. 获取参数
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"error": "No URL provided"}), 400

    try:
        # 3. 执行 yt-dlp 命令获取视频链接
        # --get-url 会直接返回视频流地址，不会下载整个视频到服务器
        result = subprocess.check_output(
            ['yt-dlp', '--get-url', url], 
            stderr=subprocess.STDOUT
        )
        video_url = result.decode().strip()
        
        return jsonify({"video_url": video_url})
        
    except subprocess.CalledProcessError as e:
        return jsonify({"error": f"Failed to parse: {e.output.decode()}"}), 500

@app.route('/', methods=['GET'])
def index():
    return "API is running. Use POST /download with JSON body {url: '...'}"

if __name__ == '__main__':
    # Render 会自动分配 PORT 环境变量
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
