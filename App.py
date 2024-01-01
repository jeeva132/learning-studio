from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)
app.secret_key = "Secret Key"

# Update the PostgreSQL connection URL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://learn_mkis_user:iVhn19zxcPkxI8FUhFaqc5GKNdPvS4YA@dpg-cm7u326n7f5s73ebs30g-a.oregon-postgres.render.com/learn_mkis'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

class Subscription(db.Model):
    __tablename__ = 'subscriptions'

    subscription_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'))
    subscription_date = db.Column(db.DateTime, default=datetime.utcnow)

    # Define relationships with User and Course models
    user = db.relationship('User', backref=db.backref('subscriptions', lazy='dynamic'))
    course = db.relationship('Course', backref=db.backref('subscribers', lazy='dynamic'))

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255))
    email = db.Column(db.String(255))
    password = db.Column(db.String(255))
    user_type = db.Column(db.String(255))
    phone_number = db.Column(db.String(255))

class Pathway(db.Model):
    __tablename__ = 'pathways'

    pathway_id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    link = db.Column(db.String(255))

class Course(db.Model):
    __tablename__ = 'courses'

    course_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    instructor_id = db.Column(db.Integer)
    video_link = db.Column(db.String(255))



def check_login():
    user_id = session.get('user_id')
    if user_id is None:
        return False
    user = User.query.get(user_id)
    if user is None:
        return False
    return True


@app.route('/coursepage.html')
def coursepage():
    if check_login():
        user_id = session['user_id']
        user = User.query.get(user_id)
        courses = Course.query.limit(4).all()
        pathways = Pathway.query.limit(4).all()
        python_courses = Course.query.filter(Course.title.like('Python%')).all()
        return render_template('coursepage.html', user=user, courses=courses, pathways=pathways, python_courses=python_courses)
    return redirect(url_for('login_page'))

@app.route('/courses.html')
def courses():
    if check_login():
        # Retrieve the user's ID from the session
        user_id = session['user_id']
        
        # Retrieve the courses subscribed by the user
        user_courses = db.session.query(Course).join(Subscription, Course.course_id == Subscription.course_id).filter(Subscription.user_id == user_id).all()

        return render_template('courses.html', courses=user_courses)
    return redirect(url_for('login_page'))


@app.route('/pathways.html')
def pathways():
    pathways = Pathway.query.all()
    python_courses = Course.query.filter(Course.title.like('Python%')).limit(4).all()
    return render_template('pathways.html', pathways=pathways)

@app.route('/coursepage.html')
def course_page():
    courses = Course.query.limit(4).all()
    pathways = Pathway.query.limit(4).all()
    python_courses = Course.query.filter(Course.title.like('Python%')).limit(4).all()
    return render_template('coursepage.html', courses=courses, pathways=pathways, python_courses=python_courses)

@app.route('/')
def index_page():
    return render_template('index.html')

@app.route('/search', methods=['GET', 'POST'])
def search():
    if request.method == 'POST':
        search_query = request.form.get('search_query')
        search_results = Course.query.filter(Course.title.ilike(f'%{search_query}%')).all()
        return render_template('search.html', search_results=search_results)
    return render_template('search_form.html')

@app.route('/user.html')
def user_page():
    if check_login():
        user_id = session['user_id']
        user = User.query.get(user_id)
        return render_template('user.html', user=user)
    return redirect(url_for('login_page'))


@app.route('/login.html', methods=['GET', 'POST'])
def login_page():
    return render_template('login.html')

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         email = request.form['email']
#         password = request.form['password']
#         user = User.query.filter_by(email=email, password=password).first()
#         if user:
#             session['user_id'] = user.user_id  # Store user_id in the session
#             return redirect(url_for('coursepage'))
#         else:
#             flash('Invalid email or password. Please try again.', 'error')
#     return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email, password=password).first()
        if user:
            session['user_id'] = user.user_id  # Store user_id in the session
            if user.user_type == "instructor":
                return redirect(url_for('instructor'))
            else:
                return redirect(url_for('coursepage'))
        else:
            flash('Invalid email or password. Please try again.', 'error')
    return render_template('login.html')


    

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        phone_number = request.form['phone_number']
        password = request.form['password']
        user_type = request.form['user_type']
        new_user = User(username=name, email=email, phone_number=phone_number, user_type=user_type, password=password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('registration_success'))
    return render_template('registration_form.html')

