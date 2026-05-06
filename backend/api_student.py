from flask import Blueprint, request, jsonify, session
import hashlib

from db_config import get_conn

student_api = Blueprint('student_api', __name__)

# 学生登录
@student_api.route('/login', methods=['POST'])
def student_login():
    data = request.json
    student_no = data.get('student_no')
    password = data.get('password')
    if not student_no or not password:
        return jsonify(success=False, message="学号和密码必填")
    password_hash = hashlib.sha256(password.encode('utf-8')).hexdigest()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.student_no, s.name, s.gender, s.grade, s.phone, s.remark,
               b.dorm_building, b.dorm_room_number, b.bed_number
        FROM student s
        LEFT JOIN bed b ON s.bed_id = b.id
        WHERE s.student_no=%s AND s.password=%s
    """, (student_no, password_hash))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        session['student_id'] = row[0]
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="学号或密码错误")

# 退出
@student_api.route('/logout', methods=['POST'])
def student_logout():
    session.pop('student_id', None)
    return jsonify(success=True)

# 当前学生信息
@student_api.route('/current', methods=['GET'])
def student_current():
    student_id = session.get('student_id')
    if not student_id:
        return jsonify(success=False, message="未登录")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.student_no, s.name, s.gender, s.grade, s.phone, s.remark,
               b.dorm_building, b.dorm_room_number, b.bed_number
        FROM student s
        LEFT JOIN bed b ON s.bed_id = b.id
        WHERE s.id=%s
    """, (student_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        return jsonify(success=True, data=dict(zip(
            ['id','student_no','name','gender','grade','phone','remark',
             'dorm_building','dorm_room_number','bed_number'], row)))
    else:
        return jsonify(success=False, message="未找到学生")

# 个人信息
@student_api.route('/info', methods=['GET'])
def student_info():
    return student_current()

# 本宿舍奖项
@student_api.route('/awards', methods=['GET'])
def student_awards():
    student_id = session.get('student_id')
    if not student_id:
        return jsonify(success=False, message="未登录")

    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.callproc('GetDormAwards', (student_id,))
        awards = []
        for row in cur.fetchall():
            awards.append({
                'id': row[0],
                'building': row[1],
                'room_number': row[2],
                'award_type': row[3],
                'term': row[4],
                'reason': row[5],
                'award_time': row[6]
            })
        return jsonify(success=True, data=awards)
    except Exception as e:
        return jsonify(success=False, message=str(e))
    finally:
        cur.close()
        conn.close()

        
# 本宿舍检查
@student_api.route('/checks', methods=['GET'])
def student_checks():
    student_id = session.get('student_id')
    if not student_id:
        return jsonify(success=False, message="未登录")

    conn = get_conn()
    cur = conn.cursor()

    try:
        # 使用 WITH 子句在一个查询中完成所有操作
        cur.execute("""
            WITH StudentDorm AS (
                SELECT 
                    d.id AS dorm_id,
                    b.dorm_building,
                    b.dorm_room_number
                FROM student s
                JOIN bed b ON s.bed_id = b.id
                JOIN dormitory d 
                    ON b.dorm_building = d.building 
                    AND b.dorm_room_number = d.room_number
                WHERE s.id = %s
            ),
            DormChecks AS (
                SELECT 
                    c.id,
                    d.building,
                    d.room_number,
                    c.check_date,
                    c.checker,
                    c.score,
                    c.remarks,
                    c.rectified
                FROM dorm_check c
                JOIN dormitory d ON c.dorm_id = d.id
                JOIN StudentDorm sd ON d.id = sd.dorm_id
                ORDER BY c.check_date DESC, c.id DESC
            )
            SELECT * FROM DormChecks
        """, (student_id,))

        results = cur.fetchall()

        # 处理查询结果
        if not results:
            # 检查是否因为学生没有床位而没有数据
            cur.execute("SELECT bed_id FROM student WHERE id = %s", (student_id,))
            if cur.fetchone()[0] is None:
                return jsonify(success=False, message="未关联床位")

            return jsonify(success=True, data=[])

        checks = []
        for row in results:
            checks.append(dict(zip(
                ['id', 'building', 'room_number', 'check_date', 'checker', 'score', 'remarks', 'rectified'],
                row
            )))

        return jsonify(success=True, data=checks)

    except Exception as e:
        return jsonify(success=False, message=str(e))

    finally:
        cur.close()
        conn.close()


# 作为被访学生的访客记录
@student_api.route('/visitors', methods=['GET'])
def student_visitors():
    student_id = session.get('student_id')
    if not student_id:
        return jsonify(success=False, message="未登录")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT v.id, v.name, d.building, d.room_number, v.visit_time, v.leave_time, v.purpose
        FROM visitor v
        LEFT JOIN dormitory d ON v.dorm_id = d.id
        WHERE v.student_id=%s
        ORDER BY v.visit_time DESC, v.id DESC
    """, (student_id,))
    visitors = [dict(zip(['id','name','building','room_number','visit_time','leave_time','purpose'], r)) for r in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(success=True, data=visitors)

# 楼管信息
@student_api.route('/admin_info', methods=['GET'])
def student_admin_info():
    student_id = session.get('student_id')
    if not student_id:
        return jsonify(success=False, message="未登录")
    conn = get_conn()
    cur = conn.cursor()
    # 先查学生宿舍楼
    cur.execute("SELECT b.dorm_building FROM student s LEFT JOIN bed b ON s.bed_id=b.id WHERE s.id=%s", (student_id,))
    row = cur.fetchone()
    if not row or not row[0]:
        cur.close(); conn.close()
        return jsonify(success=False, message="未分配宿舍楼")
    building = row[0]
    # 查管理员（假设 dorm_manager 表有 building 字段，且为单楼管/多楼管都可）
    cur.execute("SELECT name, phone FROM dorm_manager WHERE building=%s", (building,))
    admins = [dict(zip(['name', 'phone'], r)) for r in cur.fetchall()]
    cur.close(); conn.close()
    if admins:
        return jsonify(success=True, data={'building': building, 'admins': admins})
    else:
        return jsonify(success=False, message=f"{building}楼未找到管理员信息")

# 学生修改自己密码
@student_api.route('/change_password', methods=['POST'])
def student_change_password():
    if not session.get('student_id'):
        return jsonify(success=False, message="未登录")
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    if not old_password or not new_password:
        return jsonify(success=False, message="请填写完整信息")
    student_id = session['student_id']
    old_password_hash = hashlib.sha256(old_password.encode('utf-8')).hexdigest()
    new_password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM student WHERE id=%s AND password=%s", (student_id, old_password_hash))
    if not cur.fetchone():
        cur.close(); conn.close()
        return jsonify(success=False, message="原密码错误")
    cur.execute("UPDATE student SET password=%s WHERE id=%s", (new_password_hash, student_id))
    conn.commit()
    cur.close(); conn.close()
    return jsonify(success=True, message="密码修改成功")
