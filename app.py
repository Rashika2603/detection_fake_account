from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# SQLite database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
db = SQLAlchemy(app)

# User model for the database
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), nullable=False)

# Report model for the database
class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reporter = db.Column(db.String(80), nullable=False)
    reported_username = db.Column(db.String(80), nullable=False)
    reason = db.Column(db.String(500), nullable=False)
    status = db.Column(db.String(20), default='pending')

# Create database tables (run once)
with app.app_context():
    db.create_all()

# Sample data to populate the database
sample_data = [
    {'username': 'admin', 'password': 'admin_password', 'role': 'admin'},
    {'username': 'user1', 'password': 'user1_password', 'role': 'user'},
    {'username': 'user2', 'password': 'user2_password', 'role': 'user'},
]

@app.before_request
def before_first_request():
    if not User.query.filter_by(username='admin').first():
        for data in sample_data:
            new_user = User(**data)
            db.session.add(new_user)
            db.session.commit()


@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def login():
    username = request.form.get('username')
    password = request.form.get('password')

    user = User.query.filter_by(username=username).first()

    if user and user.password == password:
        session['user'] = username
        if user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    else:
        return "Invalid credentials. <a href='/'>Try again</a>"

@app.route('/admin_dashboard')
def admin_dashboard():
    if 'user' in session:
        user = User.query.filter_by(username=session['user']).first()
        if user and user.role == 'admin':
            return render_template('admin_dashboard.html', username=session['user'])
    return "Unauthorized access. Please log in as an admin. <a href='/'>Login</a>"

@app.route('/user_dashboard')
def user_dashboard():
    if 'user' in session:
        user = User.query.filter_by(username=session['user']).first()
        if user and user.role == 'user':
            return render_template('user_dashboard.html', username=session['user'])
    return "Unauthorized access. Please log in as a user. <a href='/'>Login</a>"

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/report', methods=['GET', 'POST'])
def report_user():
    if request.method == 'POST':
        if 'user' in session:
            reporter = session['user']
            reported_username = request.form.get('reported_username')
            reason = request.form.get('reason')

            # Check if the reported user exists
            reported_user = User.query.filter_by(username=reported_username).first()

            if not reported_user:
                return "Reported user does not exist. <a href='/report'>Try again</a>"

            # Create a report
            report = Report(reporter=reporter, reported_username=reported_username, reason=reason)
            db.session.add(report)
            db.session.commit()

            return "Report submitted successfully. <a href='/user_dashboard'>Back to Dashboard</a>"

    return render_template('report.html')

@app.route('/admin_reports')
def admin_reports():
    if 'user' in session:
        user = User.query.filter_by(username=session['user']).first()
        if user and user.role == 'admin':
            reports = Report.query.filter_by(status='pending').all()
            return render_template('admin_reports.html', reports=reports)
    return "Unauthorized access. Please log in as an admin. <a href='/'>Login</a>"

@app.route('/admin/action/<int:report_id>', methods=['GET', 'POST'])
def admin_action(report_id):
    if 'user' in session:
        user = User.query.filter_by(username=session['user']).first()
        if user and user.role == 'admin':
            report = Report.query.get(report_id)

            if request.method == 'POST':
                action = request.form.get('action')
                if action == 'approve':
                    report.status = 'approved'
                    # Take appropriate action here, e.g., banning the reported user.
                elif action == 'reject':
                    report.status = 'rejected'
                db.session.commit()
                return redirect(url_for('admin_reports'))

            return render_template('admin_action.html', report=report)
    return "Unauthorized access. Please log in as an admin. <a href='/'>Login</a>"

# ... (previous code)

# # Initialize the database
# def init_db():
#     with app.app_context():
#         db.create_all()
#         # Add an admin user
#         admin = User(username='admin_user', password='admin_password', role='admin')
#         # Add a regular user
#         regular_user = User(username='regular_user', password='user_password', role='user')

#         # Add users to the database
#         try:
#             db.session.add(admin)
#             db.session.add(regular_user) 
#             db.session.commit()
#         except IntegrityError:
#             db.session.rollback()



if __name__ == '__main__':
    # init_db()
    app.run(debug=True)

