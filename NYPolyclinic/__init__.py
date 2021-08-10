from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_mail import Mail, Message
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from itsdangerous import URLSafeTimedSerializer
from sqlalchemy import text
from faceRocgn import authFace
import Users, Applicant, appointments, Item, qns, Cart
import smtplib
from Forms import *
from datetime import datetime, timedelta
from pyechart import bargraph
from Item import Item
from qns import FAQ

app = Flask(__name__, static_url_path='/static')
limiter = Limiter(app, key_func=get_remote_address)
app.config["SECRET_KEY"] = b'o5Dg987*&G^@(E&FW)}'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite'
app.config["MAIL_SERVER"] = "smtp.gmail.com"
app.config["MAIL_PORT"] = 465
app.config["MAIL_USE_SSL"] = True
app.config["MAIL_USERNAME"] = "flaskapptest123@gmail.com"
app.config["MAIL_PASSWORD"] = "flaskapp123"
app.config["DEFAULT_MAIL_SENDER"] = "flaskapptest123@gmail.com"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
mail = Mail(app)
db = SQLAlchemy(app)
app.config["SESSION_TYPE"] = 'sqlalchemy'
app.config["SESSION_SQLALCHEMY"] = db
sess = Session(app)


# SQL Table
class Users(db.Model):
    NRIC = db.Column(db.String(10), primary_key=True)
    fname = db.Column(db.String(20), nullable=False)
    lname = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"NRIC: {self.NRIC}, Name :{self.fname + ' ' + self.lname} , Role: {self.role}"


class Items(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    price = db.Column(db.Float, nullable=False)
    have = db.Column(db.Float, nullable=False)
    want = db.Column(db.Float, nullable=False)
    bio = db.Column(db.String(20))
    picture = db.Column(db.String(20))

    def __repr__(self):
        return f"Name: {self.name},Price: {self.price}"


class FAQs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.String(120))
    answer = db.Column(db.String(120))
    date = db.Column(db.DateTime)


@app.route('/')
def home():
    return render_template('home.html')


# Online Pharmacy
@app.route('/pharmacy', methods=['GET', 'POST'])
def show_items():
    search = SearchBar(request.form)
    if request.method == 'POST' and search.validate():
        item_list = []
        start_item_list = []
        contain_item_list = []
        items = Items.query.all()
        for i in items:
            item = Item(i.id, i.name, i.price, i.have, i.bio, i.picture)
            item_list.append(item)
            if item.get_item_name().lower().startswith(search.search.data.lower()):
                start_item_list.append(item)
            elif search.search.data.lower() in item.get_item_name().lower():
                contain_item_list.append(item)
            item_list = start_item_list + contain_item_list

        return render_template('Pharmacy/pharmacy.html', items_list=item_list, form=search)

    item_list = []
    items = Items.query.all()
    for i in items:
        item = Item(i.id, i.name, i.price, i.have, i.bio, i.picture)
        item_list.append(item)

    return render_template('Pharmacy/pharmacy.html', items_list=item_list, form=search)


# Login system
@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        sql = text("Select * from Users where NRIC = :x")
        c = db.engine.execute(sql, x=form.NRIC.data)
        user = None
        for i in c:
            user = i
        try:
            if form.NRIC.data == user.NRIC:
                flash("This NRIC is already in used.You can login to access our service.", "danger")
                return redirect(url_for('register'))
        except AttributeError:
            user = Users(NRIC=form.NRIC.data, fname=form.FirstName.data, lname=form.LastName.data,
                         password=form.Password.data,email=form.Email.data,role="Patient")
            db.session.add(user)
            db.session.commit()
            flash(f'Account created for {form.FirstName.data} {form.LastName.data}!', 'success')
            return redirect(url_for('register'))
    return render_template('Login/register.html', form=form)


