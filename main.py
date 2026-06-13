from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import subprocess
import os
import json
import requests

app = Flask(__name__)

# 配置：正式部署域名
ALLOWED_DOMAIN = "video-downloader.youtube.kdns.fr"

# 严格的跨域限制：只允许你的域名调用
CORS(app, origins=[f"https://{ALLOWED_DOMAIN}"])

@app.route('/', methods=['GET'])
def home():
    return "怡烨科技 Twitter 解析服务运行中!", 200

# 校验函数
def is_valid_request():
    referer = request.headers.get('Referer', '')
    # 只要 Referer 中包含你的域名即视为合法请求
    if ALLOWED_DOMAIN in referer:
        return True
    return False

@app.route('/download', methods=['POST'])
def download():
    # 安全检查
    if not is_valid_request():
        return jsonify({"status": "error", "message": "Access Denied"}), 403
        
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"status": "error", "message": "URL missing"}), 400
    
    try:
        # 使用 yt-dlp 获取视频信息
        cmd = ['yt-dlp', '--dump-json', '--no-warnings', url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return jsonify({"status": "error", "message": "解析失败"}), 200
            
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
    video_url = request.args.get('url')
    if not video_url: return "No URL", 400
    
    # 这里通过添加 Referer 绕过 Twitter 对直接下载的限制
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://x.com/'}
    r = requests.get(video_url, headers=headers, stream=True)
    return Response(stream_with_context(r.iter_content(chunk_size=1024)), 
                    content_type=r.headers.get('Content-Type', 'video/mp4'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
