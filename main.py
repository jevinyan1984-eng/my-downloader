from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import subprocess
import os
import json
import requests

app = Flask(__name__)

# 配置：设置你最终的部署域名
# 注意：不需要带 'https://'，只需域名部分即可
ALLOWED_DOMAIN = "video-downloader.youtube.kdns.fr"

# 1. 设置跨域白名单：只允许你这个域名发起 AJAX 请求
CORS(app, origins=[f"https://{ALLOWED_DOMAIN}"])

@app.route('/', methods=['GET'])
def home():
    return "怡烨科技 Twitter 解析服务运行中!", 200

# 校验函数：双重保险
def is_valid_request():
    referer = request.headers.get('Referer', '')
    
    # 打印日志到 Render Logs，解决你看不到请求来源的问题
    print(f"DEBUG: Checking Referer: {referer}") 
    
    # 逻辑：只要 Referer 字符串里包含了你的域名就通过
    if ALLOWED_DOMAIN in referer:
        return True
        
    return False

@app.route('/download', methods=['POST'])
def download():
    # 2. 如果 Referer 不匹配，直接返回 403 Forbidden
    if not is_valid_request():
        return jsonify({"status": "error", "message": "Access Denied: Origin not allowed"}), 403
        
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"status": "error", "message": "URL missing"}), 400
    
    try:
        cmd = ['yt-dlp', '--dump-json', '--no-warnings', url]
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"DEBUG: yt-dlp error: {result.stderr}")
            return jsonify({"status": "error", "message": "解析失败，推特视频链接不正确"}), 200
            
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
    # 利用代理解决 Twitter 视频链接的 403 问题
    video_url = request.args.get('url')
    if not video_url: return "No URL", 400
    
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://x.com/'}
    r = requests.get(video_url, headers=headers, stream=True)
    return Response(stream_with_context(r.iter_content(chunk_size=1024)), 
                    content_type=r.headers.get('Content-Type', 'video/mp4'))

if __name__ == '__main__':
    # 确保在 Render 上正确绑定端口
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
