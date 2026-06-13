from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import json

app = Flask(__name__)
# 确保域名完全匹配
CORS(app, origins=["https://jevinyan1984-eng.github.io"])

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"status": "error", "message": "未提供URL"}), 400
    
    try:
        # 使用 --dump-json 获取视频元数据
        cmd = ['yt-dlp', '--dump-json', '--no-warnings', url]
        result = subprocess.check_output(cmd, stderr=subprocess.STDOUT)
        info = json.loads(result.decode())
        
        return jsonify({
            "status": "success",
            "title": info.get("title", "无标题"),
            "thumbnail": info.get("thumbnail", ""),
            "formats": [{"url": f.get("url"), "note": f.get("format_note", "高清")} 
                        for f in info.get("formats", []) if f.get("vcodec") != "none"]
        })
    except Exception as e:
        # 错误时返回 status: error，不要直接 500 报错
        return jsonify({"status": "error", "message": str(e)}), 200

@app.route('/', methods=['GET'])
def index():
    return "API is running."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