@app.route('/registration_success')
def registration_success():
    return 'Registration Successful'

# ... (Previous Flask code)

@app.route('/subscribe/<int:course_id>', methods=['POST'])
def subscribe(course_id):
    if not check_login():
        flash('Please log in to subscribe.', 'error')
        return redirect(url_for('login_page'))

    # Retrieve the user ID from the session
    user_id = session['user_id']

    # Check if the user is already subscribed to the course
    subscription = Subscription.query.filter_by(user_id=user_id, course_id=course_id).first()
    if subscription:
        flash('You are already subscribed to this course.', 'info')
    else:
        # Create a new subscription entry in the database
        new_subscription = Subscription(user_id=user_id, course_id=course_id, subscription_date=datetime.now())
        db.session.add(new_subscription)
        db.session.commit()
        flash('You have successfully subscribed to this course!', 'success')

    return redirect(url_for('coursepage'))

# # ... (Other Flask routes)

# if __name__ == "__main__":
#     app.run(debug=True)

@app.route('/instructor_page')
def instructor_page():
    if check_login() and session.get('user_id'):
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user.user_type == "instructor":
            # Implement instructor-specific logic here
            return render_template('instructor.html', user=user)
        else:
            return redirect(url_for('coursepage'))
    return redirect(url_for('login_page'))

@app.route('/add.html')
def user():
    return render_template('add.html')

@app.route('/student.html')
def student():
    if check_login() and session.get('user_id'):
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user.user_type == "instructor":
            # Retrieve the subscription data for the instructor's course
            instructor_courses = Course.query.filter_by(instructor_id=user.user_id).all()
            subscriptions = Subscription.query.filter(Subscription.course_id.in_([course.course_id for course in instructor_courses])).all()
            return render_template('student.html', user=user, subscriptions=subscriptions)
        else:
            return redirect(url_for('coursepage'))
    return redirect(url_for('login_page'))

@app.route('/instructor')

def instructor():
    if check_login() and session.get('user_id'):
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user.user_type == "instructor":
            # Retrieve the courses uploaded by the instructor
            instructor_courses = Course.query.filter_by(instructor_id=user.user_id).all()
            return render_template('instructor.html', user=user, instructor_courses=instructor_courses)
        else:
            return redirect(url_for('coursepage'))
    return redirect(url_for('login_page'))

@app.route('/instructor.html')
def instructor_courses():
    if check_login() and session.get('user_id'):
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user.user_type == "instructor":
            # Retrieve the courses uploaded by the instructor
            instructor_courses = Course.query.filter_by(instructor_id=user.user_id).all()
            return render_template('instructor.html', user=user, instructor_courses=instructor_courses)
        else:
            return redirect(url_for('coursepage'))
    return redirect(url_for('login_page'))

@app.route('/add_course', methods=['POST'])
def add_course():
    if check_login() and session.get('user_id'):
        user_id = session['user_id']
        user = User.query.get(user_id)
        if user.user_type == "instructor":
            # Get the form data from the submitted form
            title = request.form['title']
            description = request.form['description']
            video_link = request.form['video_link']

            # Create a new course with the instructor's user_id
            new_course = Course(title=title, description=description, video_link=video_link, instructor_id=user.user_id)
            db.session.add(new_course)
            db.session.commit()

            return redirect(url_for('instructor'))
        else:
            return redirect(url_for('coursepage'))
    return redirect(url_for('login_page'))
@app.route('/delete_course/<int:course_id>', methods=['POST'])
def delete_course(course_id):
    course = Course.query.get(course_id)
    
    if course:
        # Delete the course from the database
        db.session.delete(course)
        db.session.commit()
        flash('Course deleted successfully', 'success')
    else:
        flash('Course not found', 'error')

    return redirect(url_for('instructor_courses'))



if __name__ == "__main__":
    app.run(debug=True)
