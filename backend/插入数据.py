import pymysql
import random
import hashlib
from faker import Faker
from datetime import datetime, timedelta

from db_config import get_db_config

fake = Faker('zh_CN')

db_config = get_db_config()

N_BEDS_PER_DORM = 4
MAX_STUDENTS_PER_BUILDING = 10000
N_VISITORS = 20000

girls_buildings = ['A', 'B', 'C', 'D', 'E', 'F']
boys_buildings  = ['G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P']
all_buildings = girls_buildings + boys_buildings

def sha256_encrypt(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def generate_room_number(building_letter, room_idx):
    floor = room_idx // 64 + 1
    room_on_floor = room_idx % 64 + 1
    return f"{building_letter}{floor:02d}{room_on_floor:02d}"

def insert_managers():
    conn = pymysql.connect(**db_config)
    cur = conn.cursor()
    for letter in all_buildings:
        name = fake.name()
        gender = 'F' if letter in girls_buildings else 'M'
        phone = fake.phone_number()
        account = phone
        password = sha256_encrypt(phone)
        cur.execute(
            "INSERT INTO dorm_manager (name, gender, phone, building, account, password) VALUES (%s, %s, %s, %s, %s, %s)",
            (name, gender, phone, letter, account, password)
        )
    conn.commit()
    cur.close()
    conn.close()
    print(f"已插入{len(all_buildings)}名宿舍管理员。")

def generate_studentid(college, year, major, class_num, gender, girl_count, boy_count):
    college_str = str(college).zfill(2)
    year_str = str(year)[-2:]
    major_str = str(major)
    class_str = str(class_num).zfill(2)
    if gender == 'F':
        serial = str(girl_count + 1).zfill(2)
    else:
        serial = str(boy_count + 1 + girl_count).zfill(2)
    return f"{college_str}{year_str}{major_str}{class_str}{serial}"

def insert_students():
    conn = pymysql.connect(**db_config)
    cur = conn.cursor()
    students = []
    colleges = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,22,24]
    years = [17,18,19,20,21,22,23,24]
    majors = [1,2,3,4,5]
    classes_per_major = [3,4,5]
    students_per_class = 30
    for college in colleges:
        for year in years:
            for major in majors:
                n_class = random.choice(classes_per_major)
                for class_num in range(1, n_class+1):
                    n_girls = random.randint(8,12)
                    n_boys = students_per_class - n_girls
                    girl_count = 0
                    boy_count = 0
                    for idx in range(students_per_class):
                        gender = 'F' if idx < n_girls else 'M'
                        if gender == 'F':
                            studentid = generate_studentid(college, year, major, class_num, gender, girl_count, boy_count)
                            girl_count += 1
                        else:
                            studentid = generate_studentid(college, year, major, class_num, gender, girl_count, boy_count)
                            boy_count += 1
                        name = fake.name_female() if gender == 'F' else fake.name_male()
                        grade = 2000 + int(str(year))
                        phone = fake.phone_number()
                        remark = f"{college}学院{grade}级{major}专业{class_num}班"
                        password = sha256_encrypt(studentid)
                        students.append({
                            'student_no': studentid,
                            'name': name,
                            'gender': gender,
                            'grade': grade,
                            'phone': phone,
                            'password': password,
                            'remark': remark
                        })
    # 分批插入
    batch_size = 1000
    for i in range(0, len(students), batch_size):
        values = [(stu['student_no'], stu['name'], stu['gender'], stu['grade'], stu['phone'], stu['password'], stu['remark'], None)
                  for stu in students[i:i+batch_size]]
        cur.executemany(
            "INSERT INTO student (student_no, name, gender, grade, phone, password, remark, bed_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            values
        )
    conn.commit()
    cur.close()
    conn.close()
    print(f"已插入{len(students)}名学生。")
    return students

