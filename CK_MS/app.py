"""
app.py — Flask 应用入口
========================
职责：创建 Flask 实例、注册蓝图、CORS、静态文件服务
"""

import os
from flask import Flask, send_from_directory
from .db import init_db
from . import api_menu, api_order, api_staff, api_inventory, api_stats, api_archive

FRONTEND_DIR = os.path.dirname(__file__)


def create_app():
    app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path="")

    # ── CORS（开发时允许跨域） ──
    @app.after_request
    def add_cors(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return response

    # ── 注册 API 蓝图 ──
    app.register_blueprint(api_menu.bp)       # /api/menu/*
    app.register_blueprint(api_order.bp)      # /api/orders/*
    app.register_blueprint(api_staff.bp)      # /api/staff/*
    app.register_blueprint(api_inventory.bp)  # /api/inventory/*
    app.register_blueprint(api_stats.bp)      # /api/stats/*
    app.register_blueprint(api_archive.bp)    # /api/archives/*

    # ── 前端静态文件服务 ──
    @app.route("/")
    def serve_index():
        return send_from_directory(FRONTEND_DIR, "index.html")

    # ── 初始化数据库 ──
    init_db()

    return app
