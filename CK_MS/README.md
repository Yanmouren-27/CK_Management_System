# ☕ 咖啡社团管理系统

前后端分离的咖啡社团信息管理系统，适用于带触摸屏的吧台终端。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 后端 | Python Flask | RESTful API，Blueprint 模块化路由 |
| 数据库 | SQLite | 关系型存储，可直接用 DB Browser 查看 |
| 前端 | React 18 | 单页应用，深色触摸友好界面 |

## 快速启动

```bash
# 1. 安装依赖
pip install flask

# 2. 启动服务
python run.py

# 3. 访问
# 浏览器打开 http://localhost:5000
```

## 项目结构

```
coffee-club/
├── server/                    # 后端 Python 包
│   ├── app.py                 # Flask 应用工厂，注册蓝图
│   ├── db.py                  # 数据库层：Schema + 连接 + 查询工具
│   ├── api_menu.py            # 菜单 API（饮品/原材料/品类 CRUD）
│   ├── api_order.py           # 订单 API（售卖/内部消耗）
│   ├── api_staff.py           # 人员 API（操作人/备注选项）
│   ├── api_inventory.py       # 库存 API（入库/查库/快捷编辑）
│   ├── api_stats.py           # 统计 API（仪表盘数据）
│   └── api_archive.py         # 归档 API（按时间段归档）
├── frontend/
│   └── index.html             # React SPA 前端
├── data/                      # 运行时自动创建
│   └── coffee_club.db         # SQLite 数据库文件
├── run.py                     # 启动入口
└── README.md
```

## 数据库 Schema

系统使用 10 张表，结构清晰可读：

```
materials           原材料分类（咖啡豆、牛奶…）
  └── variants      原材料品类（哥伦比亚、耶加雪菲…）
drinks              饮品定义
  └── recipes       饮品配方（多对多关联原材料）
operators           操作人
custom_notes        自定义备注选项
orders              交易订单主表
  └── order_items   订单消耗明细
inventory_records   入库记录
archives            归档快照
```

可使用 [DB Browser for SQLite](https://sqlitebrowser.org/) 打开 `data/coffee_club.db` 直接查看和编辑数据。

## API 接口一览

### 菜单管理 `/api/menu`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/menu/materials` | 获取所有原材料 |
| POST | `/menu/materials` | 新增原材料 |
| PUT | `/menu/materials/:id` | 修改原材料 |
| DELETE | `/menu/materials/:id` | 删除原材料 |
| GET | `/menu/variants?material_id=` | 获取品类（可按原材料过滤） |
| POST | `/menu/variants` | 新增品类 |
| PUT | `/menu/variants/:id` | 修改品类 |
| DELETE | `/menu/variants/:id` | 删除品类 |
| GET | `/menu/drinks` | 获取所有饮品（含配方） |
| POST | `/menu/drinks` | 新增饮品 |
| PUT | `/menu/drinks/:id` | 修改饮品 |
| DELETE | `/menu/drinks/:id` | 删除饮品 |

### 订单 `/api/orders`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/orders` | 创建订单（自动扣减库存） |
| GET | `/orders?type=&from=&to=&limit=` | 查询订单列表 |

### 人员 `/api/staff`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET/POST | `/staff/operators` | 操作人列表/新增 |
| PUT/DELETE | `/staff/operators/:id` | 操作人修改/删除 |
| GET/POST | `/staff/notes` | 备注选项列表/新增 |
| PUT/DELETE | `/staff/notes/:id` | 备注修改/删除 |

### 库存 `/api/inventory`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/inventory/stock` | 当前库存总览 |
| POST | `/inventory/restock` | 原材料入库 |
| GET | `/inventory/records` | 入库历史记录 |
| PUT | `/inventory/quick-edit/:id` | 查库快捷编辑 |

### 统计 `/api/stats`

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/stats?from=&to=` | 综合统计（含排行、消耗明细） |

### 归档 `/api/archives`

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/archives` | 创建归档（移除原订单） |
| GET | `/archives` | 归档列表 |
| GET | `/archives/:id` | 归档详情（含订单快照） |

## 架构设计原则

**DRY（Don't Repeat Yourself）**
- 所有数据库操作通过 `db.py` 的 `query()` / `execute()` 统一进行
- 前端 API 调用通过唯一的 `api` 对象封装
- 售卖/内部消耗共用同一个 `OrderFlow` 组件
- 通用 UI 组件（Btn/Card/Modal/GridSelect 等）全局复用

**模块化**
- 后端 6 个 Blueprint 各司其职，路由互不交叉
- 前端按功能分 7 个 Section，每个 Section 自包含

**可扩展**
- `variants` 表的 `current_stock` 字段独立于交易记录
- 未来接入实时重量传感器时，只需新增一个 WebSocket 端点更新该字段
- 新增饮品/原材料品类只需通过管理界面操作，无需改代码

## 开发模式

```bash
python run.py --debug --port 5000
```

调试模式下 Flask 支持热重载，修改后端代码后自动重启。
