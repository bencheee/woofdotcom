import pdb
import os
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
if os.path.exists("env.py"):
    import env

# Configure flask app
app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

# Connect database with the app
mongo = PyMongo(app)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/user_register", methods=["GET", "POST"])
def user_register():
    if request.method == "POST":
        # Check if username/email exist
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username")})
        existing_email = mongo.db.users.find_one(
            {"email": request.form.get("email")})
        if existing_user:
            flash("Username already in use!")
            return redirect(url_for("user_register"))
        if existing_email:
            flash("Email already in use!")
            return redirect(url_for("user_register"))
        # Check if passwords match
        password1 = request.form.get("password")
        password2 = request.form.get("password2")
        if password1 != password2:
            flash("Passwords don't match!")
            return redirect(url_for("user_register"))
        # Save user details to database
        new_user = {
            "username": request.form.get("username"),
            "password": generate_password_hash(
                request.form.get("password")),
            "email": request.form.get("email"),
            "fname": request.form.get("fname"),
            "lname": request.form.get("lname"),
            "phone": request.form.get("phone"),
            "about": request.form.get("about"),
            "liked_posts": [],
            "adoption_requests": []
        }
        mongo.db.users.insert_one(new_user)
        flash("You are now registered!")
        return redirect(url_for("index"))
    return render_template("user_register.html")


@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    if request.method == "POST":
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username")})
        password = request.form.get("password")
        # Check if username/password is valid
        if existing_user is None:
            flash("Username or password incorrect!")
            return redirect(url_for("user_login"))
        if check_password_hash(existing_user["password"], password):
            session["user"] = request.form.get("username")
            flash(f"Welcome {existing_user['username']}, you are logged in!")
            return redirect(url_for("index"))
        else:
            flash("Username or password incorrect!")
            return redirect(url_for("user_login"))
    return render_template("user_login.html")


@app.route("/user_logout")
def user_logout():
    session.pop("user")
    flash("You have been logged out sucessfully!")
    return redirect(url_for("index"))


@app.route("/user_profile", methods=["GET", "POST"])
def user_profile():
    user = mongo.db.users.find_one({"username": session["user"]})
    return render_template("user_profile.html", user=user)


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP"),
        port=int(os.environ.get("PORT")),
        debug=True)
