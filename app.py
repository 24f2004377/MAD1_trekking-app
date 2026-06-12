from flask import Flask,render_template,request,session, redirect
from sqlalchemy import inspect
from werkzeug.security import generate_password_hash, check_password_hash
from extensions import db
from datetime import date,datetime
from werkzeug.utils import secure_filename
import os
from flask import flash
from flask import jsonify
from models import User, Trek, Booking

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret123'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///trek.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# CONNECT DB
db.init_app(app)
# CREATE TABLES
with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)
    print(inspector.get_table_names())
    admin = User.query.filter_by(
    email='admin@gmail.com').first()
    if not admin:
        admin_user = User(
            name='Admin',
            email='admin@gmail.com',
            password=generate_password_hash('admin123'),
            role='admin'
        )
        db.session.add(admin_user)
        db.session.commit()
        print("Admin Created")
@app.route('/')
def home():
    recent_treks=Trek.query.order_by(Trek.id.desc()).limit(3).all()

    print('Database Working')
    return render_template('/home.html',recent_treks=recent_treks)
@app.route('/all_treks')
def all_treks():
    search = request.args.get('search', '')
    if search:
        treks = Trek.query.filter(Trek.name.ilike(f'%{search}%')).all()
    else:
        treks = Trek.query.all()
    return render_template('all_treks.html',treks=treks,search=search)
@app.route('/all_users')
def all_users():
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'admin':
        return "Access Denied"
    search = request.args.get('search', '')
    if search:
        user_list = User.query.filter(User.role == 'user',User.name.ilike(f'%{search}%')).all()
    else:
        user_list = User.query.filter_by(role='user').order_by(User.id.desc()).all()
    return render_template('all_users.html',user_list=user_list)
@app.route('/all_staff')
def all_staff():
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'admin':
        return "Access Denied"
    search = request.args.get('search', '')
    if search:
        staff_list = User.query.filter(User.role == 'staff',User.name.ilike(f'%{search}%')).all()
    else:
        staff_list = User.query.filter_by(role='staff').order_by(User.id.desc()).all()
    return render_template('all_staff.html',staff_list=staff_list)
@app.route('/admin')
def admin():
    if 'user_id' not in session:
        return redirect('/login.html')
    if session['role'] != 'admin':
        return "Access Denied"
    staff_list = User.query.filter_by(role='staff').all()
    user_list = User.query.filter_by(role='user').all()
    treks = Trek.query.all()
    bookings = Booking.query.all()
    total_users = User.query.filter_by(role='user').count()
    total_staff = User.query.filter_by(role='staff').count()
    total_treks = Trek.query.count()
    total_bookings = Booking.query.count()
    pending_staff = User.query.filter_by(role='staff',approved=False).count()
    booking_data = []
    for booking in Booking.query.all():
        user = User.query.get(booking.User_ID)
        trek = Trek.query.get(booking.Trek_ID)
        booking_data.append({
            'booking': booking,
            'user': user,
            'trek': trek
        })
        print("Bookings:", len(booking_data))
    history_treks=Trek.query.filter(Trek.status.in_(['Completed','Closed'])).all()
    search_trek = request.args.get('search_trek', '')
    show_all = request.args.get('show_all')
    if search_trek:
        treks = Trek.query.filter(Trek.name.ilike(f'%{search_trek}%')).all()
    else:
        treks = Trek.query.order_by(Trek.id.desc()).limit(3).all()
    active_users_count = User.query.filter_by(role='user',blacklisted=False).count()
    search_user = request.args.get('search_user', '')
    show_all_users = request.args.get('show_all_users')
    if search_user:
        user_list = User.query.filter(User.role == 'user', User.name.ilike(f'%{search_user}%')).all()
    else:
        user_list = User.query.filter_by(role='user').order_by(User.id.desc()).limit(3).all()

    active_staff_count = User.query.filter_by(role='user',blacklisted=False).count()
    search_staff = request.args.get('search_staff','')
    show_all_staff = request.args.get('show_all_staff')
    if search_staff:
        staff_list = User.query.filter(User.role == 'staff',User.name.ilike(f'%{search_staff}%')).all()
    else:
        staff_list = User.query.filter_by(role='staff').order_by(User.id.desc()).limit(3).all()
    return render_template(
        'admin.html',total_users=total_users,
        total_staff=total_staff,
        total_treks=total_treks,
        total_bookings=total_bookings,
        pending_staff=pending_staff,staff_list=staff_list,
        user_list=user_list,
        treks=treks,
        bookings=bookings,booking_data=booking_data,
        history_treks=history_treks,
        show_all=show_all,
        show_all_users=show_all_users,
        active_users_count=active_users_count,
        active_staff_count=active_staff_count,
        show_all_staff=show_all_staff
        # user_list=user
        # recent_bookings=recent_bookings,
    )
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        role = request.form['role']
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return "Email already exists"
        new_staff = User(
            name=name,
            email=email,
            password=password,
            role=role,
            approved=(role == 'user')
        )
        
        db.session.add(new_staff)
        db.session.commit()
        flash("Registration successful! Waiting for Admin Approval.")
        
    return render_template('register.html')
