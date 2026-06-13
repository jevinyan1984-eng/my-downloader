import json
import subprocess
import requests
import urllib.parse # 新增：用于处理文件名编码
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "https://video-downloader.youtube.kdns.fr"}})

ALLOWED_DOMAIN = "video-downloader.youtube.kdns.fr"

@app.route('/stream_video', methods=['GET'])
def stream_video():
    video_url = request.args.get('url')
    # 获取传递过来的标题，用于设置下载文件名
    title = request.args.get('title', 'twitter_video')
    # 对标题进行 URL 编码，防止中文文件名乱码
    safe_filename = urllib.parse.quote(f"{title}.mp4")
    
    if not video_url:
        return "URL缺失", 400
        
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://twitter.com/",
        "Range": request.headers.get('Range', '')
    }
    
    try:
        req = requests.get(video_url, headers=headers, stream=True, timeout=30)
        
        # 核心修改：增加 Content-Disposition，强制浏览器触发下载弹窗
        # filename*=UTF-8'' 格式确保在 iPhone/Android 上的兼容性
        headers_resp = {
            "Content-Type": "video/mp4",
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}",
            "Content-Range": req.headers.get('Content-Range'),
            "Accept-Ranges": "bytes"
        }
        
        return Response(
            stream_with_context(req.iter_content(chunk_size=1024)),
            status=req.status_code,
            headers=headers_resp
        )
    except:
        return "传输失败", 500

@app.route('/download', methods=['POST'])
def download():
    # 域名校验
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
    title = info.get("title", "Twitter_Video")
    
    # 返回包含 title 的下载链接，以便前端传给 stream_video
    return jsonify({
        "status": "success",
        "title": title,
        "thumbnail": info.get("thumbnail"),
        "url": f"/stream_video?url={direct_url}&title={urllib.parse.quote(title)}"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
