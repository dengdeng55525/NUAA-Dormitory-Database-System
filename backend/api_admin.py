from flask import Blueprint, request, jsonify, session
import hashlib
import csv
from io import StringIO
from flask import Response

from db_config import get_conn

admin_api = Blueprint('admin_api', __name__)

@admin_api.route('/students', methods=['GET'])
def get_students():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))
    offset = (page-1) * per_page

    graduated = request.args.get('graduated')
    student_no = request.args.get('student_no')
    name = request.args.get('name')
    gender = request.args.get('gender')
    grade = request.args.get('grade')
    phone = request.args.get('phone')
    dorm_building = request.args.get('dorm_building')
    dorm_room_number = request.args.get('dorm_room_number')
    bed_number = request.args.get('bed_number')

    where = "1=1"
    params = []
    if graduated is not None:
        where += " AND graduated=%s"
        params.append(int(graduated))
    if student_no:
        where += " AND student_no LIKE %s"
        params.append(f"%{student_no}%")
    if name:
        where += " AND name LIKE %s"
        params.append(f"%{name}%")
    if gender:
        where += " AND gender=%s"
        params.append(gender)
    if grade:
        where += " AND grade=%s"
        params.append(grade)
    if phone:
        where += " AND phone LIKE %s"
        params.append(f"%{phone}%")
    if dorm_building:
        where += " AND dorm_building LIKE %s"
        params.append(f"%{dorm_building}%")
    if dorm_room_number:
        where += " AND dorm_room_number LIKE %s"
        params.append(f"%{dorm_room_number}%")
    if bed_number:
        where += " AND bed_number=%s"
        params.append(bed_number)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"SELECT COUNT(*) FROM v_student_bed WHERE {where}", params)
    total = cur.fetchone()[0]
    cur.execute(f"""
        SELECT student_id, student_no, name, gender, grade, phone, remark, graduated,
               dorm_building, dorm_room_number, bed_number
        FROM v_student_bed
        WHERE {where}
        ORDER BY student_id DESC
        LIMIT %s OFFSET %s
    """, params + [per_page, offset])
    data = [dict(zip(['id','student_no','name','gender','grade','phone','remark','graduated',
                      'dorm_building','dorm_room_number','bed_number'], row)) for row in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(success=True, data=data, total=total, page=page, per_page=per_page)


@admin_api.route('/students/<int:sid>', methods=['GET'])
def get_student(sid):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT s.id, s.student_no, s.name, s.gender, s.grade, s.phone, s.remark, s.graduated,
               b.dorm_building, b.dorm_room_number, b.bed_number
        FROM student s
        LEFT JOIN bed b ON s.bed_id = b.id
        WHERE s.id=%s
    """, (sid,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        return jsonify(success=True, data=dict(zip(['id','student_no','name','gender','grade','phone','remark','graduated',
                                                    'dorm_building','dorm_room_number','bed_number'], row)))
    else:
        return jsonify(success=False, message="未找到该学生")

@admin_api.route('/students', methods=['POST'])
def add_student():
    d = request.json
    try:
        conn = get_conn()
        cur = conn.cursor()
        bed_id = None
        if d.get('dorm_building') and d.get('dorm_room_number') and d.get('bed_number'):
            cur.execute("SELECT id FROM bed WHERE dorm_building=%s AND dorm_room_number=%s AND bed_number=%s",
                        (d['dorm_building'], d['dorm_room_number'], d['bed_number']))
            bed_row = cur.fetchone()
            if bed_row:
                bed_id = bed_row[0]
        password = hashlib.sha256(d['student_no'].encode('utf-8')).hexdigest()
        cur.execute("INSERT INTO student (student_no, name, gender, grade, phone, password, bed_id, remark, graduated) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,0)",
            (d['student_no'], d['name'], d['gender'], d['grade'], d.get('phone'), password, bed_id, d.get('remark')))
        if bed_id:
            cur.execute("UPDATE bed SET student_no=%s, status='已入住' WHERE id=%s", (d['student_no'], bed_id))
        conn.commit()
        cur.close(); conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))

@admin_api.route('/students/<int:sid>', methods=['PUT'])
def edit_student(sid):
    d = request.json
    try:
        conn = get_conn()
        cur = conn.cursor()
        bed_id = None
        if d.get('dorm_building') and d.get('dorm_room_number') and d.get('bed_number'):
            cur.execute("SELECT id FROM bed WHERE dorm_building=%s AND dorm_room_number=%s AND bed_number=%s",
                        (d['dorm_building'], d['dorm_room_number'], d['bed_number']))
            bed_row = cur.fetchone()
            if bed_row:
                bed_id = bed_row[0]
        cur.execute("SELECT bed_id, student_no FROM student WHERE id=%s", (sid,))
        old_row = cur.fetchone()
        old_bed_id, old_student_no = (old_row if old_row else (None, None))
        cur.execute("UPDATE student SET student_no=%s, name=%s, gender=%s, grade=%s, phone=%s, bed_id=%s, remark=%s WHERE id=%s",
            (d['student_no'], d['name'], d['gender'], d['grade'], d.get('phone'), bed_id, d.get('remark'), sid))
        # 只用"未入住""已入住"，不再用"空闲"
        if old_bed_id and old_bed_id != bed_id:
            cur.execute("UPDATE bed SET student_no=NULL, status='未入住' WHERE id=%s", (old_bed_id,))
        if bed_id:
            cur.execute("UPDATE bed SET student_no=%s, status='已入住' WHERE id=%s", (d['student_no'], bed_id))
        conn.commit()
        cur.close(); conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))

@admin_api.route('/students/<int:sid>', methods=['DELETE'])
def delete_student(sid):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT bed_id, student_no FROM student WHERE id=%s", (sid,))
        row = cur.fetchone()
        bed_id = row[0] if row else None
        student_no = row[1] if row else None
        cur.execute("DELETE FROM student WHERE id=%s", (sid,))
        if bed_id:
            cur.execute("UPDATE bed SET student_no=NULL, status='未入住' WHERE id=%s", (bed_id,))
        conn.commit()
        cur.close(); conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))


@admin_api.route('/students/graduate/<int:year>', methods=['POST'])
def graduate_students(year):
    try:
        conn = get_conn()
        cur = conn.cursor()
        # 调用存储过程
        cur.callproc('GraduateStudentsProc', (year,))
        conn.commit()
        cur.close(); conn.close()
        return jsonify(success=True, message="毕业处理完成")
    except Exception as e:
        return jsonify(success=False, message=str(e))


# ========== 宿舍奖项 ==========
@admin_api.route('/dorm_awards', methods=['GET'])
def get_dorm_awards():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))
    offset = (page-1) * per_page
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM dorm_award")
    total = cur.fetchone()[0]
    cur.execute("""
        SELECT a.id, a.award_type, a.term, a.reason, a.award_time,
               d.building, d.room_number
        FROM dorm_award a
        LEFT JOIN dormitory d ON a.dorm_id = d.id
        ORDER BY a.award_time DESC, a.id DESC
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    data = [dict(zip(['id','award_type','term','reason','award_time','building','room_number'], row)) for row in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(success=True, data=data, total=total, page=page, per_page=per_page)

@admin_api.route('/dorm_awards', methods=['POST'])
def add_dorm_award():
    d = request.json
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM dormitory WHERE building=%s AND room_number=%s",
                    (d['building'], d['room_number']))
        dorm_row = cur.fetchone()
        dorm_id = dorm_row[0] if dorm_row else None
        cur.execute("INSERT INTO dorm_award (dorm_id, award_type, term, reason, award_time) VALUES (%s, %s, %s, %s, %s)",
                    (dorm_id, d['award_type'], d['term'], d.get('reason'), d['award_time']))
        conn.commit()
        cur.close(); conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))