# Face Recognition Login
@app.route('/login', methods=['GET', 'POST'])
@limiter.limit('5/minute')
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        # Parameterized queries
        sql = text("Select * from Users where NRIC = :x and password= :y")
        c = db.engine.execute(sql, x=form.NRIC.data, y=form.Password.data)
        user = None
        for i in c:
            user = i
        try:
            username = user.fname + " " + user.lname
        except AttributeError:
            flash('Incorrect username or password', 'danger')
        else:
            if user is not None and user.role == 'Admin':
                face = authFace()
                if face == 'WEN HAO':
                    session["user"] = username
                    session["user-role"] = user.role
                    flash(
                        f'{username} has logged in!',
                        'success')
                    return redirect(url_for('home'))
            elif user is not None:
                session["user"] = username
                flash(
                    f'{username} has logged in!',
                    'success')
                return redirect(url_for('home'))
            elif user is None:
                flash('Incorrect username or password', 'danger')

    return render_template('Login/login.html', form=form)


@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)


@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("home"))


# Profile
@app.route('/profile', methods=["GET", "POST"])
def profile():
    form = UpdateProfileForm(request.form)

    db = shelve.open('storage.db', 'c', writeback=True)
    users_dict = db["Users"]
    user = users_dict[session["user-NRIC"]]
    if request.method == "POST" and form.validate():
        user.set_email(form.Email.data)
        user.set_dob(form.Dob.data)
    db.close()
    return render_template("Login/profile.html", form=form, user=user)


# Helper functions to reset email
def generate_confirmation_token(email):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    return serializer.dumps(email, salt=app.config['SECRET_KEY'])


def confirm_token(token, expiration=300):
    serializer = URLSafeTimedSerializer(app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=app.config['SECRET_KEY'],
            max_age=expiration
        )
    except:
        return False
    return email


# User password management
@app.route('/change_password', methods=["GET", "POST"])
def change_password():
    form = ChangePasswordForm(request.form)
    if request.method == "POST" and form.validate():
        db = shelve.open('storage.db', 'c', writeback=True)
        user_db = db["Users"]
        user = user_db[session["user-NRIC"]]
        user.set_password(form.Password.data)
        db.close()
        return redirect(url_for('home'))

    return render_template('Login/change_password.html', form=form)


@app.route('/reset_password', methods=["GET", "POST"])
def reset_password():
    form = ResetPasswordForm(request.form)
    if request.method == "POST" and form.validate():
        sql = text("Select * from Users where email = :x")
        c = db.engine.execute(sql, x=form.email.data)
        user = None
        for i in c:
            user = i
        try:
            email = user.email
            token = generate_confirmation_token(email)
            msg = Message(subject="Password reset", recipients=[email],
                          body="Link to reset password : {}{}. Link valid for only 5 minutes" \
                          .format(request.url_root, url_for("confirm_reset", token=token)),
                          sender="flaskapptest123@gmail.com")
            mail.send(msg)
            flash("Successfully entered email, if you have registered an account with us, a reset password email would"
                  " be sent to your email", "success")
            return redirect(url_for("home"))
        except AttributeError:
            flash("This email is not registered.", "danger")
    return render_template("Login/reset_password.html", form=form)


@app.route('/confirm_reset/<token>', methods=["GET", "POST"])
def confirm_reset(token):
    form = ChangePasswordForm(request.form)
    if request.method == "POST" and form.validate():
        sql = text("Select * from Users where email = :x")
        c = db.engine.execute(sql, x=form.email.data)
        user = None
        for i in c:
            user = i
        if user.email == session["reset_email"]:
            db.engine.execute(f"UPDATE User SET password = {form.Password.data} WHERE email = {user.email}")
            db.session.commit()
            flash("Successfully reset password", "success")
            del session["reset_email"]
            return redirect(url_for("login"))

    else:
        email = confirm_token(token)
        if email:
            session["reset_email"] = email
            return render_template("Login/new_password.html", token=token, form=form)
        else:
            flash("Token expired, please try again", "danger")
            return redirect(url_for('home'))


# Admin access
@app.route('/all_users')
def admin_all_users():
    if session["user-role"] == "Admin":
        all_users = []
        db = shelve.open('storage.db')
        user_db = db["Users"]
        for user in user_db.values():
            if user.get_NRIC() != session["user-NRIC"]:
                all_users.append(user)
        return render_template("Admin/all_users.html", all_users=all_users)

    flash("Access denied", "danger")
    return redirect(url_for('home'))


