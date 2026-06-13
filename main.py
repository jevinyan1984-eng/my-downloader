import os
import json
import subprocess
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import requests

app = Flask(__name__)
# 确保 CORS 配置允许所有来源
CORS(app, resources={r"/*": {"origins": "*"}})

def setup_cookies():
    # 确保 Render 环境变量正确读取
    yt_content = os.environ.get('YOUTUBE_COOKIES')
    if yt_content:
        with open('youtube_cookies.txt', 'w', encoding='utf-8') as f:
            f.write(yt_content)
        print(f"DEBUG: YouTube cookies loaded, size: {os.path.getsize('youtube_cookies.txt')} bytes")

setup_cookies()

@app.route('/', methods=['GET'])
def home():
    return "怡烨科技 解析服务运行正常", 200

# 强制确保这个路由存在，且处理了 URL 参数
@app.route('/proxy_download', methods=['GET'])
def proxy_download():
    video_url = request.args.get('url')
    if not video_url:
        return "No URL provided", 400
    try:
        r = requests.get(video_url, stream=True, timeout=15)
        return Response(stream_with_context(r.iter_content(chunk_size=1024)), 
                        content_type=r.headers.get('Content-Type', 'video/mp4'))
    except Exception as e:
        print(f"DEBUG_PROXY_ERROR: {str(e)}")
        return "Proxy failed", 500

@app.route('/download', methods=['POST', 'OPTIONS'])
def download():
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"status": "error", "message": "URL missing"}), 400
    
    try:
        cmd = ['yt-dlp', '--dump-json', '--no-warnings', '--no-playlist']
        if os.path.exists('youtube_cookies.txt'):
            cmd.extend(['--cookies', 'youtube_cookies.txt'])
        cmd.extend(['--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36', url])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"DEBUG_ERROR: {result.stderr}")
            return jsonify({"status": "error", "message": "解析失败，请查看日志"}), 200
            
        info = json.loads(result.stdout)
        
        # 核心：过滤掉不可用的格式
        formats = info.get("formats", [])
        valid_formats = [{"url": f.get("url"), "note": f.get("format_note", "高清")} 
                         for f in formats if f.get("url")]
        
        if not valid_formats:
            return jsonify({"status": "error", "message": "未找到可下载的格式，请重试"}), 200

        return jsonify({
            "status": "success",
            "title": info.get("title", "无标题"),
            "thumbnail": info.get("thumbnail", ""),
            "formats": valid_formats
        })
        
    except Exception as e:
        print(f"DEBUG_EXCEPTION: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
