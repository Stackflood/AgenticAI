import sqlite3
from collections import defaultdict
from pathlib import Path

DB_FILE = Path("school.db")


def create_schema(conn):
    cur = conn.cursor()
    cur.executescript(
        """
        DROP TABLE IF EXISTS enrollments;
        DROP TABLE IF EXISTS students;
        DROP TABLE IF EXISTS teachers;
        DROP TABLE IF EXISTS classes;

        CREATE TABLE classes (
            class_id INTEGER PRIMARY KEY AUTOINCREMENT,
            class_name TEXT NOT NULL UNIQUE
        );

        CREATE TABLE teachers (
            teacher_id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_name TEXT NOT NULL,
            subject TEXT NOT NULL,
            class_id INTEGER NOT NULL,
            FOREIGN KEY (class_id) REFERENCES classes(class_id)
        );

        CREATE TABLE students (
            student_id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT NOT NULL,
            class_id INTEGER NOT NULL,
            FOREIGN KEY (class_id) REFERENCES classes(class_id)
        );

        CREATE TABLE enrollments (
            enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers(teacher_id),
            FOREIGN KEY (student_id) REFERENCES students(student_id),
            UNIQUE (teacher_id, student_id)
        );
        """
    )
    conn.commit()


def seed_data(conn):
    cur = conn.cursor()

    classes = [f"Class {name}" for name in ["A", "B", "C", "D", "E"]]
    cur.executemany("INSERT INTO classes (class_name) VALUES (?)", [(c,) for c in classes])
    conn.commit()

    cur.execute("SELECT class_id, class_name FROM classes ORDER BY class_id")
    class_rows = cur.fetchall()
    class_ids = [row[0] for row in class_rows]

    teacher_subjects = ["Math", "Science", "English", "History", "Geography", "Computer", "Art", "Music", "Physics", "Chemistry"]
    teacher_rows = []
    for i in range(1, 101):
        class_id = class_ids[(i - 1) % len(class_ids)]
        teacher_rows.append((f"Teacher {i:03d}", teacher_subjects[(i - 1) % len(teacher_subjects)], class_id))
    cur.executemany(
        "INSERT INTO teachers (teacher_name, subject, class_id) VALUES (?, ?, ?)",
        teacher_rows,
    )

    student_rows = []
    for i in range(1, 101):
        class_id = class_ids[(i * 2 - 1) % len(class_ids)]
        student_rows.append((f"Student {i:03d}", class_id))
    cur.executemany(
        "INSERT INTO students (student_name, class_id) VALUES (?, ?)", student_rows,
    )

    cur.execute("SELECT teacher_id, class_id FROM teachers ORDER BY teacher_id")
    teacher_info = cur.fetchall()
    cur.execute("SELECT student_id, class_id FROM students ORDER BY student_id")
    student_info = cur.fetchall()

    enrollment_rows = []
    for student_id, student_class in student_info:
        possible_teachers = [tid for tid, tclass in teacher_info if tclass == student_class]
        if not possible_teachers:
            possible_teachers = [teacher_info[(student_id - 1) % len(teacher_info)][0]]
        primary_teacher = possible_teachers[student_id % len(possible_teachers)]
        secondary_teacher = teacher_info[(student_id * 3) % len(teacher_info)][0]
        if primary_teacher == secondary_teacher:
            secondary_teacher = teacher_info[(student_id * 5 + 7) % len(teacher_info)][0]
        enrollment_rows.append((primary_teacher, student_id))
        enrollment_rows.append((secondary_teacher, student_id))

    enrollment_rows = list(dict.fromkeys(enrollment_rows))
    cur.executemany(
        "INSERT OR IGNORE INTO enrollments (teacher_id, student_id) VALUES (?, ?)",
        enrollment_rows,
    )
    conn.commit()


def print_diagram(conn):
    cur = conn.cursor()

    print("\nSCHOOL DATABASE RELATIONSHIP DIAGRAM")
    print("=" * 60)
    print("[CLASSES] 1 ---< [TEACHERS]")
    print("[CLASSES] 1 ---< [STUDENTS]")
    print("[TEACHERS] >---< [STUDENTS]  (many-to-many via ENROLLMENTS)")
    print("=" * 60)

    cur.execute("SELECT COUNT(*) FROM teachers")
    teachers_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM students")
    students_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM enrollments")
    enrollments_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM classes")
    classes_count = cur.fetchone()[0]

    print(f"Classes: {classes_count}, Teachers: {teachers_count}, Students: {students_count}, Enrollments: {enrollments_count}")

    print("\nSample Class -> Teachers -> Students mapping:")
    cur.execute(
        """
        SELECT c.class_name, t.teacher_name, s.student_name
        FROM enrollments e
        JOIN teachers t ON e.teacher_id = t.teacher_id
        JOIN students s ON e.student_id = s.student_id
        JOIN classes c ON t.class_id = c.class_id
        ORDER BY c.class_id, t.teacher_id, s.student_id
        LIMIT 20
        """
    )
    rows = cur.fetchall()
    current_class = None
    for class_name, teacher_name, student_name in rows:
        if class_name != current_class:
            current_class = class_name
            print(f"\n{class_name}")
        print(f"  {teacher_name}  -->  {student_name}")


def main():
    if DB_FILE.exists():
        DB_FILE.unlink()

    conn = sqlite3.connect(DB_FILE)
    try:
        create_schema(conn)
        seed_data(conn)
        print_diagram(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