@admin_api.route('/dorm_awards/<int:aid>', methods=['PUT'])
def edit_dorm_award(aid):
    d = request.json
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM dormitory WHERE building=%s AND room_number=%s",
                    (d['building'], d['room_number']))
        dorm_row = cur.fetchone()
        dorm_id = dorm_row[0] if dorm_row else None
        cur.execute("UPDATE dorm_award SET dorm_id=%s, award_type=%s, term=%s, reason=%s, award_time=%s WHERE id=%s",
                    (dorm_id, d['award_type'], d['term'], d.get('reason'), d['award_time'], aid))
        conn.commit()
        cur.close(); conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))

@admin_api.route('/dorm_awards/<int:aid>', methods=['DELETE'])
def delete_dorm_award(aid):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM dorm_award WHERE id=%s", (aid,))
        conn.commit()
        cur.close(); conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))

# ========== 宿舍检查 ==========
@admin_api.route('/dorm_checks', methods=['GET'])
def get_dorm_checks():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))
    offset = (page-1) * per_page
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM dorm_check")
    total = cur.fetchone()[0]
    cur.execute("""
        SELECT c.id, c.check_date, c.checker, c.score, c.remarks, c.rectified,
               d.building, d.room_number
        FROM dorm_check c
        LEFT JOIN dormitory d ON c.dorm_id = d.id
        ORDER BY c.check_date DESC, c.id DESC
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    data = []
    for row in cur.fetchall():
        item = dict(zip(['id','check_date','checker','score','remarks','rectified','building','room_number'], row))
        # 新增逻辑：分数大于85分直接显示无需整改，rectified=1
        if item.get('score', 0) is not None and int(item['score']) > 85:
            item['rectified'] = 1
            item['rectify_text'] = "无需整改"
        else:
            item['rectify_text'] = "已整改" if item['rectified'] else "未整改"
        data.append(item)
    cur.close(); conn.close()
    return jsonify(success=True, data=data, total=total, page=page, per_page=per_page)

@admin_api.route('/dorm_checks', methods=['POST'])
def add_dorm_check():
    d = request.json
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM dormitory WHERE building=%s AND room_number=%s",
                    (d['building'], d['room_number']))
        dorm_row = cur.fetchone()
        dorm_id = dorm_row[0] if dorm_row else None
        cur.execute("INSERT INTO dorm_check (dorm_id, check_date, checker, score, remarks, rectified) VALUES (%s, %s, %s, %s, %s, %s)",
                    (dorm_id, d['check_date'], d['checker'], d['score'], d.get('remarks'), d.get('rectified',0)))
        conn.commit()
        cur.close(); conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))

@admin_api.route('/dorm_checks/<int:cid>', methods=['PUT'])
def edit_dorm_check(cid):
    d = request.json
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM dormitory WHERE building=%s AND room_number=%s",
                    (d['building'], d['room_number']))
        dorm_row = cur.fetchone()
        dorm_id = dorm_row[0] if dorm_row else None
        cur.execute("UPDATE dorm_check SET dorm_id=%s, check_date=%s, checker=%s, score=%s, remarks=%s, rectified=%s WHERE id=%s",
                    (dorm_id, d['check_date'], d['checker'], d['score'], d.get('remarks'), d.get('rectified', 0), cid))
        conn.commit()
        cur.close(); conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))

@admin_api.route('/dorm_checks/<int:cid>', methods=['DELETE'])
def delete_dorm_check(cid):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM dorm_check WHERE id=%s", (cid,))
        conn.commit()
        cur.close(); conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))

# ========== 访客 ==========
@admin_api.route('/visitors', methods=['GET'])
def get_visitors():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))
    offset = (page-1) * per_page
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM visitor")
    total = cur.fetchone()[0]
    cur.execute("""
        SELECT v.id, v.name, v.visit_time, v.leave_time, v.purpose,
               d.building, d.room_number,
               s.student_no, s.name as student_name
        FROM visitor v
        LEFT JOIN dormitory d ON v.dorm_id = d.id
        LEFT JOIN student s ON v.student_id = s.id
        ORDER BY v.visit_time DESC, v.id DESC
        LIMIT %s OFFSET %s
    """, (per_page, offset))
    data = [dict(zip(['id','name','visit_time','leave_time','purpose','building','room_number','student_no','student_name'], row)) for row in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(success=True, data=data, total=total, page=page, per_page=per_page)

@admin_api.route('/visitors/<int:vid>', methods=['PUT'])
def edit_visitor(vid):
    d = request.json
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT id FROM dormitory WHERE building=%s AND room_number=%s",
                    (d['building'], d['room_number']))
        dorm_row = cur.fetchone()
        dorm_id = dorm_row[0] if dorm_row else None
        student_id = None
        if d.get('student_no'):
            cur.execute("SELECT id FROM student WHERE student_no=%s", (d['student_no'],))
            stu_row = cur.fetchone()
            if stu_row:
                student_id = stu_row[0]
        cur.execute("UPDATE visitor SET name=%s, dorm_id=%s, student_id=%s, visit_time=%s, leave_time=%s, purpose=%s WHERE id=%s",
                    (d['name'], dorm_id, student_id, d['visit_time'], d.get('leave_time'), d.get('purpose'), vid))
        conn.commit()
        cur.close(); conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))

@admin_api.route('/visitors/<int:vid>', methods=['DELETE'])
def delete_visitor(vid):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("DELETE FROM visitor WHERE id=%s", (vid,))
        conn.commit()
        cur.close(); conn.close()
        return jsonify(success=True)
    except Exception as e:
        return jsonify(success=False, message=str(e))

@admin_api.route('/search', methods=['GET'])
def global_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify(success=True, data=[])
    conn = get_conn()
    cur = conn.cursor()
    results = {}
    # 学生信息
    cur.execute("""
        SELECT s.id, s.student_no, s.name, s.gender, s.grade, s.phone,
            b.dorm_building, b.dorm_room_number, b.bed_number
        FROM student s
        LEFT JOIN bed b ON s.bed_id = b.id
        WHERE s.student_no LIKE %s OR s.name LIKE %s
           OR b.dorm_building LIKE %s OR b.dorm_room_number LIKE %s
    """, ['%' + q + '%'] * 4)
    results['students'] = [dict(zip(['id','student_no','name','gender','grade','phone','dorm_building','dorm_room_number','bed_number'], row)) for row in cur.fetchall()]
    # 宿舍奖项
    cur.execute("""
        SELECT a.id, d.building, d.room_number, a.award_type, a.term, a.reason, a.award_time
        FROM dorm_award a
        LEFT JOIN dormitory d ON a.dorm_id = d.id
        WHERE d.building LIKE %s OR d.room_number LIKE %s OR a.award_type LIKE %s OR a.reason LIKE %s
    """, ['%' + q + '%'] * 4)
    results['awards'] = [dict(zip(['id','building','room_number','award_type','term','reason','award_time'], row)) for row in cur.fetchall()]
    # 宿舍检查
    cur.execute("""
        SELECT c.id, d.building, d.room_number, c.check_date, c.checker, c.score, c.remarks, c.rectified
        FROM dorm_check c
        LEFT JOIN dormitory d ON c.dorm_id = d.id
        WHERE d.building LIKE %s OR d.room_number LIKE %s OR c.checker LIKE %s
    """, ['%' + q + '%'] * 3)
    results['checks'] = [dict(zip(['id','building','room_number','check_date','checker','score','remarks','rectified'], row)) for row in cur.fetchall()]
    # 访客记录
    cur.execute("""
        SELECT v.id, v.name, d.building, d.room_number, s.student_no, s.name as student_name, v.visit_time, v.leave_time, v.purpose
        FROM visitor v
        LEFT JOIN dormitory d ON v.dorm_id = d.id
        LEFT JOIN student s ON v.student_id = s.id
        WHERE v.name LIKE %s OR d.building LIKE %s OR d.room_number LIKE %s OR s.student_no LIKE %s OR s.name LIKE %s
    """, ['%' + q + '%'] * 5)
    results['visitors'] = [dict(zip(['id','name','building','room_number','student_no','student_name','visit_time','leave_time','purpose'], row)) for row in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(success=True, data=results)

@admin_api.route('/current_admin', methods=['GET'])
def get_current_admin():
    admin_id = session.get('admin_id')
    if not admin_id:
        return jsonify(success=False, message="未登录")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT name, building FROM dorm_manager WHERE id=%s", (admin_id,))
    row = cur.fetchone()
    cur.close(); conn.close()
    if row:
        return jsonify(success=True, data={'name': row[0], 'building': row[1]})
    else:
        return jsonify(success=False, message="未找到管理员")

@admin_api.route('/login', methods=['POST'])
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
        return jsonify(success=True)
    else:
        return jsonify(success=False, message="手机号或密码错误")

@admin_api.route('/logout', methods=['POST'])
def admin_logout():
    session.clear()
    return jsonify(success=True)

# 管理员自己修改密码
@admin_api.route('/change_password', methods=['POST'])
def admin_change_password():
    if not session.get('admin_id'):
        return jsonify(success=False, message="未登录")
    data = request.json
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    if not old_password or not new_password:
        return jsonify(success=False, message="请填写完整信息")
    admin_id = session['admin_id']
    old_password_hash = hashlib.sha256(old_password.encode('utf-8')).hexdigest()
    new_password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT id FROM dorm_manager WHERE id=%s AND password=%s", (admin_id, old_password_hash))
    if not cur.fetchone():
        cur.close(); conn.close()
        return jsonify(success=False, message="原密码错误")
    cur.execute("UPDATE dorm_manager SET password=%s WHERE id=%s", (new_password_hash, admin_id))
    conn.commit()
    cur.close(); conn.close()
    return jsonify(success=True, message="密码修改成功")

# 管理员重置学生密码接口
@admin_api.route('/reset_student_password', methods=['POST'])
def admin_reset_student_password():
    if not session.get('admin_id'):
        return jsonify(success=False, message="未登录")
    data = request.json
    student_no = data.get('student_no', '').strip()
    student_name = data.get('student_name', '').strip()
    new_password = data.get('new_password')

    if not new_password or (not student_no and not student_name):
        return jsonify(success=False, message="请填写学生学号或姓名和新密码")

    conn = get_conn()
    cur = conn.cursor()

    if student_no:
        cur.execute("SELECT id, student_no, name FROM student WHERE student_no=%s", (student_no,))
    else:
        cur.execute("SELECT id, student_no, name FROM student WHERE name LIKE %s", ('%' + student_name + '%',))
    students = cur.fetchall()
    if not students:
        cur.close(); conn.close()
        return jsonify(success=False, message="未找到该学生")
    if len(students) > 1:
        res = [{'id': s[0], 'student_no': s[1], 'name': s[2]} for s in students]
        cur.close(); conn.close()
        return jsonify(success=False, multi=True, students=res, message="查到多个学生，请精确输入学号")
    student_id, s_no, s_name = students[0]
    new_password_hash = hashlib.sha256(new_password.encode('utf-8')).hexdigest()
    cur.execute("UPDATE student SET password=%s WHERE id=%s", (new_password_hash, student_id))
    conn.commit()
    cur.close(); conn.close()
    msg = f"学号为{s_no}姓名为{s_name}的学生密码修改成功"
    return jsonify(success=True, message=msg, student_no=s_no, student_name=s_name)

# ========== 统计分析相关API ==========

@admin_api.route('/stats/occupancy')
def stats_occupancy():
    conn = get_conn()
    cur = conn.cursor()
    ALL_BUILDINGS = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
    cur.execute("SELECT building, SUM(capacity) FROM dormitory GROUP BY building")
    total_beds_dict = {row[0]: row[1] for row in cur.fetchall()}
    cur.execute("""
        SELECT dorm_building, COUNT(*) 
        FROM bed 
        WHERE student_no IS NOT NULL AND student_no <> ''
        GROUP BY dorm_building
    """)
    used_beds_dict = {row[0]: row[1] for row in cur.fetchall()}
    result = []
    for building in ALL_BUILDINGS:
        total_beds = total_beds_dict.get(building, 0) or 0
        used_beds = used_beds_dict.get(building, 0) or 0
        rate = used_beds / total_beds if total_beds else 0
        result.append({
            'building': building,
            'used_beds': used_beds,
            'total_beds': total_beds,
            'rate': round(rate, 4)
        })
    cur.close(); conn.close()
    return jsonify(success=True, data=result)

@admin_api.route('/stats/award_ratio')
def stats_award_ratio():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM dorm_check WHERE score>85")
    award = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM dorm_check WHERE score<=85")
    punish = cur.fetchone()[0]
    cur.close(); conn.close()
    return jsonify(success=True, data={"award": award, "punish": punish})

@admin_api.route('/stats/visitor_types')
def stats_visitor_types():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT purpose, COUNT(*) FROM visitor GROUP BY purpose")
    res = [{"type": row[0] or "其他", "count": row[1]} for row in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(success=True, data=res)

# ========== 宿舍床位信息一览 API===========
@admin_api.route('/beds', methods=['GET'])
def get_beds():
    page = int(request.args.get('page', 1))
    per_page = int(request.args.get('per_page', 100))
    offset = (page-1) * per_page

    dorm_building = request.args.get('dorm_building')
    dorm_room_number = request.args.get('dorm_room_number')
    bed_number = request.args.get('bed_number')
    status = request.args.get('status')
    student_no = request.args.get('student_no')
    student_name = request.args.get('student_name')

    where = "1=1"
    params = []

    if dorm_building:
        where += " AND b.dorm_building LIKE %s"
        params.append(f"%{dorm_building}%")
    if dorm_room_number:
        where += " AND b.dorm_room_number LIKE %s"
        params.append(f"%{dorm_room_number}%")
    if bed_number:
        where += " AND b.bed_number=%s"
        params.append(bed_number)
    if status:
        where += " AND b.status=%s"
        params.append(status)
    if student_no:
        where += " AND b.student_no LIKE %s"
        params.append(f"%{student_no}%")
    if student_name:
        where += " AND s.name LIKE %s"
        params.append(f"%{student_name}%")

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT COUNT(*) 
        FROM bed b
        LEFT JOIN student s ON b.student_no = s.student_no
        WHERE {where}
    """, params)
    total = cur.fetchone()[0]
    cur.execute(f"""
        SELECT b.dorm_building, b.dorm_room_number, b.bed_number, b.status, b.student_no, s.name
        FROM bed b
        LEFT JOIN student s ON b.student_no = s.student_no
        WHERE {where}
        ORDER BY b.dorm_building, b.dorm_room_number, b.bed_number
        LIMIT %s OFFSET %s
    """, params + [per_page, offset])
    data = [dict(zip(['dorm_building','dorm_room_number','bed_number','status','student_no','student_name'], row)) for row in cur.fetchall()]
    cur.close(); conn.close()
    return jsonify(success=True, data=data, total=total, page=page, per_page=per_page)


@admin_api.route('/students/export', methods=['GET'])
def export_students():
    # 参数同/students
    graduated = request.args.get('graduated')
    student_no = request.args.get('student_no')
    name = request.args.get('name')
    gender = request.args.get('gender')
    grade = request.args.get('grade')
    phone = request.args.get('phone')
    dorm_building = request.args.get('dorm_building')
    dorm_room_number = request.args.get('dorm_room_number')
    bed_number = request.args.get('bed_number')

    where = "1=1"
    params = []
    if graduated is not None:
        where += " AND s.graduated=%s"
        params.append(int(graduated))
    if student_no:
        where += " AND s.student_no LIKE %s"
        params.append(f"%{student_no}%")
    if name:
        where += " AND s.name LIKE %s"
        params.append(f"%{name}%")
    if gender:
        where += " AND s.gender=%s"
        params.append(gender)
    if grade:
        where += " AND s.grade=%s"
        params.append(grade)
    if phone:
        where += " AND s.phone LIKE %s"
        params.append(f"%{phone}%")
    if dorm_building:
        where += " AND b.dorm_building LIKE %s"
        params.append(f"%{dorm_building}%")
    if dorm_room_number:
        where += " AND b.dorm_room_number LIKE %s"
        params.append(f"%{dorm_room_number}%")
    if bed_number:
        where += " AND b.bed_number=%s"
        params.append(bed_number)

    conn = get_conn()
    cur = conn.cursor()
    cur.execute(f"""
        SELECT s.student_no, s.name, s.gender, s.grade, s.phone, s.remark, s.graduated,
               b.dorm_building, b.dorm_room_number, b.bed_number
        FROM student s
        LEFT JOIN bed b ON s.bed_id = b.id
        WHERE {where}
        ORDER BY s.id DESC
    """, params)
    rows = cur.fetchall()
    cur.close(); conn.close()

    output = StringIO()
    writer = csv.writer(output)
    # 表头
    writer.writerow(['学号','姓名','性别','年级','电话','备注','是否毕业','宿舍楼','房号','床号'])
    for row in rows:
        # 性别、是否毕业可映射为中文
        gender_map = {'M': '男', 'F': '女'}
        graduated_map = {0: '否', 1: '是'}
        row = list(row)
        row[2] = gender_map.get(row[2], row[2])
        row[6] = graduated_map.get(row[6], row[6])
        writer.writerow(row)
    output.seek(0)
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv',
        headers={
            "Content-Disposition": "attachment; filename=students.csv"
        }
    )
# ========== 统计分析：聚合函数相关API ==========

@admin_api.route('/stats/student_count', methods=['GET'])
def stats_student_count():
    graduated = request.args.get('graduated')
    conn = get_conn()
    cur = conn.cursor()
    sql = "SELECT COUNT(*) FROM student"
    params = []
    if graduated is not None:
        sql += " WHERE graduated=%s"
        params.append(int(graduated))
    cur.execute(sql, params)
    count = cur.fetchone()[0]
    cur.close(); conn.close()
    return jsonify(success=True, data={"student_count": count})

@admin_api.route('/stats/student_per_grade', methods=['GET'])
def stats_student_per_grade():
    graduated = request.args.get('graduated')
    conn = get_conn()
    cur = conn.cursor()
    sql = "SELECT grade, COUNT(*) FROM student"
    params = []
    if graduated is not None:
        sql += " WHERE graduated=%s"
        params.append(int(graduated))
    sql += " GROUP BY grade ORDER BY grade"
    cur.execute(sql, params)
    rows = cur.fetchall()
    cur.close(); conn.close()
    data = [{"grade": row[0], "student_count": row[1]} for row in rows]
    return jsonify(success=True, data=data)


# 各宿舍获奖次数统计API
@admin_api.route('/stats/dorm_award_counts', methods=['GET'])
def stats_dorm_award_counts():
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 获取各宿舍获奖次数
        cur.execute("""
            SELECT d.building, d.room_number, COUNT(a.id) AS award_count
            FROM dormitory d
            LEFT JOIN dorm_award a ON d.id = a.dorm_id
            GROUP BY d.id
            ORDER BY d.building, d.room_number
        """)
        awards = [dict(zip(['building', 'room_number', 'award_count'], row))
                  for row in cur.fetchall()]

        return jsonify(success=True, data=awards)
    except Exception as e:
        return jsonify(success=False, message=str(e))
    finally:
        cur.close();
        conn.close()


# 各宿舍检查平均分统计API
@admin_api.route('/stats/dorm_check_scores', methods=['GET'])
def stats_dorm_check_scores():
    conn = get_conn()
    cur = conn.cursor()
    try:
        # 获取各宿舍的平均检查分
        cur.execute("""
            SELECT d.building, d.room_number, 
                   AVG(c.score) AS avg_score,
                   COUNT(c.id) AS check_count
            FROM dormitory d
            LEFT JOIN dorm_check c ON d.id = c.dorm_id
            GROUP BY d.id
            ORDER BY d.building, d.room_number
        """)
        scores = []
        for row in cur.fetchall():
            avg_score = float(row[2]) if row[2] else 0
            scores.append({
                "building": row[0],
                "room_number": row[1],
                "avg_score": round(avg_score, 2),
                "check_count": row[3]
            })
        return jsonify(success=True, data=scores)
    except Exception as e:
        return jsonify(success=False, message=str(e))
    finally:
        cur.close();
        conn.close()


