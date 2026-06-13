import json
import subprocess
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

@app.route('/stream_video', methods=['GET'])
def stream_video():
    video_url = request.args.get('url')
    # 增加 Range 头转发以支持视频拖动播放
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://twitter.com/",
        "Range": request.headers.get('Range', '')
    }
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

@app.route('/download', methods=['POST'])
def download():
    url = request.json.get('url')
    # 使用 -f best[ext=mp4] 强制选取 MP4 格式，避免下载到 m3u8
    cmd = [
        'yt-dlp', '-f', 'best[ext=mp4]', '--get-url',
        '--cookies', 'twitter_cookies.txt',
        '--user-agent', 'Mozilla/5.0', url
    ]
    
    process = subprocess.run(cmd, capture_output=True, text=True)
    direct_url = process.stdout.strip()
    
    if not direct_url:
        return jsonify({"status": "error", "message": "无法解析 MP4 视频，请检查链接"}), 200

    return jsonify({
        "status": "success",
        "title": "Twitter 视频",
        "url": f"/stream_video?url={direct_url}"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
