#!/usr/bin/env python3
"""
Coffee Club Management System — 启动脚本
==========================================
用法: python run.py [--port 5000] [--host 0.0.0.0]

启动后在浏览器访问 http://localhost:5000
"""

import argparse
import os
import sys

# Allow running with "python run.py" from CK_MS directory.
if __package__ is None or __package__ == "":
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

from CK_MS.app import create_app


def main():
    parser = argparse.ArgumentParser(description="咖啡社团管理系统")
    parser.add_argument("--host", default="0.0.0.0", help="监听地址 (默认 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="端口 (默认 5000)")
    parser.add_argument("--debug", action="store_true", help="调试模式")
    args = parser.parse_args()

    app = create_app()
    print(f"\n  ☕ 咖啡社团管理系统已启动")
    print(f"  📡 访问地址: http://localhost:{args.port}")
    print(f"  📂 数据库位置: data/coffee_club.db\n")

    app.run(host=args.host, port=args.port, debug=args.debug)


if __name__ == "__main__":
    main()
