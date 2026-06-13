from flask import Flask, request, jsonify
from flask_cors import CORS # 加上这个来解决跨域
import subprocess
import os
import json

app = Flask(__name__)
CORS(app) # 临时允许所有跨域，先跑通再说

@app.route('/download', methods=['POST'])
def download():
    try:
        url = request.json.get('url')
        # 使用 --dump-json 获取完整信息，这比 --get-url 稳定得多
        result = subprocess.check_output(['yt-dlp', '--dump-json', url], stderr=subprocess.STDOUT)
        data = json.loads(result.decode())
        
        # 只提取我们需要的信息
        return jsonify({
            "status": "success",
            "video_url": data.get("url"), # 适配旧逻辑
            "title": data.get("title", "未知标题")
        })
    except Exception as e:
        # 如果解析失败，不让后端崩掉，返回错误消息
        return jsonify({"status": "error", "message": str(e)}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
