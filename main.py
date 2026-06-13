import os
import json
import subprocess
import requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://video-downloader.youtube.kdns.fr"}})

@app.route('/stream_video', methods=['GET'])
def stream_video():
    video_url = request.args.get('url')
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://twitter.com/",
        "Range": request.headers.get('Range')
    }
    try:
        req = requests.get(video_url, headers=headers, stream=True, timeout=30)
        return Response(
            stream_with_context(req.iter_content(chunk_size=1024)),
            status=req.status_code,
            headers={
                "Content-Type": req.headers.get('Content-Type', 'video/mp4'),
                "Content-Range": req.headers.get('Content-Range'),
                "Accept-Ranges": "bytes",
                "Content-Length": req.headers.get('Content-Length')
            }
        )
    except:
        return "下载失败", 500

@app.route('/download', methods=['POST', 'OPTIONS'])
def download():
    if request.method == 'OPTIONS': return '', 200
    
    # 校验 Referer
    if "video-downloader.youtube.kdns.fr" not in request.headers.get('Referer', ''):
        return jsonify({"status": "error", "message": "非法调用"}), 403

    data = request.json
    url = data.get('url', '').split('?')[0]
    
    cmd = ['yt-dlp', '--dump-json', '--no-warnings', '--no-playlist', 
           '--user-agent', 'Mozilla/5.0', '--referer', 'https://twitter.com/',
           '--cookies', 'twitter_cookies.txt', url]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return jsonify({"status": "error", "message": "解析失败"}), 200
        
    try:
        info = json.loads(result.stdout)
        formats = [{"url": f"/stream_video?url={f.get('url')}", "res": f"{f.get('width', 0)}x{f.get('height', 0)}", "note": f.get("format_note", "高清")} 
                   for f in info.get("formats", []) if f.get("vcodec") != "none" and f.get("ext") == "mp4"]
        return jsonify({"status": "success", "title": info.get("title", "Twitter视频"), "thumbnail": info.get("thumbnail", ""), "formats": list({f['res']: f for f in formats}.values())})
    except:
        return jsonify({"status": "error", "message": "解析错误"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
