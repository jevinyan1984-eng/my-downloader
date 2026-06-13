from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import subprocess
import os
import json
import requests

app = Flask(__name__)

# 配置：正式部署域名
ALLOWED_DOMAIN = "video-downloader.youtube.kdns.fr"

# 跨域配置
CORS(app, origins=[f"https://{ALLOWED_DOMAIN}"])

@app.route('/', methods=['GET'])
def home():
    return "怡烨科技 全能视频解析服务运行中!", 200

# 安全校验函数
def is_valid_request():
    referer = request.headers.get('Referer', '')
    if ALLOWED_DOMAIN in referer:
        return True
    return False

@app.route('/download', methods=['POST'])
def download():
    if not is_valid_request():
        return jsonify({"status": "error", "message": "Access Denied"}), 403
        
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"status": "error", "message": "URL missing"}), 400
    
    try:
        # yt-dlp 支持绝大多数国内外视频网站
        cmd = ['yt-dlp', '--dump-json', '--no-warnings', url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return jsonify({"status": "error", "message": "解析失败，请检查链接"}), 200
            
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
    
    # 针对不同平台的智能 Header 策略
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'}
    
    if 'x.com' in video_url or 'twitter.com' in video_url:
        headers['Referer'] = 'https://x.com/'
    elif 'youtube.com' in video_url or 'youtu.be' in video_url:
        headers['Referer'] = 'https://www.youtube.com/'
    elif 'tiktok.com' in video_url:
        headers['Referer'] = 'https://www.tiktok.com/'
    elif 'douyin.com' in video_url or 'iesdouyin.com' in video_url:
        headers['Referer'] = 'https://www.douyin.com/'
        
    try:
        r = requests.get(video_url, headers=headers, stream=True, timeout=15)
        return Response(stream_with_context(r.iter_content(chunk_size=1024)), 
                        content_type=r.headers.get('Content-Type', 'video/mp4'))
    except Exception as e:
        return f"Download failed: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
