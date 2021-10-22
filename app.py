import pdb
import os
import random
from io import BytesIO
from PIL import Image
from datetime import datetime
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import boto3
if os.path.exists("env.py"):
    import env

# Configure flask app
app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

# Configure AWS client
s3 = boto3.client(
    's3',
    aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
)
BUCKET_NAME = os.environ.get("S3_BUCKET_NAME")
S3_RESOURCE = boto3.resource('s3')
MY_BUCKET = S3_RESOURCE.Bucket(BUCKET_NAME)
IMG_FOLDER = os.environ.get("IMG_FOLDER")

# Connect database with the app
mongo = PyMongo(app)


def permission_denied():
    flash("Permission denied.")
    return redirect(url_for("index"))


def generate_photo(item, collection):
    image = Image.open(request.files['photo'])
    image.thumbnail((768, 432))
    img_id = round(random.random() * 1000000)
    img_filename = f"{item}_img_{img_id}.webp"
    while True:
        image_exists = False
        for i in collection:
            if i["img_id"] == img_id:
                image_exists = True
        if image_exists:
            img_id = round(random.random() * 1000000)
            img_filename = f"{item}_img_{img_id}.webp"
        else:
            buffer = BytesIO()
            image.save(buffer, 'webp')
            buffer.seek(0)
            MY_BUCKET.Object(img_filename).put(
                Body=buffer, ContentType='image/webp')
            break
    img_path = f"{IMG_FOLDER}{img_filename}"
    return img_id, img_filename, img_path


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/alert/<response>")
def alert(response):
    response_received = response
    return render_template(
        "alert.html", response=response_received)


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
    # Form to change the user password
    if request.method == "POST" and "password" in request.form:
        # Check current password
        if check_password_hash(user["password"], request.form.get("password")):
            # Check if new passwords match
            if request.form.get("password2") == request.form.get("password3"):
                new_password = generate_password_hash(
                    request.form.get("password2"))
                # Update password in database
                mongo.db.users.update_one(
                    {"username": session["user"]},
                    {"$set": {"password": new_password}})
                flash("Password changed!")
            else:
                flash("New passwords don't match!")
        else:
            flash("Current password wrong!")
    # Form to edit user details
    elif request.method == "POST" and "fname" in request.form:
        fname = request.form.get("fname")
        lname = request.form.get("lname")
        phone = request.form.get("phone")
        about = request.form.get("about")
        mongo.db.users.update_one(
            {"username": session["user"]},
            {"$set": {"fname": fname, "lname": lname,
                      "phone": phone, "about": about}})
        flash("Info updated!")
        return redirect(url_for("index"))
    return render_template("user_profile.html", user=user)


@app.route("/dog_surrender")
def dog_surrender():
    return render_template("dog_surrender.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if request.method == "POST":
        # Use existing data for registered users
        if session.get("user") is None:
            email = request.form.get("email")
            name = f"{request.form.get('name')} (Not registered)"
            registered = False
        else:
            user = mongo.db.users.find_one({"username": session["user"]})
            email = user["email"]
            name = user["username"]
            registered = True
        # Send message to admin
        message_item = {
            "sent_by": name,
            "sent_on": datetime.today().timetuple(),
            "send_to": "Admin",
            "create_date": datetime.now().strftime("%d/%m/%Y"),
            "create_time": datetime.now().strftime("%H:%M"),
            "subject": request.form.get("subject"),
            "sender_email": email,
            "message": request.form.get("message"),
            "registered": registered,
            "status": "unread",
            "replied": False,
            "type": "standard"
        }
        mongo.db.messages.insert_one(message_item)
        return redirect(url_for("alert", response="message sent"))
    return render_template("contact.html")


@app.route("/post_new", methods=["GET", "POST"])
def post_new():
    categories = list(mongo.db.categories.find())
    if request.method == "POST":
        # Create new post and upload to database
        new_post = {
            "title": request.form.get("title"),
            "summary": request.form.get("summary"),
            "content": request.form.get("content"),
            "category": request.form.get("category"),
            "author": session["user"],
            "created": datetime.today().timetuple(),
            "create_date": datetime.now().strftime("%d/%m/%Y"),
            "create_time": datetime.now().strftime("%H:%M"),
            "update_date": "",
            "likes": 0,
        }
        mongo.db.posts.insert_one(new_post)
        flash("New post added!")
        return redirect(url_for("index"))
    return render_template("post_new.html", categories=categories)


@app.route("/post_edit/<post_id>", methods=["GET", "POST"])
def post_edit(post_id):
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    categories = list(mongo.db.categories.find())
    if request.method == "POST":
        title = request.form.get("title")
        summary = request.form.get("summary")
        content = request.form.get("content")
        mongo.db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {"title": title, "summary": summary,
                      "content": content,
                      "update_date": datetime.today().timetuple()}})
        flash("Changes are saved !")
        return redirect(url_for('post_page', post_id=post_id))
    return render_template(
        "post_edit.html", post=post, categories=categories)


