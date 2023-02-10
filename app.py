from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
from flask import Flask, jsonify, render_template, request, redirect, session
from flask_restful import Resource, Api, reqparse, abort, fields, marshal_with
from flask_sqlalchemy import SQLAlchemy
from itsdangerous import base64_decode
from flask_bcrypt import Bcrypt
from PIL import Image
from io import BytesIO
import qrcode
from deepface import DeepFace
import base64
import io
import sys
import datetime
from datetime import date
import string
import random
import numpy as np
import glob
import cv2
import pandas as pd
from functools import wraps
import pathlib
import jwt
import time

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Student_Data.db'
app.config['SECRET_KEY'] = 'hbdhbh$%@$%#knwqhh@5631435%@#FG#@545@Chd22#'
app.secret_key = 'hbdhbh$%@$%#knwqhh@5631435%@#FG#@545@Chd22#'

api = Api(app)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
app.permanent_session_lifetime = datetime.timedelta(days=5)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return tbl_user.query.get(int(user_id))





class tbl_user(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    # name=db.Column(db.String(200), nullable=False, unique=False)
    # username = db.Column(db.String(20), nullable=False, unique=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(80), nullable=False)
    mobnumber = db.Column(db.String(20), nullable=False, unique=True)
    role = db.Column(db.String(120), nullable=False, default="student")  # ------
    date_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    student_key = db.relationship('StudentData', backref='author', lazy=True, cascade="all,delete")
    user_key = db.relationship('Performance', backref='author', lazy=True, cascade="all,delete")

    def __repr__(self) -> str:
        return '<role %r>' % self.role




class StudentData(db.Model, UserMixin):
    reg_id = db.Column(db.String(120), primary_key=True)
    fname = db.Column(db.String(200), nullable=False)
    mname = db.Column(db.String(200), nullable=False)
    lname = db.Column(db.String(200), nullable=False)
    branch = db.Column(db.String(200), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    dob = db.Column(db.String(200), nullable=True)
    # age= db.Column(db.Integer, nullable=False)
    blood_g = db.Column(db.String, nullable=True)
    # address=db.Column(db.String(80), nullable=False)
    laneno = db.Column(db.String(80), nullable=False)
    street = db.Column(db.String(80), nullable=False)
    city = db.Column(db.String(80), nullable=False)
    district = db.Column(db.String(80), nullable=False)
    state = db.Column(db.String(80), nullable=False)
    country = db.Column(db.String(80), nullable=False)
    pincode = db.Column(db.Integer, nullable=False)
    # mobnumber_prt = db.Column(db.Integer, nullable=False)
    # mobnumber = db.Column(db.Integer, nullable=False, unique=True)
    mobnumber_prt = db.Column(db.String(20), nullable=False)
    mobnumber = db.Column(db.String(20), nullable=False, unique=True)
    prn = db.Column(db.String(200), nullable=False, unique=True)
    qr_id = db.Column(db.String(200), nullable=False, unique=True)
    qr_photo = db.Column(db.String(200))
    photo = db.Column(db.String(200), nullable=False)
    # image_enc=db.Column(db.String(500), nullable=False)
    date_time = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    performance_key = db.relationship('Performance', backref='child', lazy=True, cascade="all,delete")
    user_id = db.Column(db.Integer, db.ForeignKey('tbl_user.id'), nullable=False, unique=True)

    def __repr__(self) -> str:
        return '<role %r>' % "student"


class Performance(db.Model, UserMixin):
    per_id = db.Column(db.Integer, primary_key=True)
    day = db.Column(db.String(20), nullable=False)
    date = db.Column(db.Date, nullable=False)
    intime = db.Column(db.Time)
    outtime = db.Column(db.Time)
    status = db.Column(db.String(120), nullable=False)
    # remark = db.Column(db.String(120), nullable=False)
    studentr_key = db.Column(db.String(120), db.ForeignKey(StudentData.reg_id), nullable=False)
    user_id = db.Column(db.String(120), db.ForeignKey(tbl_user.id), nullable=False)

    def __repr__(self) -> int:
        return '<role %r>' % "student"


# jwt token
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.args.get('token')
        if not token:
            return jsonify({"status": False, "message": "Token is missing"})
        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
        except:
            return jsonify({"status": False, "message": "Token is invalid"})
        return f(*args, **kwargs)

    return decorated


# homepage (random page)
@app.route("/", methods=['POST', 'GET'])
def Homepage():
    return redirect("/login")


# student,admin,guard login
@app.route("/login", methods=['GET'])
def login():
    Data = request.get_json()
    email = Data["email"]
    password = Data["password"]

    user = tbl_user.query.filter_by(email=email).first()
    if user:
        if bcrypt.check_password_hash(user.password, password):
            login_user(user)
            session['email'] = email
            token = jwt.encode({'user': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)},
                               app.config['SECRET_KEY'])
            return jsonify({'status': True, 'Token': token, 'role': user.role})
        else:
            return jsonify({'status': False, "message": "Password incorrect"})
    else:
        return jsonify({'status': False, "message": "Username not found"})


# student Registartion
@app.route("/registration", methods=['POST'])
def registration():
    Data = request.get_json()
    # name=Data["name"]
    mobnumber = Data["mobile_number"]
    password = bcrypt.generate_password_hash(Data["password"])
    email = Data["email"]

    try:
        Newstudent = tbl_user(mobnumber=mobnumber, password=password, email=email)
        db.session.add(Newstudent)
        db.session.commit()
        return jsonify({'status': True, "message": "Registration successful"})
    except:
        return jsonify({'status': False, "message": "Registration Failed"})


# Qr code generator
def qrcodegenerator():
    length = 16
    digits = ['0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
    lower_case = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h',
                  'i', 'j', 'k', 'm', 'n', 'o', 'p', 'q',
                  'r', 's', 't', 'u', 'v', 'w', 'x', 'y',
                  'z']
    upper_case = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H',
                  'I', 'J', 'K', 'M', 'N', 'O', 'P', 'Q',
                  'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y',
                  'Z']
    symbols = ['@', '#', '$', '%', '=', ':', '?', '.', '/', '|', '~', '>',
               '*', '(', ')', '<']
    letters = digits + lower_case + upper_case + symbols
    Qr_id = ''.join(random.choice(letters) for i in range(length))
    # Qr_id = base64.b64encode(bytes(Qr_id, 'utf-8'))
    image = qrcode.make(Qr_id)
    # buffered = BytesIO()
    image.save("./upload/myimage.jpg", format="JPEG")
    # Qr_Photo = base64.b64encode(buffered.getvalue())
    with open("./upload/myimage.jpg", "rb") as image_file:
        Qr_Photo = base64.b64encode(image_file.read()).decode("UTF")
    return Qr_id, Qr_Photo


