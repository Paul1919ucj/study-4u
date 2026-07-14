from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, flash
from flask_sqlalchemy import SQLAlchemy
import os
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.secret_key = "study4u_secret_key"
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///study4u.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["UPLOAD_FOLDER"]="uploads"

db = SQLAlchemy(app)
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(250),nullable=False)

class Note(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class CalendarEvent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    event_date = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    task = db.Column(db.String(200), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class CourseFile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(200), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

@app.route("/", methods=["POST", "GET"])
def home():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        print("Login username:", username)
        print("Login password:", password)

        user = User.query.filter_by(username=username, password=password).first()

        if user:
            session["username"] = user.username
            return redirect("/dashboard")
        else:
            print("Invalid username or password")
        
    return render_template("index.html")
     
@app.route("/register", methods=['GET','POST'])
def register():

    if request.method =="POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        new_user = User(username=username, email=email, password=password)

        db.session.add(new_user)
        db.session.commit()

        print("User saved successfully")

    return render_template("register.html")

@app.route("/dashboard")
def dashboard():
    username = session.get("username")
    
    if not username:
        return redirect("/")
    
    user = User.query.filter_by(username=username).first()

    notes_count = Note.query.filter_by(user_id=user.id).count()
    tasks_count = Task.query.filter_by(user_id=user.id).count()
    events_count = CalendarEvent.query.filter_by(user_id=user.id).count()
    courses_count = CourseFile.query.filter_by(user_id=user.id).count()

    latest_notes = Note.query.filter_by(user_id=user.id).limit(4).all()
    latest_tasks = Task.query.filter_by(user_id=user.id).limit(5).all()
    latest_events = CalendarEvent.query.filter_by(user_id=user.id).limit(3).all()
    latest_files = CourseFile.query.filter_by(user_id=user.id).limit(4).all()


    latest_reviews= Review.query.order_by(Review.id.desc()).limit(3).all()
    users = User.query.all()

    today_date = datetime.now().strftime("%B %d %Y")



    return render_template(
        "dashboard.html", 
        username=username,
        
        today_date=today_date, 
        notes_count=notes_count, 
        tasks_count=tasks_count, 
        events_count=events_count, 
        courses_count=courses_count, 
        latest_notes=latest_notes,
        latest_tasks=latest_tasks,
        latest_events=latest_events,
        latest_files=latest_files,
        latest_reviews=latest_reviews,
        users=users

        
    )

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('home'))

@app.route("/notes", methods=['GET', 'POST'])
def notes():
    
    username = session.get("username")
    user = User.query.filter_by(username=username).first()
        
    if request.method == "POST":

        print('Notes from submitted')
        title = request.form.get("title")
        content = request.form.get("content")

        print('Title:', title)
        print('Content', content)


        new_note = Note(

            title=title,
            content=content,
            user_id=user.id

        )

        db.session.add(new_note)
        db.session.commit()

        print("Note saved successfully")

    notes = Note.query.filter_by(user_id=user.id).all()

    return render_template("notes.html", notes=notes)

@app.route("/delete_note/<int:note_id>")
def delete_note(note_id):

    note = Note.query.get(note_id)

    db.session.delete(note)
    db.session.commit()
    
    return redirect(url_for("notes"))

@app.route("/edit_note/<int:note_id>", methods=['GET', 'POST'])
def edit_note(note_id):

    note = Note.query.get_or_404(note_id)

    if request.method == "POST":

        note.title = request.form.get("title")
        note.content = request.form.get("content")

        db.session.commit()

        return redirect(url_for("notes"))
    
    return render_template('edit_note.html', note=note)

@app.route("/todo", methods=['GET', 'POST'])
def todo():

    username = session.get("username")
    user = User.query.filter_by(username=username).first()

    if request.method == 'POST':

        task = request.form.get('task')

        new_task = Task(
            task=task,
            user_id=user.id
        )

        db.session.add(new_task)
        db.session.commit()

    tasks = Task.query.filter_by(user_id=user.id).all()

    return render_template("todo.html", tasks=tasks)

@app.route("/delete_test/<int:task_id>")
def delete_task(task_id):

    task = Task.query.get_or_404(task_id)

    db.session.delete(task)
    db.session.commit()

    return redirect(url_for("todo"))

@app.route("/edit_task/<int:task_id>", methods=['GET', 'POST'])
def edit_task(task_id):
    
    task = Task.query.get_or_404(task_id)

    if request.method == 'POST':
        task.task = request.form.get('task')

        db.session.commit()

        return redirect(url_for("todo"))
    
    return render_template("edit_task.html", task=task)
        
@app.route("/calendar", methods=['GET', 'POST'])
def calendar():

    username = session.get("username")
    user = User.query.filter_by(username=username).first()

    if request.method == 'POST':

        title = request.form.get("title")
        description = request.form.get("description")
        event_date = request.form.get("event_date")

        new_event = CalendarEvent(

            title=title,
            description=description,
            event_date=event_date,
            user_id=user.id
        )

        db.session.add(new_event)
        db.session.commit()

    events = CalendarEvent.query.filter_by(user_id=user.id).all()

    today = datetime.now().strftime("%Y-%m-%d")

    return render_template("calendar.html", events=events, today=today)

@app.route("/delete_event/<int:event_id>")
def delete_event(event_id):

    event = CalendarEvent.query.get_or_404(event_id)

    db.session.delete(event)
    db.session.commit()

    return redirect(url_for("calendar"))

@app.route("/edit_event/<int:event_id>", methods=['GET', 'POST'])
def edit_event(event_id):

    event = CalendarEvent.query.get_or_404(event_id)

    if request.method == "POST":

        event.title = request.form.get("title")
        event.description = request.form.get("description")
        event.event_date =request.form.get("event_date")

        db.session.commit()

        return redirect(url_for("calendar"))
    
    return render_template("edit_event.html", event=event)

@app.route("/courses", methods=['GET', 'POST'])
def courses():

    username = session.get("username")
    user = User.query.filter_by(username=username).first()

    if request.method == 'POST':
    
        file = request.files.get("file")

        if file:

            filename = secure_filename(file.filename)

            existing_file = CourseFile.query.filter_by(

                filename=filename,
                user_id=user.id
            ).first()

            if existing_file:
                flash("This file already exist!", "error")
                return redirect(url_for("courses"))
            
            print(filename)
            print(app.config["UPLOAD_FOLDER"])

            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            print("File saved!")

            new_file = CourseFile(

                filename=filename,
                user_id=user.id

            )

            db.session.add(new_file)
            db.session.commit()

    files = CourseFile.query.filter_by(user_id=user.id).all()

    return render_template("courses.html", files=files)

@app.route("/download/<filename>")
def download(filename):

    return send_from_directory(
        app.config["UPLOAD_FOLDER"],
        filename,
        download_name=filename
    )

@app.route("/delete_file/<int:file_id>")
def delete_file(file_id):

    file = CourseFile.query.get_or_404(file_id)

    filepath = os.path.join(

        app.config["UPLOAD_FOLDER"],
        file.filename
    )

    if os.path.exists(filepath):
        os.remove(filepath)

    db.session.delete(file)
    db.session.commit()

    return redirect(url_for("courses"))

@app.route("/settings", methods=['GET', 'POST'])
def settings():
    username = session.get("username")

    if not username:
        session.clear()
        flash("Session expired. Please log in again", "error")
        return redirect(url_for("home"))
    
    user = User.query.filter_by(username=username).first()

    if not user:
        session.clear()
        flash("Session expired. PLease log in again.", "error")
        return redirect(url_for("home"))

    if request.method == 'POST':
    
        new_username = request.form.get("username")
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        confirm_password = request.form.get("confirm_password")

        if new_username:
            existing_user = User.query.filter_by(username=new_username).first()

            if existing_user and existing_user.id != user.id:
                flash("Username already exists!", "error")
                return redirect(url_for("settings"))
            
            user.username = new_username
            session["username"] = new_username

        if current_password or new_password or confirm_password:
            if current_password != user.password:
                flash("Current password is incorrect!", "error")
                return redirect(url_for("settings"))
            
            if new_password != confirm_password:
                flash("New passwords do not match!", "error")
                return redirect(url_for("settings"))
            
            if not new_password:
                flash("New password cannot be empty!", "error")
                return redirect(url_for("settings"))
            
            user.password = new_password

        db.session.commit()
        flash("Settings updatet successfully!", "success")
        return redirect(url_for("settings"))

    return render_template("settings.html", user=user)

@app.route("/rate_us", methods=['GET', 'POST'])
def rate_us():
    username = session.get("username")

    if not username:
        return redirect(url_for("home"))
    
    user = User.query.filter_by(username=username).first()

    if not user:
        session.clear()
        return redirect(url_for("home"))
    
    if request.method == 'POST':
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        if not rating:
            flash("Please select a rating!", "error")
            return redirect(url_for("rate_us"))
        
        new_review = Review(

            rating=int(rating),
            comment=comment,
            user_id=user.id

        )

        db.session.add(new_review)
        db.session.commit()

        flash("Review submitted successfully!", "success")
        return redirect(url_for("rate_us"))
    
    reviews = Review.query.all()

    return render_template("rate_us.html", reviews=reviews, users=User.query.all())

with app.app_context():
    db.create_all()
    
if __name__=="__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)