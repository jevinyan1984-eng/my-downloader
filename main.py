from flask import Flask, request, jsonify
from flask_cors import CORS
import subprocess
import os
import json

# 1. 必须先创建 app 对象
app = Flask(__name__)
CORS(app) 

# 2. 现在才能使用 @app.route
@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    
    try:
        # 使用 subprocess.run 代替 check_output
        result = subprocess.run(
            ['yt-dlp', '--dump-json', '--no-warnings', url], 
            capture_output=True, text=True
        )
        
        if result.returncode != 0:
            return jsonify({"status": "error", "message": f"yt-dlp错误: {result.stderr}"}), 200
            
        info = json.loads(result.stdout)
        return jsonify({
            "status": "success",
            "title": info.get("title", "无标题"),
            "thumbnail": info.get("thumbnail", ""),
            "formats": [{"url": f.get("url"), "note": f.get("format_note", "高清")} 
                        for f in info.get("formats", []) if f.get("vcodec") != "none"]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": f"程序异常: {str(e)}"}), 200

@app.route('/', methods=['GET'])
def index():
    return "API is running."

# 3. 最后运行应用
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