# ------------------------------------studentform-------------------------------

@app.route("/studentform/add", methods=["POST"])
@token_required
@login_required
def Studentform():
    if current_user.is_authenticated and current_user.role == "student":
        if "email" in session:
            Data = request.get_json()
            fname = Data["fname"]
            mname = Data["mname"]
            lname = Data["lname"]
            branch = Data["branch"]
            year = Data["year"]
            dob = Data["dob"]
            # age=Data["age"]
            blood_g = Data["blood_g"]
            # address=Data["address"]
            laneno = Data["laneno"]
            street = Data["street"]
            city = Data["city"]
            district = Data["district"]
            state = Data["state"]
            country = Data["country"]
            pincode = Data["pincode"]
            mobnumber_prt = Data["mobnumber_prt"]
            mobnumber = Data["mobnumber"]
            prn = Data["prn"]
            reg_id = "DPCOE4060" + prn
            photo = Data["photo"]
            qr_id, qr_photo = qrcodegenerator()
            # user_id=current_user.id
            try:
                info = StudentData(reg_id=reg_id,
                                   mname=mname,
                                   fname=fname,
                                   lname=lname,
                                   branch=branch,
                                   year=year,
                                   dob=dob,
                                   # age=age,
                                   blood_g=blood_g,
                                   # address=address,
                                   laneno=laneno,
                                   street=street,
                                   city=city,
                                   district=district,
                                   state=state,
                                   country=country,
                                   pincode=pincode,
                                   mobnumber_prt=mobnumber_prt,
                                   mobnumber=mobnumber,
                                   prn=prn,
                                   photo=photo,
                                   qr_id=qr_id,
                                   qr_photo=qr_photo,
                                   # image_enc=image_enc,
                                   user_id=current_user.id)
                db.session.add(info)
                db.session.commit()
                return jsonify({"status": True, "message": "added successfully"})
            except:
                return jsonify({"status": False, "message": "Already exist"})
        else:
            return jsonify({"status": False, "message": "Try again"})
    else:
        return jsonify({"status": False, "message": "Please login"})


