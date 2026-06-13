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

   # 修改原来的 try 部分，改用 yt-dlp 获取 JSON 信息
try:
    # --dump-json 获取视频的元数据（预览图、分辨率等）
    result = subprocess.check_output(
        ['yt-dlp', '--dump-json', url], 
        stderr=subprocess.STDOUT
    )
    # 解析 JSON 数据
    import json
    info = json.loads(result.decode())
    
    # 提取我们想要的数据
    response_data = {
        "title": info.get("title"),
        "thumbnail": info.get("thumbnail"),
        "formats": [{"url": f.get("url"), "note": f.get("format_note")} 
                    for f in info.get("formats", []) if f.get("vcodec") != "none"]
    }
    return jsonify(response_data)

@app.route('/', methods=['GET'])
def index():
    return "API is running. Use POST /download with JSON body {url: '...'}"

if __name__ == '__main__':
    # Render 会自动分配 PORT 环境变量
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
