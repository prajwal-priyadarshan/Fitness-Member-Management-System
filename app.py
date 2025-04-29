from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from datetime import datetime
import queue
import heapq
from functools import wraps

app = Flask(__name__)
app.secret_key = 'supersecretkey'

app.config['MONGO_URI'] = "mongodb://localhost:27017/fitnesssdb"
mongo = PyMongo(app)

# Queue for scheduling equipment
equipment_schedule_queue = queue.Queue()

# Heap for most check-ins
checkin_heap = []

def login_required(role=None):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):
            if role == 'admin' and 'admin' not in session:
                flash("Admin login required", "danger")
                return redirect(url_for('admin_login'))
            elif role == 'member' and 'member_id' not in session:
                flash("Member login required", "danger")
                return redirect(url_for('member_login'))
            return fn(*args, **kwargs)
        return decorated_view
    return wrapper

class Member:
    def __init__(self, member_id):
        self.member_id = member_id

    @staticmethod
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            member = mongo.db.members.find_one({'email': email, 'password': password})
            if member:
                session['member_id'] = str(member['_id'])
                session['member_email'] = member['email']
                session['member_name'] = member.get('name', 'Member')
                return redirect(url_for('member_dashboard'))
            flash('Invalid credentials', 'danger')
        return render_template('member_login.html')

    @staticmethod
    def signup():
        if request.method == 'POST':
            name, email, phone, password, dob, gender = [request.form.get(k) for k in ['name', 'email', 'phone', 'password', 'dob', 'gender']]
            if mongo.db.members.find_one({'email': email}):
                flash("Email already registered", "danger")
            else:
                mongo.db.members.insert_one({'name': name, 'email': email, 'phone': phone, 'password': password, 'dob': dob, 'gender':gender})
                flash("Signup successful!", "success")
                return redirect(url_for('member_login'))
        return render_template('signup.html')

    def dashboard(self):
        if 'member_id' not in session:
            return redirect(url_for('member_login'))
        return render_template('member_dashboard.html', member_name=session['member_name'])

    def profile(self):
        member = mongo.db.members.find_one({'_id': ObjectId(session['member_id'])})
        return render_template('member_profile.html', member=member)

    def workout(self):
        workouts = mongo.db.workouts.find_one({'member_id': session['member_id']})
        return render_template('member_workout.html', workout_plan=workouts)
    

    def diet(self):
        diet_plan = mongo.db.diets.find_one({'member_email': session['member_email']})
        return render_template('member_diet.html', diet_plan=diet_plan)


    def payment(self):
        return render_template('member_payment.html')

    def payment_history(self):
        payments = mongo.db.payments.find({'member_id': session['member_id']})
        return render_template('member_payment_history.html', payments=payments)

    def emergency_contact(self):
        if request.method == 'POST':
            contact_name = request.form.get('contact_name')
            relation = request.form.get('relation')
            phone = request.form.get('phone')

            data = {
            'member_id': self.member_id,
            'contact_name': contact_name,
            'relation': relation,
            'phone': phone
            }

        # Upsert: update if exists, insert if not
            mongo.db.emergency_contacts.update_one(
                {'member_id': self.member_id},
                {'$set': data},
                upsert=True
            )

    # Fetch latest contact to render on GET or after POST
        contact = mongo.db.emergency_contacts.find_one({'member_id': self.member_id})
        return render_template('member_emergency_contact.html', contact=contact)

    def feedback(self):
        if request.method == 'POST':
            subject = request.form.get('subject')
            message = request.form.get('message')

            mongo.db.feedback.insert_one({
                'member_id': self.member_id,
                'subject': subject,
                'message': message,
                'timestamp': datetime.now()
            })

            flash("Feedback submitted", "success")
            return render_template('member_feedback.html')

        return render_template('member_feedback.html')
    

    def check_in(self):
        if 'member_id' not in session:
            flash("Please log in to check in.")
            return redirect(url_for('member_login'))

        member_id = session['member_id']

        if request.method == 'POST':
            # Record the check-in time
            checkin_data = {
                'member_id': member_id,
                'timestamp': datetime.now()
            }
            mongo.db.checkins.insert_one(checkin_data)

            # Update the heap for most check-ins
            heapq.heappush(checkin_heap, (-mongo.db.checkins.count_documents({'member_id': member_id}), member_id))

            flash("Check-in successful!")
            return redirect(url_for('member_dashboard'))

        return render_template('check_in.html')

    def check_out(self):
        if 'member_id' not in session:
            flash("Please log in to check out.")
            return redirect(url_for('member_login'))

        member_id = session['member_id']

        if request.method == 'POST':
            checkout_data = {
                'member_id': member_id,
                'timestamp': datetime.now()
            }
            mongo.db.checkouts.insert_one(checkout_data)
            flash("Checked out successfully!")
            return redirect(url_for('member_dashboard'))

        return render_template('check_out.html')

