from flask import Flask, request, jsonify
from flask_cors import CORS  # 导入 CORS
import subprocess
import os

app = Flask(__name__)
CORS(app)  # 关键！启用 CORS

@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    try:
        # 获取视频直链
        result = subprocess.check_output(['yt-dlp', '--get-url', url], stderr=subprocess.STDOUT)
        return jsonify({"video_url": result.decode().strip()})
    except subprocess.CalledProcessError as e:
        return jsonify({"error": str(e.output.decode())}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))
