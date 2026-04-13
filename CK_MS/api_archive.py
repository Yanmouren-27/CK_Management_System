"""
api_archive.py — 日志归档 API
===============================
支持按时间段将订单记录归档，归档后原记录从 orders 表移除
"""

import json
from flask import Blueprint, request, jsonify
from .db import query, execute, get_db

bp = Blueprint("archive", __name__, url_prefix="/api/archives")


@bp.post("")
def create_archive():
    """
    创建归档
    请求体: { "start_date": "2024-01-01", "end_date": "2024-01-31", "label": "一月归档" }
    """
    d = request.json
    start, end = d["start_date"], d["end_date"]
    label = d.get("label") or f"归档 {start} ~ {end}"

    # 查找要归档的订单
    orders = query(
        """SELECT * FROM orders
           WHERE created_at >= ? AND created_at <= ? || ' 23:59:59'
           ORDER BY created_at""",
        (start, end),
    )
    if not orders:
        return jsonify({"error": "该时间段内无订单记录"}), 400

    # 为每个订单附加明细
    for order in orders:
        order["items"] = query(
            "SELECT * FROM order_items WHERE order_id=?", (order["id"],)
        )
        try:
            order["notes"] = json.loads(order["notes"]) if order["notes"] else []
        except (json.JSONDecodeError, TypeError):
            order["notes"] = []

    # 统计
    sale_count = sum(1 for o in orders if o["type"] == "sale")
    internal_count = sum(1 for o in orders if o["type"] == "internal")
    total_revenue = sum(o.get("drink_price", 0) or 0 for o in orders if o["type"] == "sale")
    total_cost = sum(o.get("total_material_cost", 0) or 0 for o in orders)

    with get_db() as conn:
        # 写入归档
        cur = conn.execute(
            """INSERT INTO archives
               (label, start_date, end_date, order_count,
                sale_count, internal_count, total_revenue, total_cost, snapshot)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                label, start, end, len(orders),
                sale_count, internal_count,
                round(total_revenue, 2), round(total_cost, 2),
                json.dumps(orders, ensure_ascii=False, default=str),
            ),
        )
        archive_id = cur.lastrowid

        # 删除已归档订单及其明细（CASCADE 会删 order_items）
        order_ids = [o["id"] for o in orders]
        placeholders = ",".join("?" * len(order_ids))
        conn.execute(f"DELETE FROM orders WHERE id IN ({placeholders})", order_ids)

    return jsonify({
        "id": archive_id,
        "label": label,
        "order_count": len(orders),
        "sale_count": sale_count,
        "internal_count": internal_count,
    }), 201


@bp.get("")
def list_archives():
    """归档列表（不含快照数据）"""
    rows = query(
        """SELECT id, label, start_date, end_date,
                  order_count, sale_count, internal_count,
                  total_revenue, total_cost, created_at
           FROM archives ORDER BY created_at DESC"""
    )
    return jsonify(rows)


@bp.get("/<int:aid>")
def get_archive(aid):
    """归档详情（含完整快照）"""
    arch = query("SELECT * FROM archives WHERE id=?", (aid,), one=True)
    if not arch:
        return jsonify({"error": "归档不存在"}), 404
    try:
        arch["snapshot"] = json.loads(arch["snapshot"])
    except (json.JSONDecodeError, TypeError):
        arch["snapshot"] = []
    return jsonify(arch)
