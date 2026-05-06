from flask import Flask, send_from_directory, session, redirect, request, jsonify
from api_admin import admin_api
from api_student import student_api
from api_visitor import visitor_api
import hashlib
import os

from db_config import get_conn

app = Flask(__name__, static_folder="static")
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-me-in-local-env")

# 正确注册蓝图（url_prefix 只加一次，每个子API的路由里不要再加 /api/admin 这类前缀）
app.register_blueprint(admin_api, url_prefix="/api/admin")
app.register_blueprint(student_api, url_prefix="/api/student")
app.register_blueprint(visitor_api, url_prefix="/api/visitor")

# 管理员登录接口
@app.route('/api/admin/login', methods=['POST'])
def admin_login():
    data = request.json
    phone = data.get('phone')
    password = data.get('password')
    if not phone or not password:
        return jsonify(success=False, message="手机号和密码必填")
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM dorm_manager WHERE phone=%s AND password=%s", (phone, password_hash))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        session['admin_id'] = row[0]
        session['admin_name'] = row[1]
        return jsonify(success=True, role="admin")
    else:
        return jsonify(success=False, message="手机号或密码错误")

# 学生登录接口
@app.route('/api/student/login', methods=['POST'])
def student_login():
    data = request.json
    student_no = data.get('student_no')
    password = data.get('password')
    if not student_no or not password:
        return jsonify(success=False, message="学号和密码必填")
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM student WHERE student_no=%s AND password=%s", (student_no, password_hash))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        session.clear()  # 清空别的登录
        session['student_id'] = row[0]
        session['student_name'] = row[1]
        return jsonify(success=True, role="student")
    else:
        return jsonify(success=False, message="学号或密码错误")

# 管理员登出接口
@app.route('/api/admin/logout', methods=['POST'])
def admin_logout():
    session.clear()
    return jsonify(success=True)

# 学生登出接口
@app.route('/api/student/logout', methods=['POST'])
def student_logout():
    session.clear()
    return jsonify(success=True)

# 静态文件服务
@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory(app.static_folder, filename)

# 登录页
@app.route('/login.html')
def login_page():
    return send_from_directory(app.static_folder, 'login.html')

# 管理员主页（需登录）
@app.route('/admin_manager.html')
def admin_page():
    if not session.get('admin_id'):
        return redirect('/login.html')
    return send_from_directory(app.static_folder, 'admin_manager.html')

# 学生主页（需登录）
@app.route('/student_info.html')
def student_page():
    if not session.get('student_id'):
        return redirect('/login.html')
    return send_from_directory(app.static_folder, 'student_info.html')

# 根路径：判断是否登录，跳转
@app.route('/')
def index():
    if session.get('admin_id'):
        return redirect('/admin_manager.html')
    elif session.get('student_id'):
        return redirect('/student_info.html')
    else:
        return redirect('/login.html')

if __name__ == "__main__":
    app.run(debug=True)
