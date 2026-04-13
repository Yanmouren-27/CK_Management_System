"""
api_menu.py — 菜单管理 API
============================
三级菜单 CRUD：饮品(drinks) → 原材料(materials) → 品类(variants)
"""

from flask import Blueprint, request, jsonify
from .db import query, execute

bp = Blueprint("menu", __name__, url_prefix="/api/menu")


# ━━━ 原材料（二级） ━━━

@bp.get("/materials")
def list_materials():
    rows = query("SELECT * FROM materials ORDER BY sort_order, id")
    return jsonify(rows)


@bp.post("/materials")
def create_material():
    data = request.json
    mid = execute(
        "INSERT INTO materials (name, sort_order) VALUES (?, ?)",
        (data["name"], data.get("sort_order", 0)),
    )
    return jsonify({"id": mid, "name": data["name"]}), 201


@bp.put("/materials/<int:mid>")
def update_material(mid):
    data = request.json
    execute(
        "UPDATE materials SET name=?, sort_order=? WHERE id=?",
        (data["name"], data.get("sort_order", 0), mid),
    )
    return jsonify({"ok": True})


@bp.delete("/materials/<int:mid>")
def delete_material(mid):
    execute("DELETE FROM materials WHERE id=?", (mid,))
    return jsonify({"ok": True})


# ━━━ 原材料品类（三级） ━━━

@bp.get("/variants")
def list_variants():
    material_id = request.args.get("material_id")
    if material_id:
        rows = query(
            """SELECT v.*, m.name AS material_name
               FROM variants v JOIN materials m ON v.material_id = m.id
               WHERE v.material_id = ? ORDER BY v.id""",
            (material_id,),
        )
    else:
        rows = query(
            """SELECT v.*, m.name AS material_name
               FROM variants v JOIN materials m ON v.material_id = m.id
               ORDER BY m.sort_order, v.id"""
        )
    return jsonify(rows)


@bp.post("/variants")
def create_variant():
    d = request.json
    vid = execute(
        "INSERT INTO variants (material_id, name, price_per_kg, unit) VALUES (?, ?, ?, ?)",
        (d["material_id"], d["name"], d["price_per_kg"], d.get("unit", "g")),
    )
    return jsonify({"id": vid}), 201


@bp.put("/variants/<int:vid>")
def update_variant(vid):
    d = request.json
    fields, values = [], []
    for col in ("name", "price_per_kg", "unit", "current_stock", "material_id"):
        if col in d:
            fields.append(f"{col}=?")
            values.append(d[col])
    if fields:
        values.append(vid)
        execute(f"UPDATE variants SET {','.join(fields)} WHERE id=?", tuple(values))
    return jsonify({"ok": True})


@bp.delete("/variants/<int:vid>")
def delete_variant(vid):
    execute("DELETE FROM variants WHERE id=?", (vid,))
    return jsonify({"ok": True})


# ━━━ 饮品（一级） ━━━

def _drink_with_recipe(drink_row):
    """给饮品附加完整配方信息"""
    recipes = query(
        """SELECT r.*, m.name AS material_name, v.name AS variant_name, v.unit
           FROM recipes r
           LEFT JOIN materials m ON r.material_id = m.id
           LEFT JOIN variants  v ON r.default_variant_id = v.id
           WHERE r.drink_id = ?""",
        (drink_row["id"],),
    )
    return {**drink_row, "recipe": recipes}


@bp.get("/drinks")
def list_drinks():
    rows = query("SELECT * FROM drinks ORDER BY sort_order, id")
    return jsonify([_drink_with_recipe(r) for r in rows])


@bp.post("/drinks")
def create_drink():
    d = request.json
    drink_id = execute(
        "INSERT INTO drinks (name, price, sort_order) VALUES (?, ?, ?)",
        (d["name"], d["price"], d.get("sort_order", 0)),
    )
    for item in d.get("recipe", []):
        execute(
            "INSERT INTO recipes (drink_id, material_id, default_variant_id, amount) VALUES (?, ?, ?, ?)",
            (drink_id, item["material_id"], item.get("default_variant_id"), item["amount"]),
        )
    return jsonify({"id": drink_id}), 201


@bp.put("/drinks/<int:did>")
def update_drink(did):
    d = request.json
    execute(
        "UPDATE drinks SET name=?, price=?, sort_order=? WHERE id=?",
        (d["name"], d["price"], d.get("sort_order", 0), did),
    )
    # 重建配方：先清后插
    execute("DELETE FROM recipes WHERE drink_id=?", (did,))
    for item in d.get("recipe", []):
        execute(
            "INSERT INTO recipes (drink_id, material_id, default_variant_id, amount) VALUES (?, ?, ?, ?)",
            (did, item["material_id"], item.get("default_variant_id"), item["amount"]),
        )
    return jsonify({"ok": True})


@bp.delete("/drinks/<int:did>")
def delete_drink(did):
    execute("DELETE FROM drinks WHERE id=?", (did,))
    return jsonify({"ok": True})
