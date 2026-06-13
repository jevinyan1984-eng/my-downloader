import os
import json
import subprocess
import requests
from flask import Flask, request, jsonify, Response, stream_with_context
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# --- Cookie 自动生成逻辑 ---
def setup_cookies():
    yt_content = os.environ.get('YOUTUBE_COOKIES')
    dy_content = os.environ.get('DOUYIN_COOKIES')
    
    if yt_content:
        with open('youtube_cookies.txt', 'w', encoding='utf-8') as f:
            f.write(yt_content)
        print("DEBUG: YouTube cookies file generated.")
    if dy_content:
        with open('douyin_cookies.txt', 'w', encoding='utf-8') as f:
            f.write(dy_content)
        print("DEBUG: Douyin cookies file generated.")

# 启动时初始化
setup_cookies()

@app.route('/', methods=['GET'])
def home():
    return "怡烨科技 解析服务运行正常", 200

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"status": "error", "message": "URL missing"}), 400
    
    try:
        # 构建 yt-dlp 命令，加入 --verbose 以获取最详细的报错
        cmd = ['yt-dlp', '--dump-json', '--no-warnings', '--no-playlist', '--verbose']
        
        # 智能匹配 Cookie
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
        
        # 执行命令并捕获输出
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # 详细报错排查逻辑
        if result.returncode != 0:
            # 将错误详细信息写入日志
            print(f"DEBUG_ERROR_STDERR: {result.stderr}")
            print(f"DEBUG_ERROR_STDOUT: {result.stdout}")
            return jsonify({"status": "error", "message": f"解析失败: 请查看后端日志"}), 200
            
        if not result.stdout:
            return jsonify({"status": "error", "message": "解析结果为空，请确认链接是否有效"}), 200
            
        info = json.loads(result.stdout)
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

@app.route('/proxy_download')
def proxy_download():
    video_url = request.args.get('url')
    if not video_url: return "No URL", 400
    
    # 简单的流代理，仅限非 YouTube 平台使用
    try:
        r = requests.get(video_url, stream=True, timeout=10)
        return Response(stream_with_context(r.iter_content(chunk_size=1024)), 
                        content_type=r.headers.get('Content-Type', 'video/mp4'))
    except Exception as e:
        return f"Proxy failed: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
