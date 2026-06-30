# 📚 图书借阅管理系统

> **FastAPI + MySQL + JWT 双角色图书借阅管理系统**
>
> 管理员 / 学生双角色，完整 CRUD + 评论评分 + 收藏 + 推荐算法 + 数据可视化 + Docker 部署 + CI/CD

---

## 📋 目录

- [项目简介](#项目简介)
- [技术栈](#技术栈)
- [功能清单](#功能清单)
- [项目架构](#项目架构)
- [数据库设计](#数据库设计)
- [快速开始](#快速开始)
- [API 文档](#api-文档)
- [Docker 部署](#docker-部署)
- [CI/CD 流水线](#cicd-流水线)
- [推荐算法说明](#推荐算法说明)
- [项目目录结构](#项目目录结构)
- [许可证](#许可证)

---

## 项目简介

一个功能完整的图书借阅管理系统，支持**管理员**和**学生**两种角色登录。管理员可以进行图书管理、学生管理、公告发布、数据可视化分析；学生可以浏览馆藏、借书还书、评分评论、收藏图书、查看个性化推荐。

| 属性 | 值 |
|------|-----|
| 前端页面 | **18 个** |
| API 接口 | **45+** |
| 数据库表 | **10 张** |
| Git 提交 | **65+** |
| 推荐算法 | 协同过滤 + 规则推荐 |

---

## 技术栈

### 后端

| 技术 | 用途 |
|------|------|
| **Python 3.13 / 3.11** | 运行环境 |
| **FastAPI** | Web 框架 |
| **SQLAlchemy 2.0** | ORM 数据库操作 |
| **PyMySQL** | MySQL 驱动 |
| **JWT (python-jose)** | 登录鉴权 |
| **bcrypt** | 密码加密存储 |
| **Pillow** | 验证码图片生成 |

### 前端

| 技术 | 用途 |
|------|------|
| **HTML5 + CSS3 + JavaScript** | 原生三件套，无框架依赖 |
| **Chart.js 4.4** | 数据可视化图表 |
| **CSS 变量 + 深色模式** | 主题切换 |

### 数据库

| 技术 | 用途 |
|------|------|
| **MySQL 8.0** | 关系型数据库 |
| **SQLite** | 单元测试数据库 |
| **MySQL 触发器** | 自动扣库存 + 操作日志 |

### DevOps

| 技术 | 用途 |
|------|------|
| **Docker** | 容器化部署 |
| **docker-compose** | 容器编排 |
| **GitHub Actions** | CI/CD 自动化流水线 |
| **pytest** | 单元测试（21 条用例） |

---

## 功能清单

### 🔧 管理员端（9 个页面）

| 页面 | 功能 |
|------|------|
| 📊 **首页看板** | KPI 统计卡片、分类柱状图、热门图书 Top 6、最近借阅动态、公告预览 |
| 📖 **图书管理** | 增删改查、ISBN/出版社/封面/简介字段、详情弹窗（含借阅历史+评分）、库存缺书预警、批量导入导出 CSV |
| 👨‍🎓 **学生管理** | 增删改查、绑定系统账号、批量导入导出 CSV |
| 📢 **公告管理** | 发布/编辑/删除公告、置顶功能 |
| 📝 **登录日志** | 全站登录记录、按账号+时间范围筛选、导出 CSV |
| 📋 **借阅日志** | 借书/还书操作全记录、按类型+关键词筛选、导出 CSV/TXT |
| ⚠️ **逾期图书** | 筛选逾期列表、逾期天数统计、直接还书处理、导出 CSV |
| 📈 **数据可视化** | 饼图/柱状图/折线图/直方图/极坐标图/横向柱状图/双柱图等 **8 种图表**，覆盖分类分布、借阅趋势、读者排行、库存分布、周热度、逾期分布、出版社分布、班级分布 |
| ⚙️ **系统设置** | 可视化配置逾期天数、最大借书数量、续借天数、验证码开关、保存即时生效无需重启 |

### 🎓 学生端（9 个页面）

| 页面 | 功能 |
|------|------|
| 📊 **我的首页** | 个人统计卡片、公告预览、个人信息、热门图书、借阅趋势图、快捷入口 |
| 🎯 **图书推荐** | Tab 切换 5 种推荐：猜你喜欢/高分推荐/全站热门/冷门好书/**协同过滤个性化推荐**，每种显示推荐因子说明 |
| 📚 **馆藏浏览** | 卡片/列表双视图、分类+库存筛选、封面图片展示、收藏/借书一键操作、图书详情弹窗（评分+评论+借阅） |
| 📈 **数据可视化** | 饼图/折线图/柱状图/直方图/评分分布/借还对比 **6 种图表** |
| 📖 **我的借阅** | 状态筛选（未归还/已归还/逾期）、还书操作、借书弹窗、导出 CSV |
| ⭐ **我的收藏** | 收藏列表卡片展示、一键取消收藏、跳转借阅 |
| 📈 **阅读统计** | 累计借阅/在借/逾期/已归还统计、分类偏好、月度趋势 |
| 📝 **登录日志** | 个人登录记录、时间范围筛选、导出 CSV |
| 👤 **个人中心** | 个人资料编辑、密码修改、账号信息一览 |

### 🔐 鉴权系统

| 功能 | 说明 |
|------|------|
| **双角色登录** | 管理员 / 学生角色隔离 |
| **图形验证码** | Pillow 生成 4 位验证码图片，5 分钟有效 |
| **JWT Token** | 2 小时有效期，接口级权限拦截 |
| **学生自助注册** | 填信息 + 验证码自动创建账号 |
| **bcrypt 加密** | 密码哈希存储，数据库不存明文 |
| **接口权限** | 未登录 → 401，学生访问管理接口 → 403 |

---

## 项目架构

```
┌─────────────────────────────────────────────────────────┐
│                    前端（HTML + CSS + JS）               │
│  18个页面 · Chart.js图表 · CSS变量深色模式 · Fetch API  │
├─────────────────────────────────────────────────────────┤
│                   FastAPI 路由层（src/api/）             │
│         auth.py · admin.py · student.py                 │
├─────────────────────────────────────────────────────────┤
│                    业务逻辑层（src/service/）            │
│  auth_service · book_service · reader_service           │
│  borrow_service（借阅限制 · 逾期拦截 · 库存变更）       │
├─────────────────────────────────────────────────────────┤
│                    数据访问层（src/dao/）                │
│  8个DAO模块 · SQLAlchemy ORM · 分页查询 · 聚合统计      │
├─────────────────────────────────────────────────────────┤
│                  MySQL 8.0（10张表）                     │
│  触发器：自动扣库存 · 自动写操作日志                     │
│  启动自建表 · 自迁移schema · 自初始化默认数据            │
└─────────────────────────────────────────────────────────┘
```

---

## 数据库设计

### 10 张数据表

| 表名 | 说明 | 核心字段 |
|------|------|---------|
| `sys_user` | 系统账号表 | username, password(bcrypt), role(admin/student), name, phone |
| `book` | 图书表 | book_name, author, category, isbn, publisher, description, cover_url, stock, total_borrows |
| `reader` | 学生读者表 | student_name, class, phone, bind_user_id |
| `borrow_record` | 借阅记录表 | book_id, reader_id, borrow_time, return_time, status |
| `login_log` | 登录日志表 | user_id, login_ip, login_time, logout_time, login_role |
| `borrow_operation_log` | 借阅操作日志 | borrow_record_id, operate_type(borrow/return), operate_time |
| `announcement` | 公告表 | title, content, publisher_id, is_pinned |
| `book_review` | 评分评论表 | book_id, user_id, rating(1-5), comment |
| `system_config` | 系统配置表 | config_key, config_value, config_type |
| `book_favorite` | 图书收藏表 | user_id, book_id |

### 2 个 MySQL 触发器

| 触发器 | 触发时机 | 作用 |
|--------|----------|------|
| `after_borrow_insert` | 新增借阅记录 | 自动写入操作日志 + 图书库存 -1 |
| `after_borrow_update_return` | 更新归还时间 | 自动写入归还日志 + 图书库存 +1 |

---

## 快速开始

### 前置条件

- Python 3.11+
- MySQL 8.0（本机或远程）
- 可选：Docker Desktop

### 1. 创建数据库

```sql
CREATE DATABASE IF NOT EXISTS library_manage CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 2. 安装依赖

```powershell
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

### 3. 启动服务

**Windows PowerShell：**

```powershell
cd d:\claude-devops-auto-demo

# 设置环境变量
$env:DATABASE_URL = "mysql+pymysql://root:123456@127.0.0.1:3306/library_manage?charset=utf8mb4"
$env:PYTHONPATH = "."

# 启动
python -m uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload
```

**Linux / macOS：**

```bash
export DATABASE_URL="mysql+pymysql://root:123456@127.0.0.1:3306/library_manage?charset=utf8mb4"
export PYTHONPATH="."
uvicorn src.main:app --host 0.0.0.0 --port 5000 --reload
```

### 4. 打开浏览器

```
http://localhost:5000/frontend/login.html
```

### 5. 默认账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 🔧 管理员 | `admin` | `123456` |
| 🎓 学生 | `zhangsan` | `123456` |
| 🎓 学生 | `lisi` | `123456` |
| 🎓 学生 | `wangwu` | `123456` |
| 🎓 学生 | `zhaoliu` | `123456` |
| 🎓 学生 | `sunqi` | `123456` |
| 🎓 学生 | `zhouba` | `123456` |

> 启动时自动创建管理员账号和初始化系统配置，无需手动操作数据库。

---

## API 文档

启动服务后访问 Swagger UI：

```
http://localhost:5000/docs
```

### 主要接口分类

| 前缀 | 说明 | 接口数 |
|------|------|--------|
| `/api/auth/*` | 鉴权（登录/退出/注册/验证码/当前用户） | 6 |
| `/api/admin/*` | 管理员专属（看板/图书/学生/借阅/公告/日志/逾期/设置/评论管理/封面抓取） | 25+ |
| `/api/student/*` | 学生专属（看板/图书/借阅/收藏/评分/推荐/统计/个人中心/日志） | 20+ |

### 部分关键接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/auth/login` | 用户登录（含验证码） |
| POST | `/api/auth/register` | 学生自助注册 |
| GET | `/api/auth/captcha` | 获取图形验证码 |
| GET | `/api/admin/dashboard` | 管理端数据看板 |
| GET | `/api/admin/charts/overview` | 可视化全局数据 |
| POST | `/api/admin/books/import` | 批量导入图书 CSV |
| POST | `/api/admin/books/fetch-covers` | 批量抓取图书封面 |
| GET | `/api/admin/settings` | 获取系统配置 |
| PUT | `/api/admin/settings` | 修改系统配置 |
| GET | `/api/student/recommend` | 图书推荐（5 种类型） |
| GET | `/api/student/recommend/types` | 推荐类型列表 |
| GET | `/api/student/charts` | 学生个人可视化数据 |
| POST | `/api/student/reviews` | 提交评分评论 |
| PUT | `/api/student/reviews/{id}` | 修改自己的评论 |
| DELETE | `/api/student/reviews/{id}` | 删除自己的评论 |
| POST | `/api/student/favorites?book_id=N` | 添加收藏 |
| DELETE | `/api/student/favorites/{book_id}` | 取消收藏 |
| POST | `/api/student/borrows` | 学生借书 |
| PUT | `/api/student/borrows/{id}/return` | 学生还书 |

---

## Docker 部署

### 方式一：Docker Compose（推荐，连接本机 MySQL）

```powershell
cd d:\claude-devops-auto-demo
docker-compose up -d --build
```

容器启动后访问 `http://localhost:5000/frontend/login.html`

### 方式二：单独构建镜像

```powershell
docker build -t library-manage-system:latest .
docker run -d -p 5000:5000 \
  -e DATABASE_URL="mysql+pymysql://root:123456@host.docker.internal:3306/library_manage?charset=utf8mb4" \
  -e PYTHONPATH=/app \
  --name library_backend library-manage-system:latest
```

### 容器说明

| 容器 | 端口 | 说明 |
|------|------|------|
| `library_backend` | `5000:5000` | FastAPI + 前端静态资源 |

### 常用 Docker 命令

```powershell
docker-compose up -d --build   # 构建并启动
docker-compose down            # 停止
docker-compose restart         # 重启
docker logs library_backend    # 查看日志
```

---

## CI/CD 流水线

GitHub Actions 自动执行：

```
代码推送 → 拉取代码 → 启动 MySQL 测试容器 → 安装依赖
→ Pylint 代码检查 → Pytest 21 条单元测试
→ Docker 镜像构建 → 模块导入验证
```

| 阶段 | 说明 |
|------|------|
| **Lint** | Pylint ≥ 6.0 代码规范检查 |
| **Test** | pytest 运行 21 条测试用例（鉴权/图书/借阅/日志） |
| **Build** | 构建 Docker 镜像并验证模块导入 |

所有 push/PR 到 `master` 分支自动触发。

---

## 推荐算法说明

### 5 种推荐类型

| Tab | 算法 | 推荐因子 |
|-----|------|---------|
| 🤖 **猜你喜欢** | 分类协同过滤 | 分析用户借阅偏好分类 → 同分类热门书推荐 |
| ⭐ **高分推荐** | 评分排序 | 全站评分 ≥ 4 星的口碑好书 |
| 🔥 **全站热门** | 热度排名 | 全站借阅次数 Top 榜 |
| 💎 **冷门好书** | 逆热度推荐 | 高分但借阅次数少（<5 次）的宝藏书 |
| 🧠 **个性化推荐** | 协同过滤算法 | **相似用户发现 → 关联书籍统计 → 排除已借** |

### 协同过滤流程

```
1. 找到与当前用户借过相同图书的其他读者
2. 统计这些相似读者借过的其他书（按被借次数排序）
3. 排除当前用户已借过的书
4. 数据稀疏时自动退化：新用户 → 热门推荐，样本不足 → 同分类补充
```

---

## 项目目录结构

```
claude-devops-auto-demo/
├── src/                          # 后端源码
│   ├── api/                      # API 路由层
│   │   ├── auth.py               # 鉴权（登录/注册/验证码）
│   │   ├── admin.py              # 管理员接口（25+ 端点）
│   │   └── student.py            # 学生接口（20+ 端点）
│   ├── service/                  # 业务逻辑层
│   │   ├── auth_service.py       # JWT签发/密码加密
│   │   ├── book_service.py       # 图书业务
│   │   ├── reader_service.py     # 读者业务
│   │   └── borrow_service.py     # 借阅业务（数量限制+逾期拦截）
│   ├── dao/                      # 数据访问层
│   │   ├── auth_dao.py           # 账号操作
│   │   ├── book_dao.py           # 图书CRUD
│   │   ├── reader_dao.py         # 读者CRUD
│   │   ├── borrow_dao.py         # 借阅CRUD
│   │   ├── login_log_dao.py      # 登录日志
│   │   ├── borrow_log_dao.py     # 操作日志
│   │   ├── review_dao.py         # 评分评论
│   │   ├── favorite_dao.py       # 收藏夹
│   │   ├── announcement_dao.py   # 公告
│   │   └── config_dao.py         # 系统配置
│   ├── db/                       # 数据库
│   │   ├── database.py           # 引擎+会话+触发器初始化
│   │   └── models.py             # 10张数据表模型
│   ├── schemas/                  # Pydantic 校验模型
│   │   ├── auth.py / book.py / reader.py
│   │   ├── borrow.py / log.py / review.py
│   │   └── announcement.py
│   ├── config/
│   │   └── settings.py           # 全局配置（数据库/JWT/分页）
│   ├── common/
│   │   ├── dependencies.py       # JWT鉴权依赖+角色拦截
│   │   └── exception.py          # 全局异常处理
│   └── main.py                   # 应用入口（FastAPI实例+生命周期）
│
├── frontend/                     # 前端页面
│   ├── login.html                # 登录页（验证码+注册）
│   ├── app.js                    # 共享JS（API封装/侧边栏/深色模式/CSV导出）
│   ├── style.css                 # 统一样式表（含深色模式CSS变量）
│   ├── admin_*.html              # 管理员9个页面
│   └── student_*.html            # 学生端9个页面
│
├── tests/                        # 单元测试
│   ├── test_auth.py              # 鉴权测试（6条）
│   ├── test_book.py              # 图书测试（5条）
│   ├── test_borrow.py            # 借阅测试（5条）
│   └── test_logs.py              # 日志测试（5条）
│
├── .github/workflows/
│   └── ci-cd.yml                 # GitHub Actions CI/CD
│
├── Dockerfile                    # Docker 镜像构建文件
├── docker-compose.yml            # Docker 容器编排
├── requirements.txt              # Python 依赖清单
├── .dockerignore                 # Docker 构建排除
└── README.md                     # 本文件
```

---

## 许可证

MIT License

---

> **项目统计**：18 个前端页面 · 45+ API 接口 · 10 张数据库表 · 2 个 MySQL 触发器 · 21 条单元测试 · 5 种推荐算法 · 14 种数据图表 · Docker + CI/CD 自动化