@app.route('/login', methods=['GET', 'POST'])
def login(): 
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password,password):
            # SAVE USER IN SESSION
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['role'] = user.role
            if user.blacklisted:
                return "Your account has been blacklisted"
            elif user.role == 'admin':
                return redirect('/admin')
            elif user.approved==False:
                return "Waiting For Admin Approval"
            elif user.role == 'staff':
                return redirect('/staff')
            elif user.role == 'user':
                return redirect('/user_dashboard')
            else:
                return redirect('/dashboard')
        return render_template('login.html',error="Invalid email or password")
    return render_template('login.html', error='Not valid email user')
@app.route('/user_dashboard')
def user_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'user':
        return "Access Denied"
    treks = Trek.query.all()
    search = request.args.get('search', '')
    difficulty = request.args.get('difficulty', '')
    location = request.args.get('location','')
    availability = request.args.get('availability', '')
    query = Trek.query
    if search:
        query = query.filter(Trek.name.ilike(f'%{search}%'))
    if location:
        query = query.filter(Trek.location.ilike(f'%{location}%'))
    if difficulty:
        query = query.filter(Trek.difficulty == difficulty)
    if availability == 'available':
        query = query.filter(Trek.available_slots > 0)
    treks = query.all()
    return render_template('user_dashboard.html',treks=treks,name=session['user_name'])
@app.route('/create_trek', methods=['GET', 'POST'])
def create_trek():
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'admin':
        return "Access Denied"
    staff_members=User.query.filter_by(role='staff',approved=True).all()
    if request.method == 'POST':
        name = request.form['name']
        location = request.form['location']
        duration=request.form['duration']
        available_slots = request.form['available_slots']
        assigned_staff_id = request.form['assigned_staff_id']
        difficulty = request.form['difficulty']
        start_date = datetime.strptime(request.form['start_date'],'%Y-%m-%d').date()
        end_date = datetime.strptime(request.form['end_date'],'%Y-%m-%d').date()
        image = request.files.get('image')
        filename = None
        if image and image.filename:
            filename = secure_filename(image.filename)
            image.save(os.path.join('static', filename))
        else:
            filename="trekking_1.jpg"
        trek_details = request.form['trek_details']
        trek = Trek(
            name=name,
            location=location,
            duration=duration,
            available_slots=available_slots,
            assigned_staff_id=assigned_staff_id,
            difficulty=difficulty,
            start_date=start_date,
            end_date=end_date,
            image=filename,
            trek_details=trek_details
        )
        if not all([name, location, duration,available_slots,assigned_staff_id,difficulty,start_date,end_date,]):
            return "Please fill all required fields"
        db.session.add(trek)
        db.session.commit()
        return "Trek Created Successfully"
    return render_template('create_trek.html',staff_members=staff_members)