@app.route('/admin_update/<uid>', methods=["GET", "POST"])
def admin_update(uid):
    if session["user-role"] == "Admin":
        form = AdminUpdateForm(request.form)
        db = shelve.open("storage.db", flag="w", writeback=True)
        user_db = db["Users"]
        user = user_db[uid]

        if request.method == "POST" and form.validate():
            user.set_email(form.Email.data)
            user.set_password(form.Password.data)
            user.set_url(form.URL.data)
            appointment_dict = db['Appointments']
            for appts in appointment_dict:
                print(appointment_dict[appts])
                if appointment_dict[appts].get_doctor() == user.get_first_name() + " " + user.get_last_name():
                    appointment_dict[appts].set_url(user.get_url())
            flash("Successfully updated")

        db.close()

        return render_template("Admin/admin_update.html", user=user, form=form)

    else:
        flash("Access denied", "danger")
        return redirect(url_for("home"))


@app.route('/admin_delete/<uid>', methods=["GET"])
def admin_delete(uid):
    if session["user-role"] == "Admin":
        db = shelve.open('storage.db')
        user_db = db["Users"]
        del user_db[uid]
        db['Users'] = user_db
        db.close()
        flash("Successfully deleted user", "success")
        return redirect(url_for('admin_all_users'))
    else:
        flash("Access denied", "danger")
        return redirect(url_for('home'))


@app.route('/add_doctor', methods=["GET", "POST"])
def add_doctor():
    if session["user-role"] == "Admin":
        form = RegisterForm(request.form)
        if request.method == "POST" and form.validate():
            db = shelve.open('storage.db', 'c')
            users_dict = db['Users']

            if form.NRIC.data in users_dict:
                flash("This NRIC is already in used.You can login to access our service.", "danger")
                return redirect(url_for('admin_all_users'))
            else:
                user = Users.Doctor(form.NRIC.data, form.FirstName.data, form.LastName.data, form.Gender.data,
                                    form.Dob.data,
                                    form.Email.data, form.Password.data, form.specialization.data, form.URL.data)
                user.set_role("Doctor")
                users_dict[user.get_NRIC()] = user
                db['Users'] = users_dict
                flash(f'Account created for {form.FirstName.data} {form.LastName.data}!', 'success')
                return redirect(url_for('login'))
        return render_template("Admin/add_doctor.html", form=form)
    else:
        flash("Access denied", "danger")
        return redirect(url_for('home'))


# AppointmentSystem
@app.route('/appointment_list')
def appointment():
    db = shelve.open('storage.db', 'c')
    appointment_dict = db['Appointments']
    appointment_list = []
    year_month = []
    period = {}
    for key in appointment_dict:
        appointment = appointment_dict.get(key)
        if appointment.get_patient() == session['user'] or appointment.get_doctor() == session['user'] or session[
            'user-role'] == 'Admin':
            appointment_list.append(appointment)
    for appt in appointment_list:
        date = appt.get_date()
        time = appt.get_time()
        appt_date = validate_history(date, time)
        if appt_date:
            appointment_list.remove(appt)
    appointment_list.sort(key=lambda x: x.get_datetime())
    for i in range(len(appointment_list)):
        date = appointment_list[i].get_date()
        appt_date = date.strftime("%Y-%m-%d")
        month = appt_date.split("-")[1]
        year = appt_date.split("-")[0]
        ym = year + "-" + month
        if ym not in year_month:
            year_month.append(ym)
    for i in range(len(year_month)):
        current_month = []
        for appt in appointment_list:
            date = appt.get_date()
            appt_date = date.strftime("%Y-%m-%d")
            month = appt_date.split("-")[1]
            year = appt_date.split("-")[0]
            ym = year + "-" + month
            if ym == year_month[i]:
                current_month.append(appt)
        period[year_month[i]] = current_month
    return render_template('Appointment/appointment_list.html', period=period, number=len(appointment_list))


