"""
api_stats.py — 统计数据 API
=============================
为管理面板提供聚合统计数据
"""

import json
from flask import Blueprint, request, jsonify
from .db import query

bp = Blueprint("stats", __name__, url_prefix="/api/stats")


@bp.get("")
def get_stats():
    """
    获取统计数据
    参数: from=2024-01-01, to=2024-12-31（可选，默认全部）
    """
    conditions, params = [], []
    if f := request.args.get("from"):
        conditions.append("created_at >= ?")
        params.append(f)
    if t := request.args.get("to"):
        conditions.append("created_at <= ? || ' 23:59:59'")
        params.append(t)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""

    # 基础聚合
    summary = query(
        f"""SELECT
                COUNT(*)                                             AS total_orders,
                SUM(CASE WHEN type='sale' THEN 1 ELSE 0 END)        AS sale_count,
                SUM(CASE WHEN type='internal' THEN 1 ELSE 0 END)    AS internal_count,
                COALESCE(SUM(CASE WHEN type='sale' THEN drink_price ELSE 0 END), 0)   AS total_revenue,
                COALESCE(SUM(CASE WHEN type='sale' THEN total_material_cost ELSE 0 END), 0)     AS sale_cost,
                COALESCE(SUM(CASE WHEN type='internal' THEN total_material_cost ELSE 0 END), 0) AS internal_cost
            FROM orders {where}""",
        tuple(params),
        one=True,
    )

    # 饮品销量排行（仅 sale 类型）
    sale_conditions = list(conditions) + ["type='sale'", "drink_name IS NOT NULL"]
    sale_where = "WHERE " + " AND ".join(sale_conditions)
    ranking = query(
        f"""SELECT drink_name, COUNT(*) AS count, SUM(drink_price) AS revenue
            FROM orders {sale_where}
            GROUP BY drink_name ORDER BY count DESC LIMIT 10""",
        tuple(params),
    )

    # 原材料消耗明细（按品类分 sale/internal）
    item_conditions = []
    item_params = []
    if f := request.args.get("from"):
        item_conditions.append("o.created_at >= ?")
        item_params.append(f)
    if t := request.args.get("to"):
        item_conditions.append("o.created_at <= ? || ' 23:59:59'")
        item_params.append(t)

    item_where = ("WHERE " + " AND ".join(item_conditions)) if item_conditions else ""
    material_usage = query(
        f"""SELECT
                oi.material_name, oi.variant_name, oi.unit,
                SUM(CASE WHEN o.type='sale'     THEN oi.amount ELSE 0 END) AS sale_usage,
                SUM(CASE WHEN o.type='internal'  THEN oi.amount ELSE 0 END) AS internal_usage,
                SUM(oi.unit_cost) AS total_cost
            FROM order_items oi
            JOIN orders o ON oi.order_id = o.id
            {item_where}
            GROUP BY oi.material_name, oi.variant_name
            ORDER BY total_cost DESC""",
        tuple(item_params),
    )

    # 操作人统计
    op_stats = query(
        f"""SELECT operator_name, COUNT(*) AS count
            FROM orders {where}
            GROUP BY operator_name ORDER BY count DESC""",
        tuple(params),
    )

    return jsonify({
        "summary": summary,
        "drink_ranking": ranking,
        "material_usage": material_usage,
        "operator_stats": op_stats,
    })
