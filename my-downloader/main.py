from flask import Flask, request, jsonify
import subprocess
import os

app = Flask(__name__)

@app.route('/download', methods=['POST'])
def download():
    url = request.json.get('url')
    # 调用 yt-dlp 获取视频直链 (不下载到服务器磁盘，防止空间耗尽)
    result = subprocess.check_output(['yt-dlp', '--get-url', url])
    return jsonify({"video_url": result.decode().strip()})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))