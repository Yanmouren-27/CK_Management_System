"""
database.py — 数据库层
======================
职责：连接管理、Schema 定义、查询工具函数、种子数据
所有 SQL 操作统一通过本模块的 query() / execute() 进行，确保 DRY
"""

import sqlite3
import os
import json
from contextlib import contextmanager

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "coffee_club.db")

# ──────────────────────────────────────────────
#  连接管理
# ──────────────────────────────────────────────

def get_connection():
    """获取数据库连接（开启外键约束 + Row 工厂）"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


@contextmanager
def get_db():
    """上下文管理器：自动提交/回滚/关闭"""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


# ──────────────────────────────────────────────
#  通用查询工具
# ──────────────────────────────────────────────

def query(sql, params=(), one=False):
    """执行 SELECT，返回 dict 列表（one=True 时返回单条或 None）"""
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
        result = [dict(r) for r in rows]
        return result[0] if one and result else (None if one else result)


def execute(sql, params=()):
    """执行 INSERT/UPDATE/DELETE，返回 lastrowid"""
    with get_db() as conn:
        cursor = conn.execute(sql, params)
        return cursor.lastrowid


def execute_many(statements):
    """在同一事务中执行多条语句，每条为 (sql, params) 元组"""
    with get_db() as conn:
        results = []
        for sql, params in statements:
            cursor = conn.execute(sql, params)
            results.append(cursor.lastrowid)
        return results


# ──────────────────────────────────────────────
#  Schema 定义
# ──────────────────────────────────────────────

SCHEMA = """
-- ===== 三级菜单体系 =====

-- 二级：原材料分类（咖啡豆、牛奶、糖浆等）
CREATE TABLE IF NOT EXISTS materials (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 三级：原材料品类（不同产地的咖啡豆、不同品牌的牛奶等）
CREATE TABLE IF NOT EXISTS variants (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    material_id   INTEGER NOT NULL,
    name          TEXT    NOT NULL,
    price_per_kg  REAL    NOT NULL DEFAULT 0,   -- 单价（元/千克 或 元/升）
    unit          TEXT    NOT NULL DEFAULT 'g',  -- 计量单位：g 或 ml
    current_stock REAL    NOT NULL DEFAULT 0,    -- 当前库存量
    total_stocked REAL    NOT NULL DEFAULT 0,    -- 累计入库量
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (material_id) REFERENCES materials(id) ON DELETE CASCADE
);

-- 一级：饮品
CREATE TABLE IF NOT EXISTS drinks (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL,
    price       REAL    NOT NULL DEFAULT 0,     -- 售价
    sort_order  INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 饮品配方（饮品 → 原材料的用量映射）
CREATE TABLE IF NOT EXISTS recipes (
    id                 INTEGER PRIMARY KEY AUTOINCREMENT,
    drink_id           INTEGER NOT NULL,
    material_id        INTEGER NOT NULL,
    default_variant_id INTEGER,
    amount             REAL    NOT NULL DEFAULT 0,  -- 默认用量
    FOREIGN KEY (drink_id)           REFERENCES drinks(id)    ON DELETE CASCADE,
    FOREIGN KEY (material_id)        REFERENCES materials(id),
    FOREIGN KEY (default_variant_id) REFERENCES variants(id)
);

-- ===== 人员与备注 =====

CREATE TABLE IF NOT EXISTS operators (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    is_active  INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS custom_notes (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    label      TEXT    NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===== 交易记录 =====

-- 主订单
CREATE TABLE IF NOT EXISTS orders (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    type                TEXT    NOT NULL CHECK(type IN ('sale', 'internal')),
    mode                TEXT    NOT NULL CHECK(mode IN ('drink', 'custom')),
    drink_id            INTEGER,
    drink_name          TEXT,
    drink_price         REAL    DEFAULT 0,
    operator_id         INTEGER,
    operator_name       TEXT,
    notes               TEXT    DEFAULT '[]',   -- JSON: 备注标签列表
    total_material_cost REAL    NOT NULL DEFAULT 0,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (drink_id)    REFERENCES drinks(id),
    FOREIGN KEY (operator_id) REFERENCES operators(id)
);

-- 订单明细行（每行 = 一种原材料消耗）
CREATE TABLE IF NOT EXISTS order_items (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id      INTEGER NOT NULL,
    material_id   INTEGER NOT NULL,
    material_name TEXT,
    variant_id    INTEGER NOT NULL,
    variant_name  TEXT,
    amount        REAL    NOT NULL,              -- 用量
    unit          TEXT    NOT NULL DEFAULT 'g',
    unit_cost     REAL    NOT NULL DEFAULT 0,    -- 该行成本
    FOREIGN KEY (order_id)    REFERENCES orders(id)    ON DELETE CASCADE,
    FOREIGN KEY (material_id) REFERENCES materials(id),
    FOREIGN KEY (variant_id)  REFERENCES variants(id)
);

-- ===== 库存入库记录 =====

CREATE TABLE IF NOT EXISTS inventory_records (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id   INTEGER NOT NULL,
    variant_name TEXT,
    material_name TEXT,
    quantity     REAL    NOT NULL,
    unit_price   REAL    DEFAULT 0,
    created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (variant_id) REFERENCES variants(id)
);

-- ===== 归档 =====

CREATE TABLE IF NOT EXISTS archives (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    label         TEXT    NOT NULL,
    start_date    TEXT    NOT NULL,
    end_date      TEXT    NOT NULL,
    order_count   INTEGER NOT NULL DEFAULT 0,
    sale_count    INTEGER NOT NULL DEFAULT 0,
    internal_count INTEGER NOT NULL DEFAULT 0,
    total_revenue REAL    NOT NULL DEFAULT 0,
    total_cost    REAL    NOT NULL DEFAULT 0,
    snapshot      TEXT    NOT NULL DEFAULT '[]', -- JSON: 订单快照
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


# ──────────────────────────────────────────────
#  初始化与种子数据
# ──────────────────────────────────────────────

SEED_DATA = {
    "materials": [
        ("咖啡豆", 1),
        ("牛奶",   2),
        ("糖浆",   3),
        ("其他",   4),
    ],
    "variants": [
        # (material_name, name, price_per_kg, unit)
        ("咖啡豆", "哥伦比亚",   200, "g"),
        ("咖啡豆", "耶加雪菲",   320, "g"),
        ("咖啡豆", "曼特宁",     260, "g"),
        ("牛奶",   "鲜牛奶",      12, "ml"),
        ("牛奶",   "燕麦奶",      28, "ml"),
        ("糖浆",   "香草糖浆",    40, "ml"),
        ("糖浆",   "焦糖糖浆",    40, "ml"),
        ("其他",   "巧克力粉",    80, "g"),
    ],
    "drinks": [
        # (name, price, [(material_name, variant_name, amount), ...])
        ("美式",     18, [("咖啡豆", "哥伦比亚", 18)]),
        ("拿铁",     24, [("咖啡豆", "哥伦比亚", 18), ("牛奶", "鲜牛奶", 200)]),
        ("卡布奇诺", 24, [("咖啡豆", "哥伦比亚", 18), ("牛奶", "鲜牛奶", 150)]),
        ("摩卡",     28, [("咖啡豆", "哥伦比亚", 18), ("牛奶", "鲜牛奶", 180), ("糖浆", "焦糖糖浆", 20), ("其他", "巧克力粉", 10)]),
        ("香草拿铁", 28, [("咖啡豆", "哥伦比亚", 18), ("牛奶", "鲜牛奶", 200), ("糖浆", "香草糖浆", 15)]),
    ],
    "operators": ["小王", "小李", "小张"],
    "notes": ["调模", "过萃", "萃取不足", "加冰", "少糖"],
}


def init_db():
    """初始化数据库：建表 + 写入种子数据（仅首次）"""
    with get_db() as conn:
        conn.executescript(SCHEMA)

        # 检查是否已有数据
        count = conn.execute("SELECT COUNT(*) c FROM materials").fetchone()["c"]
        if count > 0:
            return  # 已初始化过

        # 写入原材料
        mat_ids = {}
        for name, sort in SEED_DATA["materials"]:
            cur = conn.execute(
                "INSERT INTO materials (name, sort_order) VALUES (?, ?)",
                (name, sort),
            )
            mat_ids[name] = cur.lastrowid

        # 写入品类
        var_ids = {}
        for mat_name, var_name, price, unit in SEED_DATA["variants"]:
            cur = conn.execute(
                "INSERT INTO variants (material_id, name, price_per_kg, unit, current_stock) VALUES (?, ?, ?, ?, ?)",
                (mat_ids[mat_name], var_name, price, unit, 0),
            )
            var_ids[(mat_name, var_name)] = cur.lastrowid

        # 写入饮品 + 配方
        for drink_name, price, recipe in SEED_DATA["drinks"]:
            cur = conn.execute(
                "INSERT INTO drinks (name, price) VALUES (?, ?)",
                (drink_name, price),
            )
            drink_id = cur.lastrowid
            for mat_name, var_name, amount in recipe:
                conn.execute(
                    "INSERT INTO recipes (drink_id, material_id, default_variant_id, amount) VALUES (?, ?, ?, ?)",
                    (drink_id, mat_ids[mat_name], var_ids[(mat_name, var_name)], amount),
                )

        # 操作人
        for name in SEED_DATA["operators"]:
            conn.execute("INSERT INTO operators (name) VALUES (?)", (name,))

        # 备注选项
        for label in SEED_DATA["notes"]:
            conn.execute("INSERT INTO custom_notes (label) VALUES (?)", (label,))

    print("[DB] 数据库初始化完成，种子数据已写入")
