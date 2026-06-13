import os
import json
import subprocess
import requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)

# 配置：生产环境域名，用于跨域安全校验
ALLOWED_DOMAIN = "video-downloader.youtube.kdns.fr"
CORS(app, origins=[f"https://{ALLOWED_DOMAIN}"])

# --- Cookie 自动生成逻辑 ---
def setup_cookies():
    # 从 Render 环境变量读取 Cookie 内容并生成本地文件
    yt_content = os.environ.get('YOUTUBE_COOKIES')
    dy_content = os.environ.get('DOUYIN_COOKIES')
    
    if yt_content:
        with open('youtube_cookies.txt', 'w', encoding='utf-8') as f:
            f.write(yt_content)
    if dy_content:
        with open('douyin_cookies.txt', 'w', encoding='utf-8') as f:
            f.write(dy_content)

# 初始化 Cookie
setup_cookies()

@app.route('/', methods=['GET'])
def home():
    return "怡烨科技 全能视频解析服务正常运行中", 200

# 安全校验
def is_valid_request():
    referer = request.headers.get('Referer', '')
    return ALLOWED_DOMAIN in referer

@app.route('/download', methods=['POST'])
def download():
    if not is_valid_request():
        return jsonify({"status": "error", "message": "Access Denied"}), 403
        
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"status": "error", "message": "URL missing"}), 400
    
    try:
        # 构建 yt-dlp 命令
        cmd = ['yt-dlp', '--dump-json', '--no-warnings', '--no-playlist']
        
        # 智能匹配 Cookie 文件
        if 'douyin.com' in url or 'tiktok.com' in url:
            if os.path.exists('douyin_cookies.txt'):
                cmd.extend(['--cookies', 'douyin_cookies.txt'])
        else:
            if os.path.exists('youtube_cookies.txt'):
                cmd.extend(['--cookies', 'youtube_cookies.txt'])
            
        cmd.extend([
            '--user-agent', 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1',
            '--geo-bypass',
            url
        ])
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"DEBUG_ERROR: {result.stderr}")
            return jsonify({"status": "error", "message": "解析失败，请检查链接有效性"}), 200
            
        info = json.loads(result.stdout)
        # 返回格式化数据，供前端选择分辨率
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
    
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1'}
    
    # 简单的 Referer 伪装，针对常见平台
    if 'x.com' in video_url: headers['Referer'] = 'https://x.com/'
    elif 'tiktok.com' in video_url: headers['Referer'] = 'https://www.tiktok.com/'
    elif 'douyin.com' in video_url: headers['Referer'] = 'https://www.douyin.com/'
    elif 'youtube.com' in video_url: headers['Referer'] = 'https://www.youtube.com/'
        
    try:
        r = requests.get(video_url, headers=headers, stream=True, timeout=20)
        return Response(stream_with_context(r.iter_content(chunk_size=1024)), 
                        content_type=r.headers.get('Content-Type', 'video/mp4'))
    except Exception as e:
        return f"Proxy failed: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