@app.route('/appointment_history')
def appointment_hist():
    db = shelve.open('storage.db', 'c')
    appointment_dict = db['Appointments']
    appointment_list = []
    appointment_hist = []
    for key in appointment_dict:
        appointment = appointment_dict.get(key)
        if appointment.get_patient() == session['user'] or appointment.get_doctor() == session['user'] or session[
            'user-role'] == 'Admin':
            appointment_list.append(appointment)
    for appt in appointment_list:
        date = appt.get_date()
        time = appt.get_time()
        appt_date = validate_history(date, time)
        if appt_date:
            appointment_hist.append(appt)
    appointment_len = len(appointment_hist)
    return render_template('Appointment/appointment_hist.html', appointment_list=appointment_hist,
                           appointment_len=appointment_len)


@app.route('/appointment_summary')
def appointment_summary():
    global current_month
    db = shelve.open('storage.db', 'c')
    appointment_dict = db['Appointments']
    appointment_list = []
    year_month = []
    period = {}
    for key in appointment_dict:
        appointment = appointment_dict.get(key)
        if appointment.get_patient() == session['user'] or appointment.get_doctor() == session['user'] or session[
            'user-role'] == 'Admin':
            appointment_list.append(appointment)
    appointment_list.sort(key=lambda x: x.get_datetime(), reverse=True)
    for i in range(len(appointment_list)):
        date = appointment_list[i].get_date()
        appt_date = date.strftime("%Y-%m-%d")
        month = appt_date.split("-")[1]
        year = appt_date.split("-")[0]
        ym = year + "-" + month
        if ym not in year_month:
            year_month.append(ym)
    for i in range(len(year_month)):
        current_month = []
        for appt in appointment_list:
            date = appt.get_date()
            appt_date = date.strftime("%Y-%m-%d")
            month = appt_date.split("-")[1]
            year = appt_date.split("-")[0]
            ym = year + "-" + month
            if ym == year_month[i]:
                current_month.append(appt)
        period[year_month[i]] = len(current_month)
    return render_template('Appointment/appointment_summary.html', period=period)


@app.route("/show_pyecharts")
def showechart():
    db = shelve.open('storage.db', 'c')
    appointment_dict = db['Appointments']
    appointment_list = []
    time_visitor = {'8AM': 0, "10AM": 0, "12PM": 0, "2PM": 0, "4PM": 0, "6PM": 0, "8PM": 0, "10PM": 0}
    xdata = []
    ydata = []
    for key in appointment_dict:
        appointment = appointment_dict.get(key)
        appointment_list.append(appointment)
    for appt in appointment_list:
        time = appt.get_time()
        if time == "8:00:00":
            time_visitor['8AM'] += 1
        elif time == "10:00:00":
            time_visitor['10AM'] += 1
        elif time == "12:00:00":
            time_visitor['12PM'] += 1
        elif time == "14:00:00":
            time_visitor['2PM'] += 1
        elif time == "16:00:00":
            time_visitor['4PM'] += 1
        elif time == "18:00:00":
            time_visitor['6PM'] += 1
        elif time == "20:00:00":
            time_visitor['8PM'] += 1
        elif time == "22:00:00":
            time_visitor['10PM'] += 1
    for key in time_visitor:
        xdata.append(key)
        ydata.append(time_visitor[key])
    bargraph(xdata, ydata)
    return render_template("Appointment/charts.html")