@app.route("/post_delete/<post_id>")
def post_delete(post_id):
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    users = list(mongo.db.users.find())
    # Delete post from 'liked_posts' list for all users
    # in users collection
    for user in users:
        if ObjectId(post_id) in user["liked_posts"]:
            user["liked_posts"].remove(post["_id"])
            mongo.db.users.update_one(
                {"username": user["username"]},
                {"$set": {"liked_posts": user["liked_posts"]}})
    # Delete post from database
    mongo.db.posts.delete_one({"_id": ObjectId(post_id)})
    flash("Post deleted!")
    return redirect("index")


@app.route("/post_page/<post_id>")
def post_page(post_id):
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    user = mongo.db.users.find_one({"username": session["user"]})
    # Create a string with update date if exists in database
    if post["update_date"] != "":
        day = post["update_date"][2]
        mon = post["update_date"][1]
        year = post["update_date"][0]
        hour = post["update_date"][3]
        mins = post["update_date"][4]
        update_date = f"{day}/{mon}/{year} at {hour}:{mins}"
    else:
        update_date = ""
    # Check if session user has liked this post before
    if user is not None:
        if post["_id"] in user["liked_posts"]:
            liked_post = True
        else:
            liked_post = False
    return render_template(
        "post_page.html", post=post, liked_post=liked_post,
        update_date=update_date)


@app.route("/post_like/<post_id>")
def post_like(post_id):
    user = mongo.db.users.find_one({"username": session["user"]})
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    likes = int(post["likes"])
    # Remove like
    if post["_id"] in user["liked_posts"]:
        likes -= 1
        user["liked_posts"].remove(post["_id"])
    # Add like
    else:
        likes += 1
        user["liked_posts"].append(post["_id"])
    # Update number of post likes in database
    mongo.db.posts.update_one(
        {"_id": ObjectId(post_id)},
        {"$set": {"likes": likes}})
    # Update list of users liked posts in database
    mongo.db.users.update_one(
        {"username": session["user"]},
        {"$set": {"liked_posts": user["liked_posts"]}})
    return redirect(url_for("post_page", post_id=post_id))


@app.route("/dog_new", methods=["GET", "POST"])
def dog_new():
    if request.method == "POST":
        user = mongo.db.users.find_one({"username": session["user"]})
        # Create new dog entry and upload to database
        dog = {
            "name": request.form.get("name").lower(),
            "gender": request.form.get("gender"),
            "age": request.form.get("age"),
            "size": request.form.get("size"),
            "good_with": request.form.getlist("good_with"),
            "description": request.form.get("description"),
            "greeting": request.form.get("greeting"),
            "created": datetime.today().timetuple(),
            "owner_id": user["_id"]
        }
        mongo.db.dogs.insert_one(dog)
        flash("New dog added!")
        return redirect(url_for("index"))
    return render_template("dog_new.html")


@app.route("/dog_edit/<dog_id>", methods=["GET", "POST"])
def dog_edit(dog_id):
    dog = mongo.db.dogs.find_one({"_id": ObjectId(dog_id)})
    if request.method == "POST":
        # Get all values from form and update database
        name = request.form.get("name").lower()
        gender = request.form.get("gender")
        age = request.form.get("age")
        size = request.form.get("size")
        description = request.form.get("description")
        greeting = request.form.get("greeting")
        good_with = request.form.getlist("good_with")
        mongo.db.dogs.update_one(
            {"_id": ObjectId(dog_id)},
            {"$set": {"name": name, "gender": gender, "age": age,
                      "size": size, "description": description,
                      "greeting": greeting, "good_with": good_with}})
        flash("Changes are saved !")
        return redirect(url_for('dog_page', dog_id=dog_id))
    return render_template("dog_edit.html", dog=dog)