@app.route('/user_details/<int:user_id>')
def user_details(user_id):
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'admin':
        return "Access Denied"
    user = User.query.get(user_id)
    if not user:
        return "User Not Found"
    bookings = Booking.query.filter_by(User_ID=user.id).all()
    booking_data = []
    current_bookings = []
    for booking in bookings:
        trek = Trek.query.get(booking.Trek_ID)
        assigned_staff = None
        if trek and trek.assigned_staff_id:
            assigned_staff = User.query.get(
                trek.assigned_staff_id
            )
        booking_data.append({
        'booking': booking,
        'trek': trek,
        'staff': assigned_staff
    })
        if booking.Status == 'Booked':
            current_bookings.append({
                'booking': booking,
                'trek': trek
            })
    total_bookings = len(bookings)
    cancelled_treks = Booking.query.filter_by(User_ID=user.id,Status='Cancelled').count()
    current_treks = Booking.query.filter_by(User_ID=user.id,Status='Booked').count()
    return render_template(
        'user_details.html',
        user=user,
        booking_data=booking_data,
        current_bookings=current_bookings,
        total_bookings=total_bookings,
        current_treks=current_treks,
        cancelled_treks=cancelled_treks,
        # assigned_staff=assigned_staff
    )
@app.route('/staff_details/<int:staff_id>')
def staff_details(staff_id):
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'admin':
        return "Access Denied"
    staff = User.query.get(staff_id)
    if not staff:
        return "Staff Not Found"
    assigned_treks = Trek.query.filter_by(assigned_staff_id=staff.id).all()
    total_treks = len(assigned_treks)
    ongoing_treks = 0
    open_treks = 0
    closed_treks = 0
    completed_treks = 0
    total_participants = 0
    trek_reports = []
    for trek in assigned_treks:
        if trek.status == "Open":
            open_treks += 1
        elif trek.status == "Closed":
            closed_treks += 1
        elif trek.status == "Completed":
            completed_treks += 1
        elif trek.status == "Ongoing":
            ongoing_treks += 1
        booked_users = []
        cancelled_users = []
        bookings = Booking.query.filter_by(Trek_ID=trek.id).all()
        for booking in bookings:
            user = User.query.get(booking.User_ID)
            if booking.Status == "Booked":
                booked_users.append(user)
                total_participants += 1
            elif booking.Status == "Cancelled":
                cancelled_users.append(user)
        trek_reports.append({
            'trek': trek,
            'booked_users': booked_users,
            'cancelled_users': cancelled_users,
            'booking_count': len(booked_users)})
    return render_template(
        'staff_details.html',
        staff=staff,
        total_treks=total_treks,
        open_treks=open_treks,
        closed_treks=closed_treks,
        completed_treks=completed_treks,
        ongoing_treks=ongoing_treks,
        total_participants=total_participants,
        trek_reports=trek_reports
    )
@app.route('/trek_details/<int:trek_id>')
def trek_details(trek_id):
    if session['role'] != 'admin':
        return "Access Denied"
    trek = Trek.query.get_or_404(trek_id)
    staff = None
    if trek.assigned_staff_id:
        staff = User.query.get(trek.assigned_staff_id)
    bookings = Booking.query.filter_by(Trek_ID=trek_id).all()
    booking_details = []
    for booking in bookings:
        user = User.query.get(booking.User_ID)
        booking_details.append({'user': user,'booking': booking})
    return render_template(
        'trek_details.html',
        trek=trek,
        staff=staff,
        booking_details=booking_details
    )