@app.route('/appointment', methods=['GET', 'POST'])
def add_appointment():
    global users_dict
    form = AppointmentForm(request.form)
    if request.method == "POST" and form.validate():
        db = shelve.open('storage.db', 'c')
        appointment_dict = db['Appointments']
        users_dict = db['Users']
        appdate = validate_date(form.Date.data, form.Time.data)
        appt = appointments.Appointment(form.Date.data, form.Time.data, form.Department.data, form.Type.data)
        appt.set_patient(session['user'])
        repeated = validate_repeated(appointment_dict, appt, session['user'])
        if appdate:
            flash("Invalid Date or Time!", 'danger')
        elif repeated:
            flash("You can only have 1 appointment at 1 timing!", 'danger')
        else:
            assignDoctor(appt)
            appt.set_id(id(appt))
            appointment_dict[appt.get_id()] = appt
            db['Appointments'] = appointment_dict
            # user = users_dict[session['user-NRIC']]
            flash("Appointment has been booked!View it in appointment list!", 'success')
            # send_email.sendmail(user.get_email(), appt.get_department(), appt.get_doctor(),appt.get_date(),appt.get_time(),appt.get_venue())
            # flash('An Email has been sent to your email address!', 'success')
            return redirect(url_for('home'))
    return render_template('Appointment/appointment.html', form=form)


@app.route('/docappointment', methods=['GET', 'POST'])
def doc_add_appointment():
    form = DocAppointmentForm(request.form)
    db = shelve.open('storage.db', 'c')
    appointment_dict = db['Appointments']
    user_dict = db["Users"]
    form.Department.data = user_dict[session['user-NRIC']].get_specialization()
    if request.method == "POST" and form.validate():
        appdate = validate_date(form.Date.data, form.Time.data)
        appt = appointments.Appointment(form.Date.data, form.Time.data, form.Department.data, form.Type.data)
        appt.set_patient(form.Patient.data)
        appt.set_doctor(session['user'])
        repeated = validate_repeated(appointment_dict, appt, form.Patient.data)
        if appdate:
            flash("Invalid Date or Time!", 'danger')
        elif repeated:
            flash("You can only have 1 appointment at 1 timing!", 'danger')
        else:
            appt.set_id(id(appt))
            appointment_dict[appt.get_id()] = appt
            db['Appointments'] = appointment_dict
            # user = users_dict[session['user-NRIC']]
            flash("Appointment has been booked!View it in appointment list!", 'success')
            # send_email.sendmail(user.get_email(), appt.get_department(), appt.get_doctor(),appt.get_date(),appt.get_time(),appt.get_venue())
            # flash('An Email has been sent to your email address!', 'success')
            return redirect(url_for('home'))
    return render_template('Appointment/docappointment.html', form=form)


@app.route('/Updateappointment/<id>', methods=['GET', 'POST'])
def update_appointment(id):
    form = AppointmentForm(request.form)
    if request.method == "POST" and form.validate():
        db = shelve.open('storage.db', 'c')
        appointment_dict = db['Appointments']
        appt = appointment_dict[int(id)]
        newappt = appointments.Appointment(form.Date.data, form.Time.data, form.Department.data, form.Type.data)
        appdate = validate_date(form.Date.data, form.Time.data)
        repeated = validate_repeated(appointment_dict, newappt, session['user'])
        if appdate:
            flash("Invalid Date!", 'danger')
        elif repeated:
            flash("You can only have 1 appointment at 1 timing!", 'danger')
        else:
            assignDoctor(appt)
            appt.set_date(form.Date.data)
            appt.set_time(form.Time.data)
            appt.set_department(form.Department.data)
            appt.set_venue(form.Type.data)
            appointment_dict[appt.get_id()] = appt

            # user = users_dict[session['user-NRIC']]
            db['Appointments'] = appointment_dict
            flash("Appointment has been changed!View it in appointment list!", 'success')
            # send_email.sendmail(user.get_email(), appt.get_department(), appt.get_doctor(),appt.get_date(),appt.get_time(),appt.get_venue())
            # flash('An Email has been sent to your email address!', 'success')
            return redirect(url_for('home'))
        return redirect(url_for('update_appointment', id=id))

    else:
        db = shelve.open('storage.db', 'r')
        appointment_dict = db['Appointments']
        db.close()
        appt = appointment_dict[int(id)]
        form.Date.data = appt.get_date()
        form.Time.data = appt.get_time()
        form.Type.data = appt.get_venue()
        form.Department.data = appt.get_department()

        return render_template('Appointment/updateAppointment.html', form=form)


