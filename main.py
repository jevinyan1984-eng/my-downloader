from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import json

app = Flask(__name__)
CORS(app, origins=["https://jevinyan1984-eng.github.io"])

@app.route('/download', methods=['POST'])
def download():
    referer = request.headers.get('Referer', '')
    if 'jevinyan1984-eng.github.io' not in referer:
        return jsonify({"error": "Unauthorized"}), 403
    
    data = request.json
    url = data.get('url')
    if not url:
        return jsonify({"error": "No URL"}), 400

    try:
        # 使用 dump-json 获取详细信息
        result = subprocess.check_output(['yt-dlp', '--dump-json', url], stderr=subprocess.STDOUT)
        info = json.loads(result.decode())
        
        response_data = {
            "title": info.get("title"),
            "thumbnail": info.get("thumbnail"),
            "formats": [{"url": f.get("url"), "note": f.get("format_note")} 
                        for f in info.get("formats", []) if f.get("vcodec") != "none"]
        }
        return jsonify(response_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def index():
    return "API is running."

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
