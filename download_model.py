#!/usr/bin/env python3
"""
下载 PP-DocLayoutV2 模型到本地目录
支持从 ModelScope 下载模型文件
"""

import os
import sys
from pathlib import Path

MODEL_DIR = Path(__file__).parent / "PP-DocLayoutV2"
MODEL_ID = "PaddlePaddle/PP-DocLayoutV2"


def download_with_modelscope():
    """使用 modelscope SDK 下载模型"""
    try:
        from modelscope import snapshot_download
        print(f"[Download] 从 ModelScope 下载模型: {MODEL_ID}")
        print(f"[Download] 目标目录: {MODEL_DIR}")

        model_path = snapshot_download(
            MODEL_ID,
            cache_dir=str(MODEL_DIR.parent),
            revision="master"
        )
        print(f"[Download] 模型下载完成: {model_path}")

        # 如果模型下载到其他位置，创建符号链接或复制
        if Path(model_path) != MODEL_DIR:
            import shutil
            if MODEL_DIR.exists():
                shutil.rmtree(MODEL_DIR)
            shutil.move(model_path, MODEL_DIR)
            print(f"[Download] 模型已移动到: {MODEL_DIR}")

        return True
    except ImportError:
        print("[Warning] modelscope 未安装，尝试使用 pip 安装...")
        return False
    except Exception as e:
        print(f"[Error] ModelScope 下载失败: {e}")
        return False


def download_with_huggingface():
    """使用 huggingface_hub 下载模型"""
    try:
        from huggingface_hub import snapshot_download as hf_download
        print(f"[Download] 尝试从 HuggingFace 下载模型...")
        # ModelScope 模型可能在 HF 上有镜像
        model_path = hf_download(
            MODEL_ID,
            local_dir=str(MODEL_DIR),
            local_dir_use_symlinks=False
        )
        print(f"[Download] 模型下载完成: {model_path}")
        return True
    except ImportError:
        print("[Warning] huggingface_hub 未安装")
        return False
    except Exception as e:
        print(f"[Error] HuggingFace 下载失败: {e}")
        return False


def download_with_paddleocr():
    """使用 PaddleOCR 内置下载机制"""
    try:
        from paddleocr import PaddleOCRVL

        print("[Download] 使用 PaddleOCR 初始化下载模型...")
        # 初始化时会自动下载模型
        _ = PaddleOCRVL(
            layout_detection_model_name="PP-DocLayoutV2",
            layout_detection_model_dir=str(MODEL_DIR),
            device="cpu",
        )
        print("[Download] 模型下载完成")
        return True
    except Exception as e:
        print(f"[Error] PaddleOCR 下载失败: {e}")
        return False


def main():
    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    # 检查模型是否已存在
    if list(MODEL_DIR.glob("*.pdmodel")) or list(MODEL_DIR.glob("*.json")):
        print(f"[Info] 模型目录已存在文件: {MODEL_DIR}")
        print("[Info] 如需重新下载，请先删除该目录")
        return 0

    print("=" * 60)
    print("PP-DocLayoutV2 模型下载工具")
    print("=" * 60)

    # 尝试不同的下载方式
    success = False

    # 优先使用 ModelScope（国内更稳定）
    if not success:
        print("\n[1/3] 尝试 ModelScope SDK...")
        success = download_with_modelscope()

    # 备选：HuggingFace
    if not success:
        print("\n[2/3] 尝试 HuggingFace Hub...")
        success = download_with_huggingface()

    # 最后：PaddleOCR 自动下载
    if not success:
        print("\n[3/3] 尝试 PaddleOCR 内置下载...")
        success = download_with_paddleocr()

    if success:
        print("\n" + "=" * 60)
        print("[Success] 模型下载完成!")
        print(f"[Success] 模型目录: {MODEL_DIR}")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("[Failed] 所有下载方式均失败")
        print("[Help] 请尝试手动安装依赖并运行:")
        print("       pip install modelscope")
        print(f"       python {__file__}")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    sys.exit(main())