@app.route('/deleteAppointment/<id>', methods=['POST'])
def delete_appointment(id):
    db = shelve.open('storage.db', 'w')
    appointment_dict = db['Appointments']
    appointment_dict.pop(int(id))
    db['Appointments'] = appointment_dict
    flash("Appointment has been deleted", 'danger')
    db.close()
    return redirect(url_for('appointment'))


def validate_date(date, time):
    date = date.strftime("%Y-%m-%d")
    appt_time = datetime.strptime(date + " " + time, '%Y-%m-%d %H:%M:%S')
    now = datetime.now()
    if now > appt_time:
        return True


def validate_history(date, time):
    date2 = date.strftime("%Y-%m-%d")
    now = datetime.now()
    dt = date2 + " " + time
    appt_time = datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
    if now > appt_time:
        return True


def validate_repeated(appointment_dict, appt, user):
    for key in appointment_dict:
        if appointment_dict[key].get_patient() == user and appt.get_date() == appointment_dict[
            key].get_date() and appt.get_time() == appointment_dict[key].get_time():
            return True


def assignDoctor(appointment):
    doc_list = []
    appointment_no = 0
    db = shelve.open('storage.db', 'c')
    user_dict = db['Users']
    appointment_dict = db['Appointments']
    for key in user_dict:
        if isinstance(user_dict[key], Users.Doctor) and appointment.get_department() == user_dict[
            key].get_specialization():
            doc_list.append(user_dict[key])
    for doctor in doc_list:
        for appts in appointment_dict:
            if appointment_dict[appts].get_doctor() == doctor.get_first_name() + " " + doctor.get_last_name():
                appointment_no += 1
            if appointment_no <= 3:
                appointment.set_doctor(f'{doctor.get_first_name()} {doctor.get_last_name()}')
                appointment.set_url(doctor.get_url())
                break


# Contact Us
@app.route('/contactus', methods=['GET', 'POST'])
def contactus():
    form = ContactForm()
    if form.validate_on_submit():
        flash(
            f'You have successfully submitted the form. Please wait 2-3 working days for reply and also check your email.Thank you.',
            'success')
        name = request.form['name']
        email = request.form['email']
        subject = request.form['subject']
        enquiries = request.form['enquiries']
        msg = Message(subject,
                      sender=app.config.get("MAIL_USERNAME"),
                      recipients=[email],
                      body="Hi " + name + ',\n\n Thanks a lot for getting in touch with us. \n \n This is an automatic email just to let you know that we have received your enquiries.\n\n'
                                          'This is the message that you sent.\n' + enquiries)
        mail.send(msg)
        return redirect(url_for('contactus'))
    return render_template('FAQ/contactus.html', title='Contact Us', form=form)


# FAQ
@app.route('/faq', methods=['GET', 'POST'])
def create_faq():
    create_faq_form = FAQ(request.form)
    if request.method == 'POST' and create_faq_form.validate():
        qn_dict = {}
        db = shelve.open('storage.db', 'c')
        try:
            qn_dict = db['FAQ']
        except:
            print("Error in retrieving Questions from storage.db.")

        question = qns.FAQ(create_faq_form.question.data, create_faq_form.answer.data, create_faq_form.date.data)
        qn_dict[question.get_qns_id()] = question
        db['FAQ'] = qn_dict

        db.close()

        return redirect(url_for('create_faq'))
    return render_template('FAQ/faq.html', form=create_faq_form)


@app.route('/retrieveQns', methods=['GET', 'POST'])
def retrieve_qns():
    search = SearchBar(request.form)
    if request.method == 'POST' and search.validate():
        qns_list = []
        sql = f"Select * from FA_Qs where question like '%{search.search.data}%'"
        questions = db.engine.execute(sql)
        for i in questions:
            item = FAQ(i.id, i.question, i.answer, i.date)
            qns_list.append(item)
        return render_template('FAQ/retrieveQns.html', count=len(qns_list), qn_list=qns_list, form=search)

    qn_list = []
    questions = FAQs.query.all()
    for i in questions:
        item = FAQ(i.id, i.question, i.answer, i.date)
        qn_list.append(item)
    return render_template('FAQ/retrieveQns.html', count=len(qn_list), qn_list=qn_list, form=search)


