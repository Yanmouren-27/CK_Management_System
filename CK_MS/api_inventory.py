"""
api_inventory.py — 库存管理 API
================================
入库(restock)、库存查看(stock)、入库记录(records)、快捷查库修改
"""

from flask import Blueprint, request, jsonify
from .db import query, execute, get_db

bp = Blueprint("inventory", __name__, url_prefix="/api/inventory")


@bp.get("/stock")
def get_stock():
    """获取所有品类的当前库存，按原材料分组"""
    rows = query(
        """SELECT v.id, v.name, v.material_id, m.name AS material_name,
                  v.price_per_kg, v.unit, v.current_stock, v.total_stocked
           FROM variants v
           JOIN materials m ON v.material_id = m.id
           ORDER BY m.sort_order, v.id"""
    )
    return jsonify(rows)


@bp.post("/restock")
def restock():
    """
    原材料入库
    请求体: { "variant_id": 1, "quantity": 1000, "unit_price": 200 }
    """
    d = request.json
    variant = query("SELECT v.*, m.name AS material_name FROM variants v JOIN materials m ON v.material_id=m.id WHERE v.id=?", (d["variant_id"],), one=True)
    if not variant:
        return jsonify({"error": "品类不存在"}), 404

    with get_db() as conn:
        # 更新库存
        conn.execute(
            "UPDATE variants SET current_stock = current_stock + ?, total_stocked = total_stocked + ? WHERE id = ?",
            (d["quantity"], d["quantity"], d["variant_id"]),
        )
        # 记录入库
        conn.execute(
            """INSERT INTO inventory_records
               (variant_id, variant_name, material_name, quantity, unit_price)
               VALUES (?, ?, ?, ?, ?)""",
            (d["variant_id"], variant["name"], variant["material_name"],
             d["quantity"], d.get("unit_price", 0)),
        )

    return jsonify({"ok": True, "new_stock": variant["current_stock"] + d["quantity"]}), 201


@bp.get("/records")
def list_records():
    """入库历史记录"""
    limit = int(request.args.get("limit", 50))
    rows = query(
        "SELECT * FROM inventory_records ORDER BY created_at DESC LIMIT ?",
        (limit,),
    )
    return jsonify(rows)


@bp.put("/quick-edit/<int:vid>")
def quick_edit_variant(vid):
    """查库：快速修改品类信息（名称、单价、当前库存）"""
    d = request.json
    fields, values = [], []
    for col in ("name", "price_per_kg", "current_stock"):
        if col in d:
            fields.append(f"{col}=?")
            values.append(d[col])
    if not fields:
        return jsonify({"error": "无有效字段"}), 400
    values.append(vid)
    execute(f"UPDATE variants SET {','.join(fields)} WHERE id=?", tuple(values))
    return jsonify({"ok": True})
