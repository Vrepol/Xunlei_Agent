# backend/app.py

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import os

from download import start_download
from file_tools import (
    preview_subfolders,
    move_files_with_keyword_in_subfolder,
    rename_files,
    delete_empty_folders_with_keyword
)

app = Flask(__name__, static_folder='../frontend', static_url_path='')
CORS(app)  # 允许跨域访问，方便前端在本地调试

# ---------- 1) 提供静态页面 ----------

@app.route('/')
def serve_index():
    # 把 frontend/index.html 作为首页
    return send_from_directory(app.static_folder, 'index.html')

# 若你前端还有其他静态资源（css/js），Flask 会自动从 static_folder 下读取


# ---------- 2) API: 批量磁力下载 ----------

@app.route('/api/download', methods=['POST'])
def api_download():
    """
    请求示例 (JSON):
    {
      "magnet_links": ["magnet:?xt=urn:btih:xxxx...", ...],
      "server_addr": "http://IP:Port"
    }
    返回：
    {
      "success": true,
      "logs": ["[1] 开始处理: ...", "...", "..."]
    }
    """
    data = request.get_json(force=True)
    magnet_links = data.get("magnet_links", [])
    server_addr = data.get("server_addr", "").strip()

    if not magnet_links or not isinstance(magnet_links, list):
        return jsonify({"success": False, "error": "magnet_links 必须是非空列表"}), 400
    if not server_addr:
        return jsonify({"success": False, "error": "server_addr 不能为空"}), 400

    try:
        logs_str = start_download(magnet_links, server_addr, headless=True)
        # 后端返回日志时，可把字符串按行拆成列表
        logs = logs_str.split("\n")
        return jsonify({"success": True, "logs": logs})
    except Exception as e:
        return jsonify({"success": False, "error": f"执行失败: {e}"}), 500


# ---------- 3) API: 预览子文件夹 ----------

@app.route('/api/list_subfolders', methods=['GET', 'POST'])
def api_list_subfolders():
    """
    GET 请求示例: /api/list_subfolders?root_folder=/path/to/xxx
    或者 POST JSON: { "root_folder": "/path/to/xxx" }
    返回：
    {
      "success": true,
      "subfolders": ["子文件夹1", "子文件夹2", ...]
    }
    """
    if request.method == 'GET':
        root_folder = request.args.get("root_folder", "").strip()
    else:
        body = request.get_json(force=True)
        root_folder = body.get("root_folder", "").strip()

    if not root_folder:
        return jsonify({"success": False, "error": "root_folder 不能为空"}), 400

    try:
        subs = preview_subfolders(root_folder)
        return jsonify({"success": True, "subfolders": subs})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------- 4) API: 按关键字移动文件 ----------

@app.route('/api/move_files', methods=['POST'])
def api_move_files():
    """
    POST JSON 示例:
    {
      "root_folder": "/DataBase/downloads",
      "keyword": "Key",
      "target_folder": "/DataBase/电视剧/Name",
      "create_if_not_exists": true,
      "recursive": false,
      "preview": true
    }
    返回：
    {
      "success": true,
      "logs": ["[预览] ...", "...", ...]
    }
    """
    data = request.get_json(force=True)
    root_folder = data.get("root_folder", "").strip()
    keyword = data.get("keyword", "").strip()
    target_folder = data.get("target_folder", "").strip()
    create_if_not_exists = data.get("create_if_not_exists", True)
    recursive = data.get("recursive", False)
    preview = data.get("preview", True)

    if not root_folder or not keyword or not target_folder:
        return jsonify({"success": False, "error": "root_folder, keyword, target_folder 均不能为空"}), 400

    try:
        logs = move_files_with_keyword_in_subfolder(
            root_folder=root_folder,
            keyword=keyword,
            target_folder=target_folder,
            create_if_not_exists=create_if_not_exists,
            recursive=recursive,
            preview=preview
        )
        return jsonify({"success": True, "logs": logs})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------- 5) API: 批量重命名 ----------

@app.route('/api/rename_files', methods=['POST'])
def api_rename_files():
    """
    POST JSON 示例:
    {
      "folder_path": "/DataBase/电视剧/Name",
      "prefix": "Name - S0E",
      "custom_pattern": "E(\\d+) ",
      "preview": true
    }
    返回：
    {
      "success": true,
      "logs": ["重命名前缀: ...", "...", ...]
    }
    """
    data = request.get_json(force=True)
    folder_path = data.get("folder_path", "").strip()
    prefix = data.get("prefix", "NewFile_").strip()
    custom_pattern = data.get("custom_pattern", "").strip()
    preview = data.get("preview", True)

    if not folder_path:
        return jsonify({"success": False, "error": "folder_path 不能为空"}), 400

    try:
        logs = rename_files(
            folder_path=folder_path,
            prefix=prefix,
            preview=preview,
            custom_pattern=custom_pattern
        )
        return jsonify({"success": True, "logs": logs})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------- 6) API: 删除空文件夹 ----------

@app.route('/api/delete_empty_folders', methods=['POST'])
def api_delete_empty_folders():
    """
    POST JSON 示例:
    {
      "root_folder": "/DataBase/downloads",
      "keyword": "Key",
      "recursive": false,
      "preview": true
    }
    返回：
    {
      "success": true,
      "logs": ["[预览] 删除: ...", "..."]
    }
    """
    data = request.get_json(force=True)
    root_folder = data.get("root_folder", "").strip()
    keyword = data.get("keyword", "").strip()
    recursive = data.get("recursive", False)
    preview = data.get("preview", True)

    if not root_folder or not keyword:
        return jsonify({"success": False, "error": "root_folder, keyword 均不能为空"}), 400

    try:
        logs = delete_empty_folders_with_keyword(
            root_folder=root_folder,
            keyword=keyword,
            recursive=recursive,
            preview=preview
        )
        return jsonify({"success": True, "logs": logs})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ---------- 7) 启动应用 ----------

if __name__ == '__main__':
    # 监听 5000 端口，可按需改成 7861 或其他
    app.run(host='0.0.0.0', port=5000, debug=True)