@app.route("/dog_delete/<dog_id>")
def dog_delete(dog_id):
    user = mongo.db.users.find_one({"username": session["user"]})
    dog = mongo.db.dogs.find_one({"_id": ObjectId(dog_id)})
    users = list(mongo.db.users.find())
    for user in users:
        # Send message about dog deletion to all applicants
        if ObjectId(dog_id) in user["adoption_requests"]:
            message_item = {
                "sent_by": "Admin",
                "send_to": user["username"],
                "sent_on": datetime.today().timetuple(),
                "create_date": datetime.now().strftime("%d/%m/%Y"),
                "create_time": datetime.now().strftime("%H:%M"),
                "subject": (
                    f"Re: Adoption - {dog['name'].capitalize()}"),
                "message": (
                    f"""
                    This is automated message to inform you that \
                    {dog['name'].capitalize()} is not available for \
                    adoption anymore. Thank you for your interest in \
                    adopting {dog['name'].capitalize()} and please \
                    keep an eye on other dogs that need saving!
                    """),
                "status": "unread",
                "replied": False,
                "type": "adoption"
            }
            mongo.db.messages.insert_one(message_item)
    # Delete dog from user's adoption requests in database
    user["adoption_requests"].remove(dog["_id"])
    mongo.db.users.update_one(
        {"username": user["username"]},
        {"$set": {
            "adoption_requests": user["adoption_requests"]}})
    # Remove dog from database
    mongo.db.dogs.delete_one({"_id": ObjectId(dog_id)})
    flash("Dog sucessfully removed from database !")
    return redirect(url_for('index'))


@app.route("/dog_page/<dog_id>")
def dog_page(dog_id):
    # Prevent users with incomplete profile from adopting
    user = mongo.db.users.find_one({"username": session["user"]})
    if (user["fname"] == "" or
            user["lname"] == "" or
            user["phone"] == "" or
            user["about"] == ""):
        flash(
            """
            In order to apply for dog adoption you need to provide \
            more details about yourself. Please update your \
            profile before applying.
            """)
        user_info = False
    else:
        user_info = True
    # Check if user already applied for adoption
    dog = mongo.db.dogs.find_one({"_id": ObjectId(dog_id)})
    if dog["_id"] in user["adoption_requests"]:
        adoption_request = True
    else:
        adoption_request = False
    owner = mongo.db.users.find_one({"_id": dog["owner_id"]})
    return render_template(
        "dog_page.html", dog=dog, owner=owner, user_info=user_info,
        adoption_request=adoption_request)


@app.route("/adopt/<dog_id>")
def adopt(dog_id):
    user = mongo.db.users.find_one({"username": session["user"]})
    dog = mongo.db.dogs.find_one({"_id": ObjectId(dog_id)})
    # Prevent users with incomplete profile to call function
    if (user["fname"] == "" or
        user["lname"] == "" or
        user["phone"] == "" or
            user["about"] == ""):
        return permission_denied()
    # Send adoption request to admin inbox
    message_item = {
        "sent_by": user["username"],
        "send_to": "Admin",
        "sent_on": datetime.today().timetuple(),
        "create_date": datetime.now().strftime("%d/%m/%Y"),
        "create_time": datetime.now().strftime("%H:%M"),
        "subject": f"Adoption - {dog['name'].capitalize()}",
        "dog_id": dog_id,
        "dog_name": dog["name"].capitalize(),
        "sender_fname": user["fname"],
        "sender_lname": user["lname"],
        "sender_email": user["email"],
        "sender_phone": user["phone"],
        "sender_about": user["about"],
        "status": "unread",
        "replied": False,
        "type": "adoption"
    }
    mongo.db.messages.insert_one(message_item)
    # Add adoption request to user's record in database
    user["adoption_requests"].append(dog["_id"])
    mongo.db.users.update_one(
        {"username": session["user"]},
        {"$set": {"adoption_requests": user["adoption_requests"]}})
    flash(
        """
        Application sucessfully sent! One of our team members \
        will contact you shortly via inbox with further steps \
        in your application.
        """)
    return redirect(url_for('dog_page', dog_id=dog_id))


@app.route("/adopt_undo/<dog_id>")
def adopt_undo(dog_id):
    user = mongo.db.users.find_one({"username": session["user"]})
    dog = mongo.db.dogs.find_one({"_id": ObjectId(dog_id)})
    # Delete users request from database
    user["adoption_requests"].remove(dog["_id"])
    mongo.db.messages.delete_one({"dog_id": dog_id})
    mongo.db.users.update_one(
        {"username": session["user"]},
        {"$set": {"adoption_requests": user["adoption_requests"]}})
    flash("Application sucessfully withdrawn !")
    return redirect(
        url_for('dog_page', dog_id=dog_id))


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP"),
        port=int(os.environ.get("PORT")),
        debug=True)
