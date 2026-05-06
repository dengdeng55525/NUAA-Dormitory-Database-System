# NUAA-Dormitory-Database-System

## 项目信息

- 项目名称：宿舍管理系统数据库课程设计

## 项目简介

本项目是一个基于 Flask 和 MySQL 的宿舍管理系统，围绕学生住宿信息、宿舍楼栋、床位分配、宿舍管理员、访客登记、奖惩记录和统计分析等场景进行设计与实现。系统后端提供管理员、学生和访客相关接口，前端页面用于完成登录、信息查询、数据维护和统计结果展示。

项目代码已经移除本地数据库密码、Flask 密钥等敏感配置。公开仓库中仅保留 `.env.example` 作为配置示例，实际运行时需要在本地通过环境变量或 `.env` 文件提供数据库连接信息。

## 目录结构

- `backend/app.py`：Flask 应用入口，负责注册接口蓝图和静态页面路由
- `backend/api_admin.py`：管理员端接口，包括学生、宿舍、床位、访客、统计和密码管理等功能
- `backend/api_student.py`：学生端接口，包括个人住宿信息、访客记录和密码修改等功能
- `backend/api_visitor.py`：访客登记接口
- `backend/db_config.py`：数据库连接配置，统一从环境变量读取
- `backend/static/`：前端页面和静态资源
- `backend/插入数据.py`：生成并插入模拟基础数据的脚本
- `backend/插入剩余90万信息.py`：批量生成历史学生模拟数据的脚本

## 环境要求

- Python 3.9+
- MySQL 8.x 或兼容版本

安装依赖：

```powershell
cd backend
py -3 -m pip install -r requirements.txt
```

## 配置说明

复制 `.env.example` 中的配置项，并在本地环境中设置真实值：

```text
DB_HOST=127.0.0.1
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_database_password
DB_NAME=dormitory_manage_system
DB_CHARSET=utf8mb4
FLASK_SECRET_KEY=replace-with-a-random-secret-key
```

其中 `DB_PASSWORD` 和 `FLASK_SECRET_KEY` 不应提交到 GitHub。

## 启动方式

进入后端目录后运行：

```powershell
py -3 app.py
```

浏览器访问：

```text
http://127.0.0.1:5000
```

## 说明

数据插入脚本使用 Faker 生成模拟姓名和手机号，用于课程设计的数据规模测试与功能演示，不包含真实业务数据。运行插入脚本前，应先确认本地数据库表结构已经创建完成，并检查数据量是否符合本机环境承载能力。

## 许可证

本仓库采用 MIT License 开源。