class Admin:
    def __init__(self):
        pass

    @staticmethod
    def login():
        if request.method == 'POST':
            email = request.form.get('email')
            password = request.form.get('password')
            admin = mongo.db.admins.find_one({'email': email, 'password': password})
            if admin:
                session['admin'] = email
                return redirect(url_for('admin_dashboard'))
            flash('Invalid credentials', 'danger')
        return render_template('admin_login.html')

    def dashboard(self):
        if 'admin' not in session:
            return redirect(url_for('admin_login'))
        return render_template('admin_dashboard.html')
    
    def emergency_contact(self):
        if 'admin' not in session:
            return redirect(url_for('admin_login'))

    # Get all emergency contacts
        contacts = list(mongo.db.emergency_contacts.find())

    # Map member_id to email
        members = {str(m['_id']): m.get('name', 'Unknown') for m in mongo.db.members.find()}

    # Add member email to each contact
        for contact in contacts:
            member_id = str(contact.get('member_id'))
            contact['member_name'] = members.get(member_id, 'Unknown')

        return render_template('admin_emergency_contact.html', contacts=contacts)


    def add_member(self):
        if request.method == 'POST':
            data = {k: request.form[k] for k in ['name', 'email', 'phone', 'password', 'dob', 'gender']}
            mongo.db.members.insert_one(data)
            flash("Member added", "success")
            return render_template('add_member.html')
        return render_template('add_member.html')

    def update_member(self):
        members = list(mongo.db.members.find())
        if request.method == 'POST':
            member_id = request.form.get('member_id')
            updated = {
                'name': request.form['name'],
                'email': request.form['email'],
                'phone': request.form['phone'],
                'password': request.form['password']
            }
            mongo.db.members.update_one({'_id': ObjectId(member_id)}, {'$set': updated})
            flash("Member updated", "success")
            return render_template('update_member.html')
        return render_template('update_member.html', members=members)

    def delete_member(self):
        members = list(mongo.db.members.find())
        if request.method == 'POST':
            member_id = request.form.get('member_id')
            if member_id:
                mongo.db.members.delete_one({'_id': ObjectId(member_id)})
                flash('Member deleted successfully!')
                return redirect(url_for('delete_member'))
            else:
                flash('Please select a member to delete.')
        return render_template('delete_member.html', members=members)

    def bubble_sort_members(self,members):
        n = len(members)
        for i in range(n):
            for j in range(0, n - i - 1):
                name1 = members[j].get('name', '').lower()
                name2 = members[j + 1].get('name', '').lower()
                if name1 > name2:
                    members[j], members[j + 1] = members[j + 1], members[j]
        return members

    def binary_search_members(self,members, keyword):
        left = 0
        right = len(members) - 1
        keyword = keyword.lower()

        while left <= right:
            mid = (left + right) // 2
            name = members[mid].get('name', '').lower()

            if name == keyword:
                return [members[mid]]  # Exact match found
            elif name < keyword:
                left = mid + 1
            else:
                right = mid - 1

        return []  # Not found

    def search_member(self):
        keyword = request.args.get('query', '').strip()
        members = []
        message = ""

        if keyword:
        # Load all members from the DB
            all_members = list(mongo.db.members.find())

        # Sort them using Bubble Sort
            sorted_members = self.bubble_sort_members(all_members)

        # Search using Binary Search
            members = self.binary_search_members(sorted_members, keyword)

        return render_template('search_member.html', members=members, query=keyword)
    def assign_workout(self):
        members = list(mongo.db.members.find())

        if request.method == 'POST':
            member_email = request.form['member_email']
            notes = request.form.get('notes', '')

        # Find member by email to get their _id
            member = mongo.db.members.find_one({'email': member_email})
            if not member:
                flash("Member not found.", "danger")
                return render_template('assign_workout.html', members=members)

            member_id = str(member['_id'])

        # Build schedule dictionary
            schedule = {}
            for day in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                workout = request.form.get(f"schedule[{day}]")
                schedule[day] = workout if workout else ""

        # Save to MongoDB using member_id
            mongo.db.workouts.update_one(
                {'member_id': member_id},
                {
                    '$set': {
                        'member_id': member_id,
                        'schedule': schedule,
                        'notes': notes,
                        'date_assigned': datetime.now()
                    }
                },
                upsert=True
            )

            flash("Workout plan assigned successfully!", "success")
            return render_template('assign_workout.html')

        return render_template('assign_workout.html', members=members)  
    
    def assign_diet(self):
        members = list(mongo.db.members.find())

        if request.method == 'POST':
            member_email = request.form['member_email']
            meals = {
                'breakfast': request.form.get('meals[breakfast]', ''),
                'lunch': request.form.get('meals[lunch]', ''),
                'dinner': request.form.get('meals[dinner]', ''),
                'snacks': request.form.get('meals[snacks]', '')
            }
            notes = request.form.get('notes', '')

            mongo.db.diets.update_one(
                {'member_email': member_email},
                    {
                    '$set': {
                        'meals': meals,
                        'notes': notes
                    }
            },
                upsert=True
            )
            flash("Diet plan assigned successfully!", "success")
            return render_template('assign_diet.html')

        return render_template('assign_diet.html', members=members)


    def add_payment(self):
        if 'admin' not in session:
            flash("Unauthorized access. Please login as admin.", "danger")
            return redirect(url_for('admin_login'))

        members = list(mongo.db.members.find())

        if request.method == 'POST':
            mongo.db.payments.insert_one({
                'member_id': request.form['member_id'],
                'amount': float(request.form['amount']),
                'payment_date': request.form['payment_date'],
                'membership_type': request.form['membership_type']
            })
            flash("Payment recorded", "success")
            return redirect(url_for('admin_dashboard'))

        return render_template('add_payment.html', members=members)

    def manage_equipment(self):
        if 'admin' not in session:
            flash("Admin login required", "danger")
            return redirect(url_for('admin_login'))

        if request.method == 'POST':
            equipment = {
                'name': request.form['name'],
                'quantity': int(request.form['quantity']),
                'condition': request.form['condition'],
                'added_date': datetime.now()
            }
            mongo.db.equipment.insert_one(equipment)
            flash("Equipment added successfully", "success")
            return redirect(url_for('manage_equipment'))

        equipment_list = list(mongo.db.equipment.find())
        return render_template('manage_equipment.html', equipment=equipment_list)

    def schedule_equipment(self):
        if 'admin' not in session:
            flash("Unauthorized access. Please login as admin.", "danger")
            return redirect(url_for('admin_login'))

        equipment_list = list(mongo.db.equipment.find())

        if request.method == 'POST':
            equipment_id = request.form.get('equipment_id')
            time_slot = request.form.get('time_slot')

            if equipment_id and time_slot:
                equipment_schedule_queue.put({
                    'equipment_id': equipment_id,
                    'time_slot': time_slot
                })
                flash("Equipment scheduled successfully!", "success")
                return redirect(url_for('schedule_equipment'))
            else:
                flash("Please select equipment and time slot", "danger")

        return render_template('schedule_equipment.html', equipment_list=equipment_list)

    def view_feedback(self):
        feedbacks = list(mongo.db.feedback.find())
    
    # Optional: ensure timestamp is datetime (safe guard)
        for fb in feedbacks:
            if 'timestamp' in fb and isinstance(fb['timestamp'], str):
                try:
                    fb['timestamp'] = datetime.fromisoformat(fb['timestamp'])
                except:
                    fb['timestamp'] = None

        return render_template('view_feedback.html', feedbacks=feedbacks)


    def view_attendance(self):
        records = list(mongo.db.attendance.find())
        return render_template('view_attendance.html', records=records)

    def attendance_report(self):
        report = list(mongo.db.attendance.find())
        return render_template('attendance_report.html', report=report)

    def admin_checkin_records(self):
        if 'admin' not in session:
            flash("Please log in as admin to view check-ins.", "danger")
            return redirect(url_for('admin_login'))

        checkins = list(mongo.db.checkins.find())
        members = {str(m['_id']): m['name'] for m in mongo.db.members.find()}
        return render_template('admin_checkin_records.html', checkins=checkins, members=members)

    def admin_checkout_records(self):
        if 'admin' not in session:
            flash("Please log in as admin to view check-outs.", "danger")
            return redirect(url_for('admin_login'))

        checkouts = list(mongo.db.checkouts.find())
        members = {str(m['_id']): m['name'] for m in mongo.db.members.find()}
        return render_template('admin_checkout_records.html', checkouts=checkouts, members=members)

    def view_payment_history(self):
        if 'admin' not in session:
            flash("Admin login required", "danger")
            return redirect(url_for('admin_login'))

        payments = list(mongo.db.payments.find())
        members = {str(m['_id']): m['name'] for m in mongo.db.members.find()}
        return render_template('view_payment_history.html', payments=payments, members=members)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    return Admin.login()