@app.route('/updateQns/<int:id>/', methods=['GET', 'POST'])
def update_qns(id):
    update_faq_form = FAQ(request.form)
    if request.method == 'POST' and update_faq_form.validate():
        db = shelve.open('storage.db', 'w')
        qn_dict = db['FAQ']

        question = qn_dict.get(id)
        question.set_question(update_faq_form.question.data)
        question.set_answer(update_faq_form.answer.data)
        question.set_date(update_faq_form.date.data)

        db['FAQ'] = qn_dict
        db.close()

        return redirect(url_for('retrieve_qns'))
    else:
        db = shelve.open('storage.db', 'r')
        qn_dict = db['FAQ']
        db.close()

        question = qn_dict.get(id)
        update_faq_form.question.data = question.get_question()
        update_faq_form.answer.data = question.get_answer()
        update_faq_form.date.data = question.get_date()

        return render_template('FAQ/updateQns.html', form=update_faq_form)


@app.route('/deleteQns/<int:id>', methods=['POST'])
def delete_qns(id):
    db = shelve.open('storage.db', 'w')
    qn_dict = db['FAQ']

    qn_dict.pop(id)

    db['FAQ'] = qn_dict
    db.close()

    return redirect(url_for('retrieve_qns'))


# Application Form
@app.route('/createApplicant', methods=['GET', 'POST'])
def create_applicant():
    create_applicant_form = CreateApplicationForm(request.form)

    if request.method == 'POST' and create_applicant_form.validate():
        applicants_dict = {}
        db = shelve.open('storage.db', 'c')

        try:
            applicants_dict = db['Applicant']
        except:
            print("Error in retrieving Applicants from storage.db.")

        # parsing parameters into Application Class in Application.py
        applicant = Applicant.Applicant(create_applicant_form.fname.data, create_applicant_form.lname.data,
                                        create_applicant_form.nric.data,
                                        create_applicant_form.email.data, create_applicant_form.age.data,
                                        create_applicant_form.address.data, create_applicant_form.gender.data,
                                        create_applicant_form.nationality.data, create_applicant_form.language.data,
                                        create_applicant_form.phoneno.data, create_applicant_form.quali.data,
                                        create_applicant_form.industry.data,
                                        create_applicant_form.comp1.data,
                                        create_applicant_form.posi1.data, create_applicant_form.comp2.data,
                                        create_applicant_form.posi2.data, create_applicant_form.empty1.data,
                                        create_applicant_form.empty2.data)

        applicants_dict[applicant.get_applicantid()] = applicant

        db['Applicant'] = applicants_dict

        # Automatically Send Email Codes
        sender_email = "nyppolyclinic@gmail.com"
        password = "helloworld123"
        rec_email = create_applicant_form.email.data
        subject = "Application for NYP Polyclinic"
        body = "Hello, we have received your application. Please wait for a few days for us to update you about the status. Thank you."
        message = "Subject: {}\n\n{}".format(subject, body)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        print("Login Success")
        server.sendmail(sender_email, rec_email, message)
        print("Email has been sent to ", rec_email)
        # Automatically Send Email Codes

        db.close()

        session['applicant_created'] = applicant.get_first_name() + ' ' + applicant.get_last_name()
        return redirect(url_for('create_applicant'))
    return render_template('ApplicationForm/applicationForm.html', form=create_applicant_form)


@app.route('/retrieveApplicants')
def retrieve_applicants():
    db = shelve.open('storage.db', 'r')
    applicants_dict = db['Applicant']
    db.close()

    applicants_list = []

    for key in applicants_dict:
        applicants = applicants_dict.get(key)
        applicants_list.append(applicants)

    return render_template('ApplicationForm/retrieveApplicants.html', count=len(applicants_list),
                           applicants_list=applicants_list)


