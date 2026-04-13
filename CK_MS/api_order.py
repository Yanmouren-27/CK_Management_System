"""
api_order.py — 订单 API
========================
处理售卖(sale)与内部消耗(internal)的下单逻辑
下单时自动扣减对应品类库存
"""

import json
from flask import Blueprint, request, jsonify
from .db import query, execute, get_db

bp = Blueprint("order", __name__, url_prefix="/api/orders")


@bp.post("")
def create_order():
    """
    创建订单
    请求体:
    {
        "type": "sale" | "internal",
        "mode": "drink" | "custom",
        "drink_id": 1,           // 可选（drink 模式）
        "drink_name": "拿铁",
        "drink_price": 24,
        "operator_id": 1,
        "operator_name": "小王",
        "notes": ["加冰", "少糖"],
        "items": [
            {"material_id": 1, "material_name": "咖啡豆",
             "variant_id": 1, "variant_name": "哥伦比亚",
             "amount": 18, "unit": "g"}
        ]
    }
    """
    d = request.json

    # 计算每行成本 & 总成本
    items = d.get("items", [])
    total_cost = 0
    for item in items:
        variant = query("SELECT * FROM variants WHERE id=?", (item["variant_id"],), one=True)
        if variant:
            item["unit_cost"] = round((variant["price_per_kg"] / 1000) * item["amount"], 4)
            item["unit"] = item.get("unit") or variant["unit"]
        else:
            item["unit_cost"] = 0
        total_cost += item["unit_cost"]

    # 事务：插入订单 + 明细行 + 扣库存
    with get_db() as conn:
        cur = conn.execute(
            """INSERT INTO orders
               (type, mode, drink_id, drink_name, drink_price,
                operator_id, operator_name, notes, total_material_cost)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                d["type"], d["mode"],
                d.get("drink_id"), d.get("drink_name"), d.get("drink_price", 0),
                d.get("operator_id"), d.get("operator_name"),
                json.dumps(d.get("notes", []), ensure_ascii=False),
                round(total_cost, 2),
            ),
        )
        order_id = cur.lastrowid

        for item in items:
            conn.execute(
                """INSERT INTO order_items
                   (order_id, material_id, material_name,
                    variant_id, variant_name, amount, unit, unit_cost)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    order_id, item["material_id"], item.get("material_name"),
                    item["variant_id"], item.get("variant_name"),
                    item["amount"], item.get("unit", "g"), item["unit_cost"],
                ),
            )
            # 扣减库存
            conn.execute(
                "UPDATE variants SET current_stock = MAX(0, current_stock - ?) WHERE id = ?",
                (item["amount"], item["variant_id"]),
            )

    return jsonify({"id": order_id, "total_material_cost": round(total_cost, 2)}), 201


@bp.get("")
def list_orders():
    """
    查询订单列表
    参数: type=sale|internal, from=2024-01-01, to=2024-12-31, limit=50
    """
    conditions, params = [], []

    if t := request.args.get("type"):
        conditions.append("o.type = ?")
        params.append(t)
    if f := request.args.get("from"):
        conditions.append("o.created_at >= ?")
        params.append(f)
    if t := request.args.get("to"):
        conditions.append("o.created_at <= ? || ' 23:59:59'")
        params.append(t)

    where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
    limit = int(request.args.get("limit", 100))
    params.append(limit)

    orders = query(
        f"SELECT * FROM orders o {where} ORDER BY o.created_at DESC LIMIT ?",
        tuple(params),
    )

    # 附加明细行
    for order in orders:
        order["items"] = query(
            "SELECT * FROM order_items WHERE order_id = ?", (order["id"],)
        )
        # 将 notes JSON 字符串解析为列表
        try:
            order["notes"] = json.loads(order["notes"]) if order["notes"] else []
        except (json.JSONDecodeError, TypeError):
            order["notes"] = []

    return jsonify(orders)
