"""
api_staff.py — 人员与备注 API
==============================
操作人(operators) + 自定义备注(custom_notes) 的 CRUD
"""

from flask import Blueprint, request, jsonify
from .db import query, execute

bp = Blueprint("staff", __name__, url_prefix="/api/staff")


# ━━━ 操作人 ━━━

@bp.get("/operators")
def list_operators():
    return jsonify(query("SELECT * FROM operators WHERE is_active=1 ORDER BY id"))


@bp.post("/operators")
def create_operator():
    d = request.json
    oid = execute("INSERT INTO operators (name) VALUES (?)", (d["name"],))
    return jsonify({"id": oid, "name": d["name"]}), 201


@bp.put("/operators/<int:oid>")
def update_operator(oid):
    d = request.json
    execute("UPDATE operators SET name=? WHERE id=?", (d["name"], oid))
    return jsonify({"ok": True})


@bp.delete("/operators/<int:oid>")
def delete_operator(oid):
    # 软删除：保留历史订单中的引用
    execute("UPDATE operators SET is_active=0 WHERE id=?", (oid,))
    return jsonify({"ok": True})


# ━━━ 备注选项 ━━━

@bp.get("/notes")
def list_notes():
    return jsonify(query("SELECT * FROM custom_notes ORDER BY id"))


@bp.post("/notes")
def create_note():
    d = request.json
    nid = execute("INSERT INTO custom_notes (label) VALUES (?)", (d["label"],))
    return jsonify({"id": nid, "label": d["label"]}), 201


@bp.put("/notes/<int:nid>")
def update_note(nid):
    d = request.json
    execute("UPDATE custom_notes SET label=? WHERE id=?", (d["label"], nid))
    return jsonify({"ok": True})


@bp.delete("/notes/<int:nid>")
def delete_note(nid):
    execute("DELETE FROM custom_notes WHERE id=?", (nid,))
    return jsonify({"ok": True})
