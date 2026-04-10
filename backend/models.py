from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.String(20), primary_key=True)
    password = db.Column(db.String(64), nullable=False)
    role = db.Column(db.String(10), nullable=False, default="student")
    profile = db.relationship("StudentProfile", backref="user", uselist=False)

    def to_dict(self):
        return {"user_id": self.user_id, "role": self.role}


class StudentProfile(db.Model):
    __tablename__ = "student_profile"
    user_id = db.Column(db.String(20), db.ForeignKey("user.user_id"), unique=True, nullable=False)
    student_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    email_add = db.Column(db.String(100))
    major = db.Column(db.String(50))
    current_semester = db.Column(db.SmallInteger, nullable=False, default=1)
    status = db.Column(db.String(10), nullable=False)
    enrollments = db.relationship("Enrollment", backref="student", lazy="dynamic")
    registrations = db.relationship("Registration", backref="student", lazy="dynamic")
    grades = db.relationship("Grade", backref="student", lazy="dynamic")

    def to_dict(self):
        return {
            "user_id": self.user_id, "student_id": self.student_id,
            "name": self.name, "phone": self.phone, "email": self.email_add,
            "major": self.major, "current_semester": self.current_semester,
            "status": self.status,
        }


class Enrollment(db.Model):
    __tablename__ = "enrollment"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profile.student_id"), nullable=False)
    current_semester = db.Column(db.SmallInteger, nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    course_professor = db.Column(db.String(50))
    course_grade = db.Column(db.Numeric(3, 1))

    def to_dict(self):
        return {
            "id": self.id, "student_id": self.student_id,
            "semester": self.current_semester, "course_name": self.course_name,
            "professor": self.course_professor,
            "grade": float(self.course_grade) if self.course_grade else None,
        }


class Registration(db.Model):
    __tablename__ = "registration"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profile.student_id"), nullable=False)
    reg_status = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(10), nullable=False)
    paid_amount = db.Column(db.Integer, nullable=False, default=0)
    reg_date = db.Column(db.Date)

    def to_dict(self):
        return {
            "id": self.id, "student_id": self.student_id,
            "reg_status": self.reg_status, "status": self.status,
            "paid_amount": self.paid_amount,
            "reg_date": self.reg_date.isoformat() if self.reg_date else None,
        }


class Grade(db.Model):
    __tablename__ = "grade"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    student_id = db.Column(db.Integer, db.ForeignKey("student_profile.student_id"), nullable=False)
    semester = db.Column(db.SmallInteger, nullable=False)
    course_name = db.Column(db.String(100), nullable=False)
    course_grade = db.Column(db.Numeric(3, 1))
    semester_grade = db.Column(db.Numeric(4, 2))
    avg_grade = db.Column(db.Numeric(4, 2))

    def to_dict(self):
        return {
            "id": self.id, "student_id": self.student_id,
            "semester": self.semester, "course_name": self.course_name,
            "course_grade": float(self.course_grade) if self.course_grade is not None else None,
            "semester_grade": float(self.semester_grade) if self.semester_grade is not None else None,
            "avg_grade": float(self.avg_grade) if self.avg_grade is not None else None,
        }