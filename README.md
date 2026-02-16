# 会议室智能预约系统（Django + Vue + MySQL）

该项目实现了一个会议室智能预约系统，覆盖如下核心能力：

- 房间信息展示（名称、容量、设备、地点、描述）
- 查看可用时间段（按日期+时间粒度返回）
- 预约 / 取消预约
- 用户身份与权限（普通用户、管理员）
- 冲突检测（避免同一会议室时间段重叠预约）
- 通知机制（邮件 + 站内消息）

## 技术栈

- 后端：Python + Django + Django REST Framework
- 前端：Vue 3 + Vite + Axios
- 数据库：MySQL

## 目录结构

```text
.
├── backend
│   ├── manage.py
│   ├── meeting_room_system
│   └── reservations
├── frontend
└── .env.example
```

## 后端启动

1. 创建虚拟环境并安装依赖

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. 配置环境变量（参考根目录 `.env.example`）

3. 执行迁移并创建超级管理员

```bash
python manage.py migrate
python manage.py createsuperuser
```

4. 启动后端

```bash
python manage.py runserver 0.0.0.0:8000
```

## 前端启动

```bash
cd frontend
npm install
npm run dev
```

默认前端地址：`http://localhost:5173`

## API 概览

- `POST /api/auth/login/` 登录并获取 Token
- `GET/POST /api/rooms/` 会议室列表 / 管理员创建
- `GET /api/rooms/{id}/availability/?date=YYYY-MM-DD` 查询可用时段
- `GET/POST /api/bookings/` 查询预约 / 新建预约
- `DELETE /api/bookings/{id}/` 取消预约（软取消）
- `GET /api/notifications/` 查看通知

## 权限说明

- 普通用户：查看会议室、查询可用时段、创建预约、取消自己的预约、查看自己的通知
- 管理员：拥有普通用户全部能力，并可管理会议室、查看全部预约

## 通知机制

每次预约创建成功或取消时，系统会自动触发：

- 邮件通知（通过 Django `send_mail`，默认控制台后端）
- 站内消息通知（`Notification` 模型持久化）

## 冲突检测规则

保存预约时会校验：

- 开始时间必须早于结束时间
- 预约人数不能超过会议室容量
- 同一会议室在同一时间段不能存在重叠的有效预约
