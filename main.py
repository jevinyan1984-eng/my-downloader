@app.route('/download', methods=['POST'])
def download():
    data = request.json
    url = data.get('url')
    
    try:
        # 使用 subprocess.run 代替 check_output，并捕获 stderr
        # 这能保证我们能拿到真正的错误原因
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