# check performance of student using user id
@app.route("/student/performance/<int:id>", methods=["GET"])
@token_required
@login_required
def student_performance(id):
    if (current_user.is_authenticated and current_user.role == "student") and "email" in session:
        performance = Performance.query.filter_by(user_id=id).all()
        if performance:
            All_performance = []
            for data in performance:
                All_performance.append({"id": data.per_id,
                                        "day": data.day,
                                        "date": data.date,
                                        "intime": str(data.intime),
                                        "outtime": str(data.outtime),
                                        "status": data.status,
                                        "student_registration Number": data.studentr_key})

            return jsonify({"status": True, "Data": All_performance})
        else:
            return jsonify({"status": False, "message": "Data not availabel"})
    else:
        return jsonify({"status": False, "message": "Please login"})


# ---------------------------------------------Admin working------------------------

# admin can see all users
@app.route("/admin/users/view", methods=["GET"])
@token_required
@login_required
def admin_users():
    if current_user.is_authenticated and current_user.role == "admin":
        if "email" in session:
            users = tbl_user.query.all()
            if users:
                users_data = []
                for data in users:
                    users_data.append({"email": data.email, "id": data.id})

                return jsonify({"status": True, "Data": users_data})
            else:
                return jsonify({"status": False, "message": "Data not availabel"})
        else:
            return jsonify({"status": False, "message": "Not Login"})
    else:
        return jsonify({"status": False, "message": "Please login"})


# admin can delete particular user record using user id
@app.route("/admin/users/delete/<int:id>", methods=["POST"])
@token_required
@login_required
def delete_users(id):
    if (current_user.is_authenticated and current_user.role == "admin") and "email" in session:
        user_data = tbl_user.query.filter_by(id=int(id)).first()
        if user_data:
            db.session.delete(user_data)
            db.session.commit()
            return jsonify({"status": True, "message": "Deleted successfully"})
        else:
            return jsonify({"status": False, "message": "Not deleted"})

    else:
        return jsonify({"status": False, "message": "Please login"})


# admin can see student data
@app.route("/admin/studentdata/view/<int:id>", methods=["GET"])
@token_required
@login_required
def dashboard_admin(id):
    if (current_user.is_authenticated and current_user.role == "admin"):
        if "email" in session:
            user_data = StudentData.query.filter_by(user_id=id).first()
            if user_data:
                return jsonify({
                    "reg_id": user_data.reg_id,
                    "fname": user_data.fname,
                    "mname": user_data.mname,
                    "lname": user_data.lname,
                    "branch": user_data.branch,
                    "year": user_data.year,
                    "dob": user_data.dob,
                    # "age":user_data.age,
                    "blood_g": user_data.blood_g,
                    # "address":user_data.address,
                    "laneno": user_data.laneno,
                    "street": user_data.street,
                    "city": user_data.city,
                    "district": user_data.district,
                    "state": user_data.state,
                    "country": user_data.country,
                    "pincode": user_data.pincode,
                    "mobnumber_prt": user_data.mobnumber_prt,
                    "mobnumber": user_data.mobnumber,
                    "prn": user_data.prn,
                    "photo": user_data.photo,
                    "qr_photo": user_data.qr_photo})
            else:
                return jsonify({"status": False, "message": "Not Found"})
    else:
        return jsonify({"status": False, "message": "Please login"})


