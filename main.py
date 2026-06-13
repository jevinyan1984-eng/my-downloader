from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import json

app = Flask(__name__)
# 允许你的 GitHub Pages 跨域访问
CORS(app, origins=["https://jevinyan1984-eng.github.io"])

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({"status": "error", "message": "未提供链接"}), 400

    try:
        # 使用 yt-dlp 获取视频信息
        # 加入 --no-warnings 防止日志过载
        result = subprocess.check_output(
            ['yt-dlp', '--dump-json', '--no-warnings', url], 
            stderr=subprocess.STDOUT
        )
        info = json.loads(result.decode())
        
        # 提取关键信息
        response_data = {
            "status": "success",
            "title": info.get("title", "未知标题"),
            "thumbnail": info.get("thumbnail", ""),
            "formats": [
                {"url": f.get("url"), "note": f.get("format_note", "标准")} 
                for f in info.get("formats", []) 
                if f.get("vcodec") != "none"
            ]
        }
        return jsonify(response_data)
        
    except Exception as e:
        # 异常捕获：返回状态码 200，让前端正常处理错误，而不是让后端 500 崩溃
        return jsonify({"status": "error", "message": str(e)}), 200

@app.route('/', methods=['GET'])
def index():
    return "API is running."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