@app.route('/admin_dashboard')
def admin_dashboard():
    admin = Admin()
    return admin.dashboard()

@app.route('/admin_emergency_contact')
def admin_emergency_contact():
    admin = Admin()
    return admin.emergency_contact()

@app.route('/member_login', methods=['GET', 'POST'])
def member_login():
    return Member.login()

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    return Member.signup()

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out", "info")
    return redirect(url_for('index'))

@app.route('/member_dashboard')
@login_required(role='member')
def member_dashboard():
    member = Member(session['member_id'])
    return member.dashboard()

@app.route('/member_profile')
@login_required(role='member')
def member_profile():
    member = Member(session['member_id'])
    return member.profile()

@app.route('/member_workout', methods=['GET', 'POST'])
@login_required(role='member')
def member_workout():
    member = Member(session['member_id'])
    return member.workout()

@app.route('/member_diet')
@login_required(role='member')
def member_diet():
    member = Member(session['member_id'])
    return member.diet()

@app.route('/member_payment')
@login_required(role='member')
def member_payment():
    member = Member(session['member_id'])
    return member.payment()

@app.route('/member_payment_history')
@login_required(role='member')
def member_payment_history():
    member = Member(session['member_id'])
    return member.payment_history()

@app.route('/member_emergency_contact', methods=['GET', 'POST'])
@login_required(role='member')
def member_emergency_contact():
    member = Member(session['member_id'])
    return member.emergency_contact()

