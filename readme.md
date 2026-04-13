# CK Management System

为社团设计的一款轻量化本地库存管理项目
咖啡社团管理系统。

适用于吧台触屏场景，支持售卖记录、内部消耗、库存管理、统计看板与日志归档。

## 功能概览

- 售卖/内部消耗两套流程（共用下单引擎）
- 饮品、原材料、原材料品类（三级）管理
- 操作人和备注选项管理
- 库存入库、库存查看、快捷查库编辑
- 统计看板（收入、成本、排行、用量）
- 按时间段归档历史订单

## 技术栈

- 后端: Flask + SQLite
- 前端: React 18（CDN + Babel，单页）
- 运行方式: Flask 同时提供 API 与前端页面

## 目录结构

```text
CK_Management_System/
├── README.md
├── readme.md
└── CK_MS/
	├── __init__.py
	├── app.py
	├── db.py
	├── run.py
	├── index.html
	├── api_menu.py
	├── api_order.py
	├── api_staff.py
	├── api_inventory.py
	├── api_stats.py
	├── api_archive.py
	└── README.md
```

## 快速开始

### 1) 安装依赖

```bash
pip install flask
```

### 2) 启动服务（推荐）

在项目根目录执行：

```bash
python -m CK_MS.run --host 127.0.0.1 --port 5000
```

### 3) 访问系统

- 前端页面: http://127.0.0.1:5000/
- API 根路径: http://127.0.0.1:5000/api

## 备用启动方式

也可以进入 CK_MS 目录执行：

```bash
python run.py
```

## 数据库说明

- 启动时自动初始化数据库并写入种子数据
- 默认数据库文件: data/coffee_club.db

## API 总览

### 菜单管理 /api/menu

- GET /materials 原材料列表
- POST /materials 新增原材料
- PUT /materials/<id> 修改原材料
- DELETE /materials/<id> 删除原材料
- GET /variants 原材料品类列表（可用 material_id 过滤）
- POST /variants 新增品类
- PUT /variants/<id> 修改品类
- DELETE /variants/<id> 删除品类
- GET /drinks 饮品列表（含配方）
- POST /drinks 新增饮品
- PUT /drinks/<id> 修改饮品
- DELETE /drinks/<id> 删除饮品

### 订单 /api/orders

- POST / 创建订单（自动扣减库存）
- GET / 查询订单（支持 type/from/to/limit）

### 人员与备注 /api/staff

- GET/POST /operators 操作人列表/新增
- PUT/DELETE /operators/<id> 操作人更新/删除（删除为软删除）
- GET/POST /notes 备注选项列表/新增
- PUT/DELETE /notes/<id> 备注更新/删除

### 库存 /api/inventory

- GET /stock 当前库存
- POST /restock 入库
- GET /records 入库记录
- PUT /quick-edit/<id> 查库快捷编辑

### 统计 /api/stats

- GET / 统计信息（支持 from/to）

### 归档 /api/archives

- POST / 按时间段创建归档
- GET / 归档列表
- GET /<id> 归档详情
