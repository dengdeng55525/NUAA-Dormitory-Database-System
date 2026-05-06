from flask import Blueprint, request, jsonify

from db_config import get_conn

visitor_api = Blueprint('visitor_api', __name__)

@visitor_api.route('/add', methods=['POST'])
def add_visitor():
    data = request.json
    name = data.get('name')
    phone = data.get('phone')
    # 宿舍号如A0101，前端可分为building='A' room_number='0101'
    building = data.get('building')  # 'A'
    room_number = data.get('room_number')  # '0101'
    student_no = data.get('student_no')  # 可选，被访学生学号
    student_name = data.get('student_name')  # 可选，被访学生姓名
    visit_time = data.get('visit_time')
    leave_time = data.get('leave_time')
    purpose = data.get('purpose')

    if not (name and phone and building and room_number and visit_time and purpose):
        return jsonify(success=False, message="信息不完整")

    conn = get_conn()
    cur = conn.cursor()

    # 查 dorm_id
    cur.execute("SELECT id FROM dormitory WHERE building=%s AND room_number=%s", (building, room_number))
    dorm_row = cur.fetchone()
    if not dorm_row:
        cur.close(); conn.close()
        return jsonify(success=False, message="宿舍不存在")
    dorm_id = dorm_row[0]

    # 查 student_id（可选，允许未填）
    student_id = None
    if student_no:
        cur.execute("SELECT id FROM student WHERE student_no=%s", (student_no,))
        stu_row = cur.fetchone()
        if stu_row:
            student_id = stu_row[0]

    # 插入 visitor
    cur.execute(
        "INSERT INTO visitor (name, dorm_id, student_id, visit_time, leave_time, purpose) VALUES (%s, %s, %s, %s, %s, %s)",
        (name, dorm_id, student_id, visit_time, leave_time, purpose)
    )
    conn.commit()
    cur.close(); conn.close()
    return jsonify(success=True, message="登记成功")