# admin can edit student form using user id
@app.route("/admin/studentdata/edit/<int:id>", methods=["POST"])
@token_required
@login_required
def dashboard_adminedit(id):
    if (current_user.is_authenticated and current_user.role == "admin") and "email" in session:

        user_data = StudentData.query.filter_by(user_id=id).first()
        if user_data:
            Data = request.get_json()
            fname = Data["fname"]
            mname = Data["mname"]
            lname = Data["lname"]
            branch = Data["branch"]
            year = Data["year"]
            dob = Data["dob"]
            # age=Data["age"]
            blood_g = Data["blood_g"]
            # address=Data["address"]
            laneno = Data["laneno"]
            street = Data["street"]
            city = Data["city"]
            district = Data["district"]
            state = Data["state"]
            country = Data["country"]
            pincode = Data["pincode"]
            mobnumber_prt = Data["mobnumber_prt"]
            mobnumber = Data["mobnumber"]
            photo = Data["photo"]

            user_data.mname = mname
            user_data.fname = fname
            user_data.lname = lname
            user_data.branch = branch
            user_data.year = year
            user_data.dob = dob
            # user_data.age=age
            user_data.blood_g = blood_g
            # user_data.address=address
            user_data.laneno = laneno
            user_data.street = street
            user_data.city = city
            user_data.district = district
            user_data.state = state
            user_data.country = country
            user_data.pincode = pincode
            user_data.mobnumber_prt = mobnumber_prt
            user_data.mobnumber = mobnumber
            user_data.photo = photo
            try:
                db.session.add(user_data)
                db.session.commit()
                return jsonify({"status": True, "message": "Updated successfuly"})
            except:
                return jsonify({"status": False, "message": "Try again"})


        else:
            return jsonify({"status": False, "message": "Not Found"})
    else:
        return jsonify({"status": False, "message": "Please login"})


# admin can check/see all performance
@app.route("/admin/performance/view", methods=["GET"])
@token_required
@login_required
def admin_performance():
    if (current_user.is_authenticated and current_user.role == "admin") and "email" in session:
        # if "email" in session:
        performance = Performance.query.all()
        if performance:
            All_performance = []
            for data in performance:
                All_performance.append({"id": data.per_id,
                                        "day": data.day,
                                        "date": data.date,
                                        "intime": str(data.intime),
                                        "outtime": str(data.outtime),
                                        "status": data.status,
                                        "student_registration Number": data.studentr_key})

            return jsonify({"status": True, "Data": All_performance})
        else:
            return jsonify({"status": False, "message": "Data not availabel"})
    else:
        return jsonify({"status": False, "message": "Please login"})


# admin can see all guards which is available
@app.route("/admin/guards/view", methods=["GET"])
@token_required
@login_required
def admin_guards():
    if (current_user.is_authenticated and current_user.role == "admin") and "email" in session:

        users = tbl_user.query.filter_by(role="guard").first()
        if users:
            return jsonify({"id": users.id, "email": users.email})
        else:
            return jsonify({"status": False, "message": "Data not available"})
    else:
        return jsonify({"status": False, "message": "Please login"})


# admin can add new guard
@app.route("/admin/guards/add", methods=["POST"])
@token_required
@login_required
def add_guards():
    if (current_user.is_authenticated and current_user.role == "admin") and "email" in session:
        Data = request.get_json()
        mobnumber = Data["mobile_number"]
        password = bcrypt.generate_password_hash(Data["password"])
        email = Data["email"]
        try:
            Newguard = tbl_user(mobnumber=mobnumber, password=password, email=email, role="guard")
            db.session.add(Newguard)
            db.session.commit()
            return jsonify({'status': True, "message": "Registration successful"})
        except:
            return jsonify({'status': False, "message": "Registration Failed"})
    else:
        return jsonify({"status": False, "message": "Please login"})


