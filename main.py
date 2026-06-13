from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import subprocess
import os
import json
import requests

app = Flask(__name__)

# 修改：这里填入你最终部署域名的地址
ALLOWED_DOMAIN = "https://your-domain.com" 
CORS(app, origins=[ALLOWED_DOMAIN])

# 根路由：保持监控正常
@app.route('/', methods=['GET'])
def home():
    return "API is running!", 200

# 校验器函数：检查 Referer
def is_valid_request():
    referer = request.headers.get('Referer')
    # 如果没有 Referer 或者来源域名不是你的，则拒绝
    if not referer or ALLOWED_DOMAIN not in referer:
        return False
    return True

@app.route('/download', methods=['POST'])
def download():
    # 安全校验：阻止非本站调用
    if not is_valid_request():
        return jsonify({"status": "error", "message": "Access Denied: Invalid Origin"}), 403
        
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"status": "error", "message": "未提供URL"}), 400
    
    try:
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

@app.route('/proxy_download')
def proxy_download():
    # 安全校验：阻止非本站调用
    if not is_valid_request():
        return "Access Denied: Invalid Origin", 403
        
    video_url = request.args.get('url')
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': 'https://x.com/'
    }
    
    try:
        r = requests.get(video_url, headers=headers, stream=True)
        return Response(stream_with_context(r.iter_content(chunk_size=1024)), 
                        content_type=r.headers.get('Content-Type', 'video/mp4'))
    except Exception as e:
        return f"下载转发失败: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