def assign_beds_and_fill_tables(students):
    conn = pymysql.connect(**db_config)
    cur = conn.cursor()

    # 获取管理员
    cur.execute("SELECT id, building FROM dorm_manager")
    manager_data = {row[1]: row[0] for row in cur.fetchall()}

    building_student_count = {b: 0 for b in all_buildings}
    dorm_rooms = {}  # (building, room_number): [student_no, ...]
    dorm_id_map = {}
    bed_records = []
    student_bedid_update = []

    girls = [s for s in students if s['gender'] == 'F']
    boys = [s for s in students if s['gender'] == 'M']

    # 女生分配
    girl_building_idx = 0
    girl_building = girls_buildings[girl_building_idx]
    for s in girls:
        if building_student_count[girl_building] >= MAX_STUDENTS_PER_BUILDING:
            girl_building_idx += 1
            if girl_building_idx >= len(girls_buildings):
                raise Exception("女生楼栋不足以容纳所有女生")
            girl_building = girls_buildings[girl_building_idx]
        room_idx = building_student_count[girl_building] // N_BEDS_PER_DORM
        bed_no = building_student_count[girl_building] % N_BEDS_PER_DORM + 1
        room_number = generate_room_number(girl_building, room_idx)
        dorm_rooms.setdefault((girl_building, room_number), []).append(s['student_no'])
        building_student_count[girl_building] += 1

    # 男生分配
    boy_building_idx = 0
    boy_building = boys_buildings[boy_building_idx]
    for s in boys:
        if building_student_count[boy_building] >= MAX_STUDENTS_PER_BUILDING:
            boy_building_idx += 1
            if boy_building_idx >= len(boys_buildings):
                raise Exception("男生楼栋不足以容纳所有男生")
            boy_building = boys_buildings[boy_building_idx]
        room_idx = building_student_count[boy_building] // N_BEDS_PER_DORM
        bed_no = building_student_count[boy_building] % N_BEDS_PER_DORM + 1
        room_number = generate_room_number(boy_building, room_idx)
        dorm_rooms.setdefault((boy_building, room_number), []).append(s['student_no'])
        building_student_count[boy_building] += 1

    # 插入dormitory和bed表
    for (building, room_number), stu_list in dorm_rooms.items():
        manager_id = manager_data[building]
        gender = 'F' if building in girls_buildings else 'M'
        remark = f"{building}栋{room_number}为{'女生' if gender=='F' else '男生'}宿舍，容量{N_BEDS_PER_DORM}人"
        # 插入宿舍
        cur.execute(
            "INSERT INTO dormitory (building, room_number, capacity, gender, manager_id, remark) VALUES (%s,%s,%s,%s,%s,%s)",
            (building, room_number, N_BEDS_PER_DORM, gender, manager_id, remark)
        )
        dorm_id = cur.lastrowid
        dorm_id_map[(building, room_number)] = dorm_id

        # 插入床位
        for bed_no in range(1, N_BEDS_PER_DORM + 1):
            if bed_no <= len(stu_list):
                student_no = stu_list[bed_no-1]
                status = '已入住'
                cur.execute(
                    "INSERT INTO bed (dorm_building, dorm_room_number, bed_number, student_no, status) VALUES (%s,%s,%s,%s,%s)",
                    (building, room_number, bed_no, student_no, status)
                )
                bed_id = cur.lastrowid
                # 更新student表的bed_id字段
                cur.execute("UPDATE student SET bed_id=%s WHERE student_no=%s", (bed_id, student_no))
            else:
                status = '空闲'
                cur.execute(
                    "INSERT INTO bed (dorm_building, dorm_room_number, bed_number, student_no, status) VALUES (%s,%s,%s,%s,%s)",
                    (building, room_number, bed_no, None, status)
                )
    conn.commit()
    cur.close()
    conn.close()
    print(f"已插入宿舍/床位/分配关系数据")

    return list(dorm_id_map.values())

def insert_dorm_checks(dorm_ids):
    conn = pymysql.connect(**db_config)
    cur = conn.cursor()
    checks = []
    today = datetime.today()
    for dorm_id in dorm_ids:
        # 每个宿舍10次检查，分布在最近30天
        for i in range(10):
            check_date = today - timedelta(days=random.randint(0, 29))
            checker = fake.name()
            score = random.randint(60, 100)
            if score > 90:
                remarks = random.choice(['优秀', '干净整洁', '卫生良好'])
                rectified = 0
            elif 80 < score <= 90:
                remarks = random.choice(['有轻微灰尘', '卫生良好'])
                rectified = 0
            else:
                remarks = random.choice(['需加强清洁', '地面有杂物', '地面有灰尘'])
                rectified = random.choice([0, 1])
            checks.append((dorm_id, check_date.date(), checker, score, remarks, rectified))
    batch_size = 1000
    for i in range(0, len(checks), batch_size):
        cur.executemany(
            "INSERT INTO dorm_check (dorm_id, check_date, checker, score, remarks, rectified) VALUES (%s,%s,%s,%s,%s,%s)",
            checks[i:i+batch_size]
        )
    conn.commit()
    cur.close()
    conn.close()
    print("已生成宿舍检查记录。")

