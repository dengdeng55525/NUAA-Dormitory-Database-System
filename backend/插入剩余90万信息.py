import pymysql
import random
import hashlib
from faker import Faker

from db_config import get_db_config

fake = Faker('zh_CN')

db_config = get_db_config()

def sha256_encrypt(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

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

def insert_students_1925_2016():
    conn = pymysql.connect(**db_config)
    cur = conn.cursor()
    students = []
    colleges = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,22,24]
    years = list(range(1925, 2017))  # 包含1925~2016
    majors = [1,2,3,4,5]
    classes_per_major = [3,4,5]
    students_per_class = 36
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
                        grade = int(year)
                        phone = fake.phone_number()
                        remark = f"{college}学院{grade}级{major}专业{class_num}班"
                        password = sha256_encrypt(studentid)
                        students.append((
                            studentid, name, gender, grade, phone, password, remark, None  # bed_id=None
                        ))
    # 分批插入
    batch_size = 2000
    for i in range(0, len(students), batch_size):
        cur.executemany(
            "INSERT INTO student (student_no, name, gender, grade, phone, password, remark, bed_id) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
            students[i:i+batch_size]
        )
        print(f"Inserted {i+batch_size} / {len(students)}")
    conn.commit()
    cur.close()
    conn.close()
    print(f"已插入{len(students)}名1925-2016学生（无床位信息）")

if __name__ == "__main__":
    insert_students_1925_2016()
