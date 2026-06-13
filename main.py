@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    
    try:
        # 确保 yt-dlp 命令正确
        result = subprocess.check_output(['yt-dlp', '--dump-json', url], stderr=subprocess.STDOUT)
        info = json.loads(result.decode())
        
        response_data = {
            "status": "success",
            "title": info.get("title", "未知标题"),
            "thumbnail": info.get("thumbnail", ""),
            "formats": [{"url": f.get("url"), "note": f.get("format_note", "默认")} 
                        for f in info.get("formats", []) if f.get("vcodec") != "none"]
        }
        return jsonify(response_data)
    except Exception as e:
        # 这里是关键：即使失败，也要返回 200 OK 并带上错误信息，不要崩溃
        return jsonify({"status": "error", "message": str(e)}), 200
