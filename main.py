from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import subprocess
import os
import json
import requests

app = Flask(__name__)
# 允许你的前端域名跨域
CORS(app, origins=["https://jevinyan1984-eng.github.io"])

# 1. 核心解析路由
@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"status": "error", "message": "未提供URL"}), 400
    
    try:
        # 使用 yt-dlp 获取视频元数据
        cmd = ['yt-dlp', '--dump-json', '--no-warnings', url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return jsonify({"status": "error", "message": f"解析失败: {result.stderr}"}), 200
            
        info = json.loads(result.stdout)
        return jsonify({
            "status": "success",
            "title": info.get("title", "无标题"),
            "thumbnail": info.get("thumbnail", ""),
            "formats": [{"url": f.get("url"), "note": f.get("format_note", "高清")} 
                        for f in info.get("formats", []) if f.get("vcodec") != "none"]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 200

# 2. 保证下载的代理路由 (防止403的关键)
@app.route('/proxy_download')
def proxy_download():
    video_url = request.args.get('url')
    if not video_url:
        return "Missing URL", 400
    
    # 伪装请求头，让 Twitter 认为这是合法浏览器请求
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://x.com/'
    }
    
    try:
        # 流式请求，不一次性占用服务器内存
        r = requests.get(video_url, headers=headers, stream=True)
        return Response(stream_with_context(r.iter_content(chunk_size=1024)), 
                        content_type=r.headers.get('Content-Type', 'video/mp4'))
    except Exception as e:
        return f"下载失败: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
