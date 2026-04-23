"""
PaddleOCR-VL Flask API
- 版面检测: 本地 PP-DocLayoutV2
- 文字识别: vLLM 远程服务器
"""

import os
import io
import json
import time
import base64
import tempfile
from flask import Flask, request, jsonify
from werkzeug.utils import secure_filename
from paddleocr import PaddleOCRVL

app = Flask(__name__)

# 配置 (支持环境变量覆盖)
VL_REC_SERVER_URL = os.environ.get("VL_REC_SERVER_URL", "http://10.11.163.100:16101/v1")
VL_REC_API_KEY = os.environ.get("VL_REC_API_KEY", "sk-r3zC3KPb2M3NVMaduSrsjBdppFVWIqwEe6qH0QqOM6HgQ7eY")
VL_REC_API_MODEL_NAME = os.environ.get("VL_REC_API_MODEL_NAME", "PaddleOCR-VL-0.9B")
DOCLAYOUT_MODEL_DIR = os.environ.get("DOCLAYOUT_MODEL_DIR", "./PP-DocLayoutV2")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

# 全局 pipeline 单例
_pipeline = None


def get_pipeline():
    """获取或初始化 OCR pipeline"""
    global _pipeline
    if _pipeline is None:
        print("[Init] 初始化 PaddleOCRVL pipeline...")
        print(f"[Init] VL_REC_SERVER_URL: {VL_REC_SERVER_URL}")
        print(f"[Init] VL_REC_API_KEY: {VL_REC_API_KEY[:10]}...")
        print(f"[Init] VL_REC_API_MODEL_NAME: {VL_REC_API_MODEL_NAME}")
        print(f"[Init] DOCLAYOUT_MODEL_DIR: {DOCLAYOUT_MODEL_DIR}")
        _pipeline = PaddleOCRVL(
            vl_rec_backend="vllm-server",
            vl_rec_server_url=VL_REC_SERVER_URL,
            vl_rec_api_key=VL_REC_API_KEY,
            vl_rec_api_model_name=VL_REC_API_MODEL_NAME,
            layout_detection_model_name="PP-DocLayoutV2",
            layout_detection_model_dir=DOCLAYOUT_MODEL_DIR,
            device="cpu",
        )
        print("[Init] Pipeline 初始化完成")
    return _pipeline


def allowed_file(filename):
    """检查文件扩展名"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/health", methods=["GET"])
def health():
    """健康检查"""
    return jsonify({
        "status": "ok",
        "service": "PaddleOCR-VL API",
        "vllm": VL_REC_SERVER_URL,
        "model": VL_REC_API_MODEL_NAME,
    })


@app.route("/ocr", methods=["POST"])
def ocr():
    """
    OCR 接口

    Form 参数:
        - file: 图片文件 (png/jpg/jpeg)
        - format: 返回格式，可选 json/md/both (默认 both)

    返回:
        - json: {"success": true, "json": {...}, "time": 0.0}
        - md: {"success": true, "md": "...", "time": 0.0}
        - both: {"success": true, "json": {...}, "md": "...", "time": 0.0}
    """
    # 检查文件
    if "file" not in request.files:
        return jsonify({"success": False, "error": "No file provided"}), 400

    file = request.files["file"]
    if not file.filename or not allowed_file(file.filename):
        return jsonify({"success": False, "error": "Invalid file type"}), 400

    # 获取格式参数
    fmt = request.form.get("format", "both").lower()
    if fmt not in ("json", "md", "both"):
        fmt = "both"

    filename = secure_filename(file.filename)
    start_time = time.time()

    try:
        # 保存临时文件
        ext = filename.rsplit(".", 1)[1].lower()
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=False) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name

        # OCR 处理
        pipeline = get_pipeline()
        results = list(pipeline.predict(tmp_path))

        # 清理临时文件
        try:
            os.unlink(tmp_path)
        except:
            pass

        if not results:
            return jsonify({"success": False, "error": "No results"}), 500

        result = results[0]
        processing_time = time.time() - start_time

        # 构造响应
        response = {
            "success": True,
            "filename": filename,
            "time": round(processing_time, 2),
        }

        if fmt in ("json", "both"):
            response["json"] = result.json.get("res", result.json)

        if fmt in ("md", "both"):
            md_data = result.markdown
            response["md"] = md_data.get("markdown_texts", md_data)

        return jsonify(response)

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    print("=" * 50)
    print("PaddleOCR-VL API Server")
    print(f"URL: http://0.0.0.0:5000/ocr")
    print("=" * 50)

    # 预热 pipeline
    get_pipeline()

    port = int(os.environ.get("PORT", 5001))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