@app.route('/member_feedback', methods=['GET', 'POST'])
@login_required(role='member')
def member_feedback():
    member = Member(session['member_id'])
    return member.feedback()

@app.route('/add_member', methods=['GET', 'POST'])
@login_required(role='admin')
def add_member():
    admin = Admin()
    return admin.add_member()

@app.route('/update_member', methods=['GET', 'POST'])
@login_required(role='admin')
def update_member():
    admin = Admin()
    return admin.update_member()

@app.route('/delete_member', methods=['GET', 'POST'])
@login_required(role='admin')
def delete_member():
    admin = Admin()
    return admin.delete_member()

@app.route('/search_member', methods=['GET', 'POST'])
@login_required(role='admin')
def search_member():
    admin = Admin()
    return admin.search_member()

@app.route('/assign_workout', methods=['GET', 'POST'])
@login_required(role='admin')
@login_required(role='admin')
def assign_workout():
    admin = Admin()
    return admin.assign_workout()

@app.route('/assign_diet', methods=['GET', 'POST'])
@login_required(role='admin')
def assign_diet():
    admin = Admin()
    return admin.assign_diet()

@app.route('/add_payment', methods=['GET', 'POST'])
@login_required(role='admin')
def add_payment():
    admin = Admin()
    return admin.add_payment()

@app.route('/manage_equipment', methods=['GET', 'POST'])
@login_required(role='admin')
def manage_equipment():
    admin = Admin()
    return admin.manage_equipment()

@app.route('/schedule_equipment', methods=['GET', 'POST'])
@login_required(role='admin')
def schedule_equipment():
    admin = Admin()
    return admin.schedule_equipment()

@app.route('/view_feedback')
@login_required(role='admin')
def view_feedback():
    admin = Admin()
    return admin.view_feedback()

@app.route('/view_attendance')
@login_required(role='admin')
def view_attendance():
    admin = Admin()
    return admin.view_attendance()

@app.route('/attendance_report')
@login_required(role='admin')
def attendance_report():
    admin = Admin()
    return admin.attendance_report()

@app.errorhandler(KeyError)
def handle_key_error(e):
    flash("Session expired or invalid access. Please log in again.", "danger")
    return redirect(url_for('member_login'))

@app.route('/check-in', methods=['GET', 'POST'])
def check_in():
    member = Member(session['member_id'])
    return member.check_in()

@app.route('/check-out', methods=['GET', 'POST'], endpoint='check_out')
def member_check_out():
    member = Member(session['member_id'])
    return member.check_out()

@app.route('/admin_checkin_records')
@login_required(role='admin')
def admin_checkin_records():
    admin = Admin()
    return admin.admin_checkin_records()

@app.route('/admin_checkout_records')
@login_required(role='admin')
def admin_checkout_records():
    admin = Admin()
    return admin.admin_checkout_records()

@app.route('/view_payment_history')
@login_required(role='admin')
def view_payment_history():
    admin = Admin()
    return admin.view_payment_history()

if __name__ == '__main__':
    app.run(debug=True)