# admin can delete guard record using that user_id
@app.route("/admin/guards/delete/<int:id>", methods=["POST"])
@token_required
@login_required
def delete_guards(id):
    if (current_user.is_authenticated and current_user.role == "admin") and "email" in session:
        user_data = tbl_user.query.filter_by(id=int(id)).first()
        if user_data:
            db.session.delete(user_data)
            db.session.commit()
            return jsonify({"status": True, "message": "Deleted successfully"})
        else:
            return jsonify({"status": False, "message": "Not deleted"})
    else:
        return jsonify({"status": False, "message": "Please login"})


# we are adding new code here
@app.route("/admin/attend_status", methods=["GET"])
@token_required
@login_required
def oneday_attend():
    user_data = StudentData.query.all()
    AllData = {}
    for key in user_data:
        AllData[key.reg_id] = {"Name": f"{key.fname} {key.lname}", "branch": key.branch, "year": key.year,
                               "Status": "Absent"}
    present_list = []

    current_date = date.today()
    today_data = Performance.query.filter_by(date=current_date).all()
    for keys in today_data:
        present_list.append(keys.studentr_key)
    for value in present_list:
        if value in AllData.keys():
            AllData[value]["Status"] = "Present"

    return jsonify({"status": True, "Data": AllData})


# -----------------------------------------Guard Working---------------------------------
# find key from qr code
def qrscanner(fimg):
    img = cv2.imread(fimg)
    detect = cv2.QRCodeDetector()
    value, points, straight_qrcode = detect.detectAndDecode(img)
    return value


# check student photo and Qr code and verify it
@app.route("/guard/check", methods=["POST"])
@token_required
@login_required
def check():
    if (current_user.is_authenticated and current_user.role == 'guard') and "email" in session:
        day = datetime.datetime.now()
        # Data=request.get_json()
        # photo=Data["photo"]
        Data = request.get_json()
        base64_image = Data["photo"]
        with open("upload/train.png", "wb") as f:
            f.write(base64.b64decode(base64_image))
        image_file = "upload/train.png"
        key = qrscanner(image_file)
        time.sleep(1)
        user_data = StudentData.query.filter_by(qr_id=key).first()
        if user_data:
            print("I AM INSIDE")

            image_f = cv2.imread(image_file)
            with open("upload/test.png", "wb") as f:
                f.write(base64.b64decode(user_data.photo))
            test_file = "upload/test.png"
            image_f_test = cv2.imread(test_file)

            result = DeepFace.verify(image_f, image_f_test)
            print(result)

            if result['verified']:
                Date = date.today()
                today_data = Performance.query.filter_by(date=Date, studentr_key=user_data.reg_id).first()
                if today_data:
                    today_data.outtime = datetime.datetime.now().time()
                    # Remark="Verified"

                    db.session.add(today_data)
                    db.session.commit()
                    return jsonify({'status': True, "message": "Verified"})
                else:

                    # intime = day.strftime("%I:%M:%S %p")
                    intime = datetime.datetime.now().time()
                    Day = day.strftime('%A')
                    Status = "Present"
                    outtime = None

                    Data = Performance(day=Day, date=Date, intime=intime, outtime=outtime, status=Status,
                                       studentr_key=user_data.reg_id, user_id=user_data.user_id)
                    db.session.add(Data)
                    db.session.commit()
                    return jsonify({'status': True, "message": "Verified"})

            else:
                return jsonify({'status': False, "message": "Not verified"})
        else:
            return jsonify({'status': False, "message": "login please"})


@app.route("/logout", methods=["POST"])
def logout():
    if current_user.is_authenticated:
        logout_user()
        if session.get('email'):
            session['email'] = None

        return jsonify({"status": True, "message": "logout successfully"})
    return jsonify({"status": False, "message": "Try again"})


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)