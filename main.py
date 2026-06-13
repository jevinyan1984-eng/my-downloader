import os
import json
import subprocess
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
# 仅允许你的域名访问
CORS(app, resources={r"/*": {"origins": "https://video-downloader.youtube.kdns.fr"}})

@app.route('/download', methods=['POST', 'OPTIONS'])
def download():
    if request.method == 'OPTIONS': return '', 200
    
    # 强制来源校验
    referer = request.headers.get('Referer', '')
    if "video-downloader.youtube.kdns.fr" not in referer:
        return jsonify({"status": "error", "message": "非法调用"}), 403

    data = request.json
    url = data.get('url', '').split('?')[0] # 清理掉 URL 参数
    if not url: return jsonify({"status": "error", "message": "请输入链接"}), 400
    
    # Twitter 专属解析命令
    cmd = [
        'yt-dlp', '--dump-json', '--no-warnings', '--no-playlist',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        '--referer', 'https://twitter.com/',
        '--cookies', 'twitter_cookies.txt',
        url
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        return jsonify({"status": "error", "message": "解析失败，请检查链接或 Cookie"}), 200
        
    try:
        info = json.loads(result.stdout)
        # 获取所有 mp4 格式，并按分辨率从高到低排序
        formats = [
            {"url": f["url"], "res": f"{f.get('width')}x{f.get('height')}", "note": f.get("format_note", "高清")}
            for f in info.get("formats", []) if f.get("ext") == "mp4" and f.get("url")
        ]
        formats.sort(key=lambda x: int(x["url"].split("?")[0].split("/")[-2].split("x")[0]) if "x" in x["url"] else 0, reverse=True)
        
        return jsonify({
            "status": "success",
            "title": info.get("title", "Twitter 视频"),
            "thumbnail": info.get("thumbnail", ""),
            "formats": formats[:3] # 取前3种最高画质
        })
    except:
        return jsonify({"status": "error", "message": "数据解析异常"}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
