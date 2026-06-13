from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import subprocess
import os
import json
import requests

app = Flask(__name__)

# 配置区域
ALLOWED_DOMAIN = "videodownloader-bip.pages.dev"
# 设置为 True 后，POSTman 等工具可以直接测试，无需 Referer
DEBUG_MODE = False 

CORS(app, resources={r"/*": {"origins": "*"}})

@app.route('/', methods=['GET'])
def home():
    return "API is running!", 200

def is_valid_request():
    # 调试模式直接放行
    if DEBUG_MODE:
        return True
        
    referer = request.headers.get('Referer', '')
    # 打印日志到 Render Logs，解决你看不到请求来源的问题
    print(f"DEBUG: Checking Referer: {referer}") 
    
    # 智能匹配：只要 referer 字符串里包含了你的域名就通过
    if ALLOWED_DOMAIN in referer:
        return True
        
    return False

@app.route('/download', methods=['POST'])
def download():
    if not is_valid_request():
        return jsonify({"status": "error", "message": "Access Denied: Referer invalid"}), 403
        
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"status": "error", "message": "URL missing"}), 400
    
    try:
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
    # 这里也可以增加校验，如果发现下载被盗链，可以加回 is_valid_request()
    video_url = request.args.get('url')
    if not video_url: return "No URL", 400
    
    headers = {'User-Agent': 'Mozilla/5.0', 'Referer': 'https://x.com/'}
    r = requests.get(video_url, headers=headers, stream=True)
    return Response(stream_with_context(r.iter_content(chunk_size=1024)), 
                    content_type=r.headers.get('Content-Type', 'video/mp4'))

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