@app.route('/delete_trek/<name>')
def delete_trek(name):
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'admin':
        return "Access Denied"
    trek = Trek.query.get(name)
    db.session.delete(trek)
    db.session.commit()
    return redirect('/all_treks')
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    return f"Welcome User {session['user_name']}"
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')
@app.route('/pending-staff')
def pending_staff():
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect('/login')
    # Check if user is admin
    if session['role'] != 'admin':
        return "Access Denied"
    # Get all unapproved staff members
    staff_users = User.query.filter_by(role='staff',approved=False).all()
    return render_template('pending_staff.html',staff_users=staff_users)
@app.route('/approve_staff/<int:id>')
def approve_staff(id):
    # Check if user is logged in
    if 'user_id' not in session:
        return redirect('/login')
    # Check if user is admin
    if session['role'] != 'admin':
        return "Access Denied"
    # Find staff member
    staff = User.query.get(id)    
    # Check if staff exists
    if not staff:
        return "Staff Not Found"
    # Approve staff
    staff.approved = True
    db.session.commit()
    return render_template('/pending_staff.html')
@app.route('/reject-staff/<int:id>')
def reject_staff(id):
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'admin':
        return "Access Denied"
    staff = User.query.get(id)
    if not staff:
        return "Staff Not Found"
    db.session.delete(staff)
    db.session.commit()
    return redirect('/pending_staff')
@app.route('/staff')
def staff_dashboard():
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'staff':
        return "Access Denied"
    #treks=Trek.query.all()
    #treks = Trek.query.filter_by(staff_id=session['user_id']).all()
    assigned_treks = Trek.query.filter_by(assigned_staff_id=session['user_id']).all()
    trek_user_report = []
    for trek in assigned_treks:
        bookings = Booking.query.filter_by(Trek_ID=trek.id,Status='Booked').all()
        users = []
        for booking in bookings:
            user = User.query.get(booking.User_ID)
            if user:
                users.append(user)
        trek_user_report.append({
            'trek': trek,
            'users': users
        })
    return render_template('staff_dashboard.html',assigned_treks=assigned_treks,trek_user_report=trek_user_report)
@app.route('/staff_edit_trek/<int:id>', methods=['GET', 'POST'])
def staff_edit_trek(id):
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'staff':
        return "Access Denied"
    trek = Trek.query.get(id)
    if not trek:
        return "Trek Not Found"
    if trek.assigned_staff_id != session['user_id']:
        return "You are not assigned to this trek"
    if request.method == 'POST':
        trek.available_slots = int(
            request.form['available_slots']
        )
        trek.status = request.form['status']
        db.session.commit()
        return redirect('/staff')
    return render_template('staff_edit_trek.html',trek=trek)
@app.route('/book_trek/<int:trek_id>')
def book_trek(trek_id):
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'user':
        return "Access Denied"
    trek = Trek.query.get(trek_id)
    if not trek:
        return "Trek Not Found"
    if trek.status == 'Closed' :
        return f"This trek is {trek.status} and cannot be booked"
    elif trek.status == 'Completed' :
        return "This trek is completed and so cannot be booked"
    existing_booking = Booking.query.filter_by(
        User_ID=session['user_id'],Trek_ID=trek_id,Status='Booked').first()
    if existing_booking:
        return "You have already booked this trek"
    if trek.available_slots <= 0:
        return "No slots available"
    trek.available_slots -= 1
    booking = Booking(
        User_ID=session['user_id'],
        Trek_ID=trek_id,
        Booking_Date=date.today(),
        Status='Booked'
    )
    db.session.add(booking)
    db.session.commit()
    return redirect('/my_bookings')
