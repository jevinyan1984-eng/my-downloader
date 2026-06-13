import os
import json
import subprocess
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS
import requests

app = Flask(__name__)
# 彻底开放跨域，解决请求被拦截问题
CORS(app, resources={r"/*": {"origins": "*"}})

# --- Cookie 自动生成逻辑 ---
def setup_cookies():
    yt_content = os.environ.get('YOUTUBE_COOKIES')
    dy_content = os.environ.get('DOUYIN_COOKIES')
    
    if yt_content:
        with open('youtube_cookies.txt', 'w', encoding='utf-8') as f:
            f.write(yt_content)
        # 调试：验证文件写入
        if os.path.exists('youtube_cookies.txt'):
            print(f"DEBUG: YouTube cookies generated. Size: {os.path.getsize('youtube_cookies.txt')} bytes")
    
    if dy_content:
        with open('douyin_cookies.txt', 'w', encoding='utf-8') as f:
            f.write(dy_content)
        print("DEBUG: Douyin cookies generated.")

# 程序启动时执行
setup_cookies()

@app.route('/', methods=['GET'])
def home():
    return "怡烨科技 解析服务运行正常", 200

@app.route('/download', methods=['POST', 'OPTIONS'])
def download():
    # 处理 CORS 预检请求
    if request.method == 'OPTIONS':
        return '', 200
        
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"status": "error", "message": "URL missing"}), 400
    
    try:
        # 构建 yt-dlp 命令
        cmd = ['yt-dlp', '--dump-json', '--no-warnings', '--no-playlist', '--verbose']
        
        # 匹配 Cookie
        if 'douyin.com' in url or 'tiktok.com' in url:
            if os.path.exists('douyin_cookies.txt'):
                cmd.extend(['--cookies', 'douyin_cookies.txt'])
        else:
            if os.path.exists('youtube_cookies.txt'):
                cmd.extend(['--cookies', 'youtube_cookies.txt'])
            
        cmd.extend([
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            '--geo-bypass',
            url
        ])
        
        # 执行
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"DEBUG_ERROR_STDERR: {result.stderr}")
            return jsonify({"status": "error", "message": "解析失败，请检查 Render 后端日志"}), 200
            
        info = json.loads(result.stdout)
        
        # 处理结果并返回
        return jsonify({
            "status": "success",
            "title": info.get("title", "无标题"),
            "thumbnail": info.get("thumbnail", ""),
            "formats": [{"url": f.get("url"), "note": f.get("format_note", "高清")} 
                        for f in info.get("formats", []) if f.get("vcodec") != "none"]
        })
        
    except Exception as e:
        print(f"DEBUG_EXCEPTION: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
