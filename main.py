from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"


# ----------------------------------------
# DATABASE INITIALIZATION
# ----------------------------------------
def init_db():
    conn = sqlite3.connect("skincare.db")
    c = conn.cursor()

    # USERS TABLE
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            profile TEXT DEFAULT ''
        )
    """)

    # TIPS TABLE
    c.execute("""
        CREATE TABLE IF NOT EXISTS tips (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            content TEXT,
            concern TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # PLANS TABLE
    c.execute("""
        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


init_db()


# ----------------------------------------
# HELPER – GET DB CONNECTION
# ----------------------------------------
def get_db():
    # use row factory if you want dict-like results (not required here)
    conn = sqlite3.connect("skincare.db")
    return conn


# ----------------------------------------
# ROUTES
# ----------------------------------------
@app.route("/")
def welcome():
    return render_template("welcome.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        password_hash = generate_password_hash(password)

        conn = get_db()
        c = conn.cursor()

        try:
            c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                      (username, password_hash))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            conn.close()
            return "Username already taken."

    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        c = conn.cursor()

        c.execute("SELECT id, password_hash FROM users WHERE username=?", (username,))
        user = c.fetchone()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["username"] = username
            return redirect(url_for("home"))
        else:
            return "Invalid username or password"

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("welcome"))


# ----------------------------------------
# HOME (global feed + quick post)
# ----------------------------------------
@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    c = conn.cursor()
    # Fetch all tips from all users, newest first, include username via join
    c.execute("""
        SELECT tips.id, tips.title, tips.content, tips.concern, tips.created_at, users.username
        FROM tips
        JOIN users ON tips.user_id = users.id
        ORDER BY tips.created_at DESC
    """)
    feed = c.fetchall()
    conn.close()

    return render_template("home.html", feed=feed)


# Quick post endpoint used by the Home page "Create Tip" box
@app.route("/post_tip", methods=["POST"])
def post_tip():
    if "user_id" not in session:
        return redirect(url_for("login"))

    title = request.form.get("title", "").strip()
    content = request.form.get("content", "").strip()
    concern = request.form.get("concern") or request.form.get("concern_text") or ""

    if not title and not content:
        # no content provided — simply redirect back
        return redirect(url_for("home"))

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        INSERT INTO tips (user_id, title, content, concern, created_at)
        VALUES (?, ?, ?, ?, ?)
    """, (session["user_id"], title, content, concern, datetime.utcnow()))
    conn.commit()
    conn.close()

    return redirect(url_for("home"))


# ----------------------------------------
# TIPS SYSTEM (view/add/edit/delete) — unchanged except add_tips stays
# ----------------------------------------
@app.route("/tips")
def tips_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, title, content, concern, created_at
        FROM tips
        WHERE user_id=?
        ORDER BY created_at DESC
    """, (session["user_id"],))
    tips = c.fetchall()
    conn.close()

    return render_template("tips.html", tips=tips)


@app.route("/add_tips", methods=["GET", "POST"])
def add_tips():
    if "user_id" not in session:
        return redirect(url_for("login"))

    concerns = ["acne", "dry skin", "oily skin", "pores", "wrinkles"]

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        concern = request.form.get("concern") or request.form.get("concern_text")

        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO tips (user_id, title, content, concern)
            VALUES (?, ?, ?, ?)
        """, (session["user_id"], title, content, concern))
        conn.commit()
        conn.close()

        return redirect(url_for("tips_page"))

    return render_template("add_tips.html", concerns=concerns)


@app.route("/edit_tips/<int:tip_id>", methods=["GET", "POST"])
def edit_tips(tip_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    concerns = ["acne", "dry skin", "oily skin", "pores", "wrinkles"]

    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        content = request.form["content"]
        concern = request.form.get("concern") or request.form.get("concern_text")

        c.execute("""
            UPDATE tips SET title=?, content=?, concern=? WHERE id=?
        """, (title, content, concern, tip_id))

        conn.commit()
        conn.close()
        return redirect(url_for("tips_page"))

    c.execute("SELECT title, content, concern FROM tips WHERE id=?", (tip_id,))
    tip = c.fetchone()
    conn.close()

    return render_template("edit_tips.html", tip=tip, concerns=concerns, tip_id=tip_id)


@app.route("/delete_tips/<int:tip_id>")
def delete_tips(tip_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM tips WHERE id=?", (tip_id,))
    conn.commit()
    conn.close()
    return redirect(url_for("tips_page"))


# ----------------------------------------
# PLANS SYSTEM (unchanged)
# ----------------------------------------
@app.route("/plans")
def plans_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    c = conn.cursor()
    c.execute("""
        SELECT id, title, description, created_at
        FROM plans
        WHERE user_id=?
        ORDER BY created_at DESC
    """, (session["user_id"],))
    plans = c.fetchall()
    conn.close()

    return render_template("plans.html", plans=plans)


@app.route("/add_plan", methods=["GET", "POST"])
def add_plan_page():
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]

        conn = get_db()
        c = conn.cursor()
        c.execute("""
            INSERT INTO plans (user_id, title, description)
            VALUES (?, ?, ?)
        """, (session["user_id"], title, description))
        conn.commit()
        conn.close()

        return redirect(url_for("plans_page"))

    return render_template("add_plan.html")


@app.route("/edit_plan/<int:plan_id>", methods=["GET", "POST"])
def edit_plan(plan_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    c = conn.cursor()

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]

        c.execute("""
            UPDATE plans SET title=?, description=? WHERE id=?
        """, (title, description, plan_id))
        conn.commit()
        conn.close()

        return redirect(url_for("plans_page"))

    c.execute("SELECT title, description FROM plans WHERE id=?", (plan_id,))
    plan = c.fetchone()
    conn.close()

    return render_template("edit_plan.html", plan=plan, plan_id=plan_id)


@app.route("/delete_plan/<int:plan_id>")
def delete_plan(plan_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("DELETE FROM plans WHERE id=?", (plan_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("plans_page"))


@app.route("/view_plan/<int:plan_id>")
def view_plan(plan_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM plans WHERE id=?", (plan_id,))
    plan = c.fetchone()
    conn.close()

    return render_template("view_plan.html", plan=plan)


# ----------------------------------------
# PROFILE PAGE
# ----------------------------------------
@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("profile.html")


# ----------------------------------------
# RUN FLASK
# ----------------------------------------
if __name__ == "__main__":
    app.run(debug=True)
