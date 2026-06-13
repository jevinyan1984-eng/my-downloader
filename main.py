from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import subprocess
import os
import json
import requests

app = Flask(__name__)

# 设置你的域名
ALLOWED_DOMAIN = "video-downloader.youtube.kdns.fr"
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/', methods=['GET'])
def home():
    return "API is running!", 200

def is_valid_request():
    referer = request.headers.get('Referer', '')
    print(f"DEBUG: Checking Referer: {referer}") # <--- 关键：在Render日志里查看这个值
    
    # 检查逻辑：只要域名存在于 referer 中即通过
    if ALLOWED_DOMAIN in referer:
        return True
    return False

@app.route('/download', methods=['POST'])
def download():
    if not is_valid_request():
        return jsonify({"status": "error", "message": "Access Denied: Referer invalid"}), 403
        
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"status": "error", "message": "URL missing"}), 400
    
    try:
        cmd = ['yt-dlp', '--dump-json', '--no-warnings', url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"DEBUG: yt-dlp error: {result.stderr}") # <--- 关键：查看解析报错
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
        print(f"DEBUG: Server error: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 200

@app.route('/proxy_download')
def proxy_download():
    # 允许直接访问，或者你也可以加上 referer 校验
    video_url = request.args.get('url')
    if not video_url: return "No URL", 400
    
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://x.com/'}
    r = requests.get(video_url, headers=headers, stream=True)
    return Response(stream_with_context(r.iter_content(chunk_size=1024)), 
                    content_type=r.headers.get('Content-Type', 'video/mp4'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