@app.route('/my_bookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect('/login')
    bookings = Booking.query.filter_by(User_ID=session['user_id']).all()
    booking_data = []
    for booking in bookings:
        user=User.query.get(booking.User_ID)
        trek = Trek.query.get(booking.Trek_ID)
        booking_data.append({
            'booking': booking,
            'trek': trek,
            'user':user
        })
    return render_template(
        'my_bookings.html',
        booking_data=booking_data
    )
@app.route('/cancel_booking/<int:booking_id>')
def cancel_booking(booking_id):
    if 'user_id' not in session:
        return redirect('/login')
    booking = Booking.query.get(booking_id)
    if not booking:
        return "Booking Not Found"
    if booking.User_ID != session['user_id']:
        return "Access Denied"
    trek = Trek.query.get(booking.Trek_ID)
    if trek:
        trek.available_slots += 1
        booking.Status = "Cancelled"
    db.session.commit()
    return redirect('/my_bookings')
@app.route('/edit_trek/<int:id>', methods=['GET', 'POST'])
def edit_trek(id):
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'admin':
        return "Access Denied"
    trek = Trek.query.get(id)
    if not trek:
        return "Trek Not Found"
    staff_members=User.query.filter_by(role='staff',approved=True).all()
    if request.method == 'POST':
        trek.name = request.form['name']
        trek.location = request.form['location']
        trek.duration=request.form['duration']
        trek.available_slots = request.form['available_slots']
        trek.assigned_staff_id = request.form['assigned_staff_id']
        trek.difficulty = request.form['difficulty']
        trek.start_date = datetime.strptime(request.form['start_date'],'%Y-%m-%d').date()
        trek.end_date = datetime.strptime(request.form['end_date'],'%Y-%m-%d').date()
        image = request.files.get('image')
        if image and image.filename:
            filename = secure_filename(image.filename)
            image.save(os.path.join('static', filename))
            trek.image = filename
        trek.trek_details = request.form['trek_details']
        db.session.commit()
        return redirect('/all_treks')
    return render_template('edit_trek.html',trek=trek,staff_member=staff_members)
@app.route('/blacklist_user/<int:id>')
def blacklist_user(id):
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'admin':
        return "Access Denied"
    user = User.query.get(id)
    if not user:
        return "User Not Found"
    if user.role == 'admin':
        return "Cannot blacklist admin"
    user.blacklisted = True
    db.session.commit()
    return redirect('/admin')
@app.route('/assign_staff/<int:trek_id>', methods=['GET', 'POST'])
def assign_staff(trek_id):
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'admin':
        return "Access Denied"
    trek = Trek.query.get(trek_id)
    staff_members = User.query.filter_by(role='staff',approved=True,blacklisted=False).all()
    if request.method == 'POST':
        staff_id = request.form['staff_id']
        trek.assigned_staff_id = staff_id
        db.session.commit()
        return redirect('/admin')
    return render_template('assign_staff.html',trek=trek,staff_members=staff_members)
@app.route('/api/treks')
def api_treks():
    treks = Trek.query.all()
    data = []
    for trek in treks:
        data.append({
            'id': trek.id,
            'name': trek.name,
            'location': trek.location,
            'difficulty': trek.difficulty,
            'duration': trek.duration,
            'available_slots': trek.available_slots,
            'status': trek.status
        })
    return jsonify(data)
@app.route('/api/trek/<int:id>')
def api_trek(id):
    trek = Trek.query.get_or_404(id)
    return jsonify({
        'id': trek.id,
        'name': trek.name,
        'location': trek.location,
        'difficulty': trek.difficulty,
        'duration': trek.duration,
        'available_slots': trek.available_slots,
        'status': trek.status
    })
@app.route('/api/users')
def api_users():
    users = User.query.filter_by(role='user').all()
    data = []
    for user in users:
        data.append({
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'approved': user.approved,
            'blacklisted': user.blacklisted
        })
    return jsonify(data)
@app.route('/api/staff')
def api_staff():
    staff_members = User.query.filter_by(role='staff').all()
    data = []
    for staff in staff_members:
        data.append({
            'id': staff.id,
            'name': staff.name,
            'email': staff.email,
            'approved': staff.approved
        })
    return jsonify(data)
@app.route('/api/bookings')
def api_bookings():
    bookings = Booking.query.all()
    data = []
    for booking in bookings:
        data.append({
            'booking_id': booking.Booking_ID,
            'user_id': booking.User_ID,
            'trek_id': booking.Trek_ID,
            'status': booking.Status,
            'booking_date': str(
                booking.Booking_Date
            )
        })
    return jsonify(data)
@app.route('/api/trek/<int:trek_id>/participants')
def trek_participants(trek_id):
    bookings = Booking.query.filter_by(Trek_ID=trek_id,Status='Booked').all()
    data = []
    for booking in bookings:
        user = User.query.get(booking.User_ID)
        data.append({
            'user_id': user.id,
            'name': user.name,
            'email': user.email
        })
    return jsonify(data)
@app.route('/api/user/<int:user_id>/bookings')
def user_bookings_api(user_id):
    bookings = Booking.query.filter_by(User_ID=user_id).all()
    data = []
    for booking in bookings:
        trek = Trek.query.get(booking.Trek_ID)
        data.append({
            'trek_name': trek.name,
            'status': booking.Status,
            'booking_date': str(
                booking.Booking_Date
            )
        })




    return jsonify(data)
@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect('/login')
    user = User.query.get(session['user_id'])
    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        password = request.form['password']
        if password:
            user.password = generate_password_hash(password)
        db.session.commit()
        if user.role == 'staff':
            return redirect('/staff')
        return redirect('/user_dashboard')
    return render_template('edit_profile.html',user=user)
@app.route('/participants/<int:trek_id>')
def participants(trek_id):
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'staff':
        return "Access Denied"
    trek = Trek.query.get(trek_id)
    booked_users = []
    cancelled_users = []
    
    bookings = Booking.query.filter_by(
        Trek_ID=trek_id
    ).all()


    for booking in bookings:
        user = User.query.get(booking.User_ID)
        if booking.Status == 'Booked':
            booked_users.append({
                'user': user,
                'booking': booking
            })

        elif booking.Status == 'Cancelled':
            cancelled_users.append({
                'user': user,
                'booking': booking
            })

    return render_template(
        'participants.html',
        trek=trek,
        booked_users=booked_users,
        cancelled_users=cancelled_users
    )
@app.route('/remove_participant/<int:booking_id>')
def remove_participant(booking_id):
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'staff':
        return "Access Denied"
    booking = Booking.query.get(booking_id)
    if not booking:
        return "Booking Not Found"
    trek = Trek.query.get(booking.Trek_ID)
    booking.Status = 'Cancelled'
    trek.available_slots += 1
    db.session.commit()
    return redirect(request.referrer)
@app.route('/add_participant/<int:trek_id>', methods=['GET', 'POST'])
def add_participant(trek_id):
    if 'user_id' not in session:
        return redirect('/login')
    if session['role'] != 'staff':
        return "Access Denied"
    trek = Trek.query.get(trek_id)
    if not trek:
        return "Trek Not Found"
    if request.method == 'POST':
        user_id = request.form['user_id']
        existing_booking = Booking.query.filter_by(
            User_ID=user_id,
            Trek_ID=trek_id
        ).first()
        if existing_booking:
            return "User already booked for this trek"
        if trek.available_slots <= 0:
            return "No slots available"
        booking = Booking(
            User_ID=user_id,
            Trek_ID=trek_id,
            Booking_Date=date.today(),
            Status='Booked'
        )
        trek.available_slots -= 1
        db.session.add(booking)
        db.session.commit()
        return redirect(f'/participants/{trek_id}')
    available_users = []
    for user in User.query.filter_by(role='user').all():
        existing = Booking.query.filter_by(
            User_ID=user.id,
            Trek_ID=trek_id
        ).first()
        if not existing and not user.blacklisted:
            available_users.append(user)
    return render_template(
        'add_participant.html',
        trek=trek,
        available_users=available_users
    )
if __name__ == '__main__':
    app.run(debug=True)