import os
import json
import subprocess
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/download', methods=['POST', 'OPTIONS'])
def download():
    if request.method == 'OPTIONS': return '', 200
    data = request.json
    url = data.get('url')
    if not url: return jsonify({"status": "error", "message": "No URL"}), 400
    
    try:
        # 使用 --cookies-from-browser 逻辑的变体
        cmd = ['yt-dlp', '--dump-json', '--no-warnings', '--no-playlist']
        
        # 针对不同平台加载 Cookie
        if 'twitter.com' in url or 'x.com' in url:
            if os.path.exists('twitter_cookies.txt'): cmd.extend(['--cookies', 'twitter_cookies.txt'])
        elif 'youtube.com' in url or 'youtu.be' in url:
            if os.path.exists('youtube_cookies.txt'): cmd.extend(['--cookies', 'youtube_cookies.txt'])
            
        cmd.extend([url])
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            return jsonify({"status": "error", "message": "解析失败，请检查 Cookie 是否过期"}), 200
            
        info = json.loads(result.stdout)
        # 只提取 MP4 格式，排除掉 m3u8 等需要二次流处理的复杂格式
        formats = [{"url": f.get("url"), "note": f.get("format_note", "高清")} 
                   for f in info.get("formats", []) if f.get("ext") == "mp4"]
        
        return jsonify({"status": "success", "title": info.get("title"), "formats": formats[:3]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 200

# 只有对于旧式视频才走代理，新视频建议前端直接下载
@app.route('/proxy_download')
def proxy_download():
    video_url = request.args.get('url')
    # 增加 Referer，防止视频源服务器拦截
    headers = {"Referer": "https://twitter.com/"}
    r = requests.get(video_url, stream=True, headers=headers, timeout=10)
    return Response(r.iter_content(chunk_size=1024), content_type=r.headers.get('Content-Type'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
