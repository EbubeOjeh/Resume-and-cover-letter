from flask import Flask, render_template, request, redirect, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from openai import OpenAI
import os
import re
import pdfplumber
import docx

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -------------------------
# DATABASE
# -------------------------

basedir = os.path.abspath(os.path.dirname(__file__))

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + \
    os.path.join(basedir, "database.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# -------------------------
# LOGIN MANAGER
# -------------------------

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# -------------------------
# OPENAI CLIENT
# -------------------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------
# DATABASE MODELS
# -------------------------


class User(UserMixin, db.Model):

    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(100), unique=True)

    password = db.Column(db.String(200))


class ResumeAnalysis(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer)

    score = db.Column(db.Integer)

    result = db.Column(db.Text)


@login_manager.user_loader
def load_user(user_id):

    return User.query.get(int(user_id))


# -------------------------
# ROUTES
# -------------------------

@app.route("/")
def home():

    return render_template("index.html")


# REGISTER

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        existing = User.query.filter_by(username=username).first()

        if existing:
            return "Username already exists"

        hashed = generate_password_hash(password)

        user = User(username=username, password=hashed)

        db.session.add(user)
        db.session.commit()

        return redirect("/login")

    return render_template("register.html")


# LOGIN

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()

        if not user:
            return "Account not found"

        if check_password_hash(user.password, password):

            login_user(user)

            return redirect("/dashboard")

        else:
            return "Incorrect password"

    return render_template("login.html")


# LOGOUT

@app.route("/logout")
@login_required
def logout():

    logout_user()

    return redirect("/")


# -------------------------
# DASHBOARD
# -------------------------

@app.route("/dashboard", methods=["GET", "POST"])
@login_required
def dashboard():

    result = None
    score = 0
    cover_letter = ""

    if request.method == "POST":

        resume_text = request.form.get("resume")
        resume_file = request.files.get("resume_file")

        # Handle uploaded files
        if resume_file and resume_file.filename != "":

            if resume_file.filename.endswith(".pdf"):

                with pdfplumber.open(resume_file) as pdf:

                    resume_text = ""

                    for page in pdf.pages:
                        resume_text += page.extract_text() or ""

            elif resume_file.filename.endswith(".docx"):

                doc = docx.Document(resume_file)

                resume_text = "\n".join([p.text for p in doc.paragraphs])

            else:

                resume_text = resume_file.read().decode("utf-8")

        job = request.form["job"]

        prompt = f"""
Analyze this resume against the job description.

Return in this format:

ATS_SCORE: number out of 100

MISSING_KEYWORDS:
...

SUGGESTIONS:
...

COVER_LETTER:
...

Resume:
{resume_text}

Job Description:
{job}
"""

        # NEW OPENAI API CALL

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        result = response.choices[0].message.content

        score_match = re.search(r'ATS_SCORE:\s*(\d+)', result)

        if score_match:
            score = int(score_match.group(1))

        cover_letter = result.split("COVER_LETTER:")[-1]

        save = ResumeAnalysis(
            user_id=current_user.id,
            score=score,
            result=result
        )

        db.session.add(save)
        db.session.commit()

    history = ResumeAnalysis.query.filter_by(user_id=current_user.id).all()

    return render_template(
        "dashboard.html",
        result=result,
        score=score,
        cover_letter=cover_letter,
        history=history
    )


# -------------------------
# COVER LETTER PDF
# -------------------------

@app.route("/download_pdf", methods=["POST"])
@login_required
def download_pdf():

    cover_letter = request.form["cover_letter"]

    styles = getSampleStyleSheet()

    pdf = SimpleDocTemplate("cover_letter.pdf")

    story = []

    for line in cover_letter.split("\n"):

        story.append(Paragraph(line, styles["Normal"]))
        story.append(Spacer(1, 10))

    pdf.build(story)

    return send_file("cover_letter.pdf", as_attachment=True)


# -------------------------

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True)
