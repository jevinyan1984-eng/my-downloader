import os
import json
import subprocess
import requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
# 仅允许你的前端域名访问
CORS(app, resources={r"/*": {"origins": "https://video-downloader.youtube.kdns.fr"}})

@app.route('/stream_video', methods=['GET'])
def stream_video():
    video_url = request.args.get('url')
    # 模拟真实浏览器请求，携带必须的 Referer
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://twitter.com/"
    }
    try:
        # 使用 stream=True 进行流式处理，不一次性占用内存
        req = requests.get(video_url, headers=headers, stream=True, timeout=30)
        return Response(stream_with_context(req.iter_content(chunk_size=1024)), 
                        content_type=req.headers.get('Content-Type', 'video/mp4'))
    except Exception as e:
        return "视频流传输失败", 500

@app.route('/download', methods=['POST', 'OPTIONS'])
def download():
    if request.method == 'OPTIONS': return '', 200
    
    # 强制来源校验，防止恶意 API 调用
    if "video-downloader.youtube.kdns.fr" not in request.headers.get('Referer', ''):
        return jsonify({"status": "error", "message": "非法调用"}), 403

    data = request.json
    url = data.get('url', '').split('?')[0]
    
    cmd = [
        'yt-dlp', '--dump-json', '--no-warnings', '--no-playlist',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        '--referer', 'https://twitter.com/',
        '--cookies', 'twitter_cookies.txt',
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return jsonify({"status": "error", "message": "解析失败"}), 200
        
    try:
        info = json.loads(result.stdout)
        formats = []
        for f in info.get("formats", []):
            if f.get("vcodec") != "none" and f.get("ext") == "mp4":
                res = f"{f.get('width', 'Unknown')}x{f.get('height', 'Unknown')}"
                # 将 URL 指向我们的 stream_video 代理接口
                proxy_url = f"/stream_video?url={f.get('url')}"
                formats.append({"url": proxy_url, "res": res, "note": f.get("format_note") or "高清"})
        
        return jsonify({
            "status": "success",
            "title": info.get("title", "Twitter 视频"),
            "thumbnail": info.get("thumbnail", ""),
            "formats": list({f['res']: f for f in formats}.values()) # 去重
        })
    except:
        return jsonify({"status": "error", "message": "数据解析异常"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