@app.route('/updateApplicants/<int:id>/', methods=['GET', 'POST'])
def update_applicants(id):
    update_applicant_form = CreateApplicationForm(request.form)
    if request.method == 'POST' and update_applicant_form.validate():

        db = shelve.open('storage.db', 'w')
        applicants_dict = db['Applicant']

        # after submit, setting the updated inputs.
        # problem now is that updated employment does not display
        applicant = applicants_dict.get(id)
        applicant.set_first_name(update_applicant_form.fname.data)
        applicant.set_last_name(update_applicant_form.lname.data)
        applicant.set_NRIC(update_applicant_form.nric.data)
        applicant.set_email(update_applicant_form.email.data)
        applicant.set_age(update_applicant_form.age.data)
        applicant.set_address(update_applicant_form.address.data)
        applicant.set_gender(update_applicant_form.gender.data)
        applicant.set_nationality(update_applicant_form.nationality.data)
        applicant.set_language(update_applicant_form.language.data)
        applicant.set_phonenumber(update_applicant_form.phoneno.data)
        applicant.set_qualification(update_applicant_form.quali.data)
        applicant.set_industry(update_applicant_form.industry.data)
        applicant.set_company1(update_applicant_form.comp1.data)
        applicant.set_postion1(update_applicant_form.posi1.data)
        applicant.set_company2(update_applicant_form.comp2.data)
        applicant.set_postion2(update_applicant_form.posi2.data)
        db['Applicant'] = applicants_dict

        # Automatically Send Email Codes
        sender_email = "nyppolyclinic@gmail.com"
        password = "helloworld123"
        rec_email = applicant.get_email()
        subject = "Application for NYP Polyclinic"
        body = "Hello, we have received your updated application. Please wait for a few days for us to update you about the status. Thank you."
        message = "Subject: {}\n\n{}".format(subject, body)
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, password)
        print("Login Success")
        server.sendmail(sender_email, rec_email, message)
        print("Email has been sent to ", rec_email)
        # Automatically Send Email Codes

        db.close()

        session['applicant_updated'] = applicant.get_first_name() + ' ' + applicant.get_last_name()

        return redirect(url_for('home'))

    else:

        db = shelve.open('storage.db', 'r')
        applicants_dict = db['Applicant']
        db.close()

        # get data input and place in in the field
        applicant = applicants_dict.get(id)
        update_applicant_form.fname.data = applicant.get_first_name()
        update_applicant_form.lname.data = applicant.get_last_name()
        update_applicant_form.nric.data = applicant.get_NRIC()
        update_applicant_form.email.data = applicant.get_email()
        update_applicant_form.age.data = applicant.get_age()
        update_applicant_form.address.data = applicant.get_address()
        update_applicant_form.gender.data = applicant.get_gender()
        update_applicant_form.nationality.data = applicant.get_nationality()
        update_applicant_form.language.data = applicant.get_language()
        update_applicant_form.phoneno.data = applicant.get_phonenumber()
        update_applicant_form.quali.data = applicant.get_qualification()
        update_applicant_form.industry.data = applicant.get_industry()
        update_applicant_form.comp1.data = applicant.get_company1()
        update_applicant_form.posi1.data = applicant.get_position1()
        update_applicant_form.comp2.data = applicant.get_company2()
        update_applicant_form.posi2.data = applicant.get_position2()

        return render_template('ApplicationForm/updateApplicant.html', form=update_applicant_form)


@app.route('/deleteApplicant/<int:id>', methods=['POST'])
def delete_applicant(id):
    db = shelve.open('storage.db', 'w')
    applicants_dict = db['Applicant']

    applicant = applicants_dict.pop(id)

    db['Applicant'] = applicants_dict
    db.close()
    session['applicant_deleted'] = applicant.get_first_name() + ' ' + applicant.get_last_name()
    return redirect(url_for('retrieve_applicants'))


@app.errorhandler(404)
def page_not_handle(e):
    return render_template("error404.html"), 404


@app.errorhandler(429)
def frequent_request(e):
    return render_template("error429.html"), 429


if __name__ == '__main__':
    app.run(debug=True)