def insert_dorm_awards(dorm_ids):
    conn = pymysql.connect(**db_config)
    cur = conn.cursor()
    award_map = {
        '优秀宿舍': ['卫生优良且纪律好', '学风浓厚', '宿舍团结互助', '文明礼貌', '学习氛围浓'],
        '卫生红旗': ['宿舍卫生检查多次满分', '长期保持整洁干净', '卫生评比表现突出'],
        '文明宿舍': ['遵守宿舍规章制度', '互帮互助氛围良好', '积极参加文明评比', '无违纪行为'],
        '警示宿舍': ['多次卫生不合格', '纪律松散', '噪音扰民', '存在未整改问题'],
    }
    award_types = list(award_map.keys())
    term = "2024-2025学年第二学期"
    today = datetime.today()
    awards = []
    for dorm_id in dorm_ids:
        # 每个宿舍随机选0-2个奖惩
        for _ in range(random.randint(0,2)):
            award_type = random.choice(award_types)
            reason = random.choice(award_map[award_type])
            award_time = today - timedelta(days=random.randint(0, 29))
            awards.append((dorm_id, award_type, term, reason, award_time.date()))
    batch_size = 1000
    for i in range(0, len(awards), batch_size):
        cur.executemany(
            "INSERT INTO dorm_award (dorm_id, award_type, term, reason, award_time) VALUES (%s,%s,%s,%s,%s)",
            awards[i:i+batch_size]
        )
    conn.commit()
    cur.close()
    conn.close()
    print("已生成宿舍奖惩记录。")

def insert_visitors(dorm_ids):
    conn = pymysql.connect(**db_config)
    cur = conn.cursor()
    reasons = ['同学聚会','送快递','借书','学习讨论','探望朋友','送饭','聊天','送物品','活动报名','送文件','辅导答疑','请教问题','还书','取快递','搬运行李','参加生日会','参加聚餐','帮忙修理','传递通知','递送礼物','送饮料','结伴出行','预约实验','技术交流','卫生检查','宿舍检查','领取物品','归还物品','节日慰问','送药品','送水果','心理辅导','班级活动','外卖送餐','考试复习','讨论作业','志愿服务','家人探访','同乡聚会','社团活动','竞赛讨论','办理手续','招聘宣讲','面试交流','学术讲座','资料共享','健康宣教','临时借宿','新生报道','安全检查','设备维修']
    # 获取所有student主键id
    conn2 = pymysql.connect(**db_config)
    cur2 = conn2.cursor()
    cur2.execute("SELECT id FROM student")
    all_student_ids = [row[0] for row in cur2.fetchall()]
    cur2.close()
    conn2.close()
    visitors = []
    today = datetime.today()
    for _ in range(N_VISITORS):
        name = fake.name()
        dorm_id = random.choice(dorm_ids)
        student_id = random.choice(all_student_ids)
        visit_time = today - timedelta(days=random.randint(0, 29), hours=random.randint(0,23))
        leave_time = visit_time + timedelta(hours=random.randint(0,3))
        purpose = random.choice(reasons)
        visitors.append((name, dorm_id, student_id, visit_time, leave_time, purpose))
    batch_size = 1000
    for i in range(0, len(visitors), batch_size):
        cur.executemany(
            "INSERT INTO visitor (name, dorm_id, student_id, visit_time, leave_time, purpose) VALUES (%s,%s,%s,%s,%s,%s)",
            visitors[i:i+batch_size]
        )
    conn.commit()
    cur.close()
    conn.close()
    print("已生成访客登记记录。")

if __name__ == "__main__":
    print("插入宿舍管理员...")
    insert_managers()
    print("插入学生...")
    students = insert_students()
    print("分配宿舍和床位...")
    dorm_ids = assign_beds_and_fill_tables(students)
    print("插入宿舍检查记录...")
    insert_dorm_checks(dorm_ids)
    print("插入宿舍奖惩记录...")
    insert_dorm_awards(dorm_ids)
    print("插入访客记录...")
    insert_visitors(dorm_ids)
    print("所有表数据已生成！")
