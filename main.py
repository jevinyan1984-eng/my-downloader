import json
import subprocess
import requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
# 允许特定域名的跨域请求
CORS(app, resources={r"/*": {"origins": "https://video-downloader.youtube.kdns.fr"}})

# 严格校验域名
ALLOWED_DOMAIN = "video-downloader.youtube.kdns.fr"

@app.route('/stream_video', methods=['GET'])
def stream_video():
    video_url = request.args.get('url')
    if not video_url:
        return "URL缺失", 400
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://twitter.com/",
        "Range": request.headers.get('Range', '')
    }
    try:
        req = requests.get(video_url, headers=headers, stream=True, timeout=30)
        return Response(
            stream_with_context(req.iter_content(chunk_size=1024)),
            status=req.status_code,
            headers={
                "Content-Type": req.headers.get('Content-Type', 'video/mp4'),
                "Content-Range": req.headers.get('Content-Range'),
                "Accept-Ranges": "bytes"
            }
        )
    except:
        return "传输失败", 500

@app.route('/download', methods=['POST'])
def download():
    # 域名校验逻辑
    referer = request.headers.get('Referer', '')
    if ALLOWED_DOMAIN not in referer:
        return jsonify({"status": "error", "message": "非法调用，拒绝访问"}), 403

    data = request.json
    url = data.get('url', '').split('?')[0]
    if not url:
        return jsonify({"status": "error", "message": "请输入链接"}), 200

    # 1. 强制获取最佳 MP4 直链
    cmd_url = ['yt-dlp', '-f', 'best[ext=mp4]', '--get-url', '--cookies', 'twitter_cookies.txt', url]
    direct_url = subprocess.run(cmd_url, capture_output=True, text=True).stdout.strip()
    
    # 2. 获取标题和封面图
    cmd_info = ['yt-dlp', '--dump-json', '--cookies', 'twitter_cookies.txt', url]
    info_json = subprocess.run(cmd_info, capture_output=True, text=True).stdout
    
    if not direct_url or not info_json:
        return jsonify({"status": "error", "message": "解析失败，请检查链接或 Cookie"}), 200
        
    info = json.loads(info_json)
    
    return jsonify({
        "status": "success",
        "title": info.get("title", "Twitter 视频"),
        "thumbnail": info.get("thumbnail"),
        "url": f"/stream_video?url={direct_url}"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
