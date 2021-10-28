import pdb
import os
import random
from io import BytesIO
from PIL import Image, UnidentifiedImageError
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
    """Resizes photo uploaded by user and uploads photo to cloud

    Returns unique strings for uploaded photo (id, filename and path).
    Uses PIL to process and convert photo. Uses BytesIO to temporarily
    store converted image before uploading it to cloud.

    Args:
        item (str): Value should be ‘post’ or ‘dog’
        collection (list): ‘posts’ or ‘dogs’ collection from database

    Returns:
        img_id (str): Unique ID for every uploaded photo
        img_filename (str): Name of the uploaded photo file
        img_path (str): URL of the uploaded photo
    """
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
    """Routes to index.html

    Returns max 3 item per collection (posts / dogs) and sorts them
    from newest to oldest.

    Returns:
        render_template for index.html
    """
    # Sort posts by date/time
    posts = sorted(
        list(mongo.db.posts.find()), key=lambda k: k['created'], reverse=True)
    dogs = sorted(
        list(mongo.db.dogs.find()), key=lambda k: k['created'], reverse=True)
    # Limit posts/dogs to newest 3 items
    posts = posts[0:3]
    dogs = dogs[0:3]
    return render_template("index.html", posts=posts, dogs=dogs)


@app.route("/alert/<response>")
def alert(response):
    response_received = response
    return render_template(
        "alert.html", response=response_received)


@app.route("/user_register", methods=["GET", "POST"])
def user_register():
    if session.get('user') is not None:
        return permission_denied()
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
    if session.get('user') is not None:
        return permission_denied()
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
    if session.get('user') is None:
        return permission_denied()
    session.pop("user")
    flash("You have been logged out sucessfully!")
    return redirect(url_for("index"))


@app.route("/user_profile", methods=["GET", "POST"])
def user_profile():
    if session.get('user') is None:
        return permission_denied()
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
    if session.get('user') is None:
        flash(
            "You have to be logged in in order to place an ad for rehoming \
            a dog.")
    return render_template("dog_surrender.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    if session.get('user') == "Admin":
        return permission_denied()
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


@app.route("/post_main", methods=["GET", "POST"])
def post_main():
    categories = list(mongo.db.categories.find())
    users = list(mongo.db.users.find())
    # Sort posts by date/time
    posts = sorted(
        list(mongo.db.posts.find()), key=lambda k: k['created'], reverse=True)
    # Return to index if no posts
    if len(posts) == 0:
        flash("There are no posts to show!")
        no_posts = True
        return redirect(url_for("index"))
    else:
        no_posts = False
    if request.method == "POST":
        category = request.form.get("category")
        author = request.form.get("author")
        sort_by = request.form.get("sort")
        # Sort posts by category and author
        if category is None and author is None:
            posts = list(mongo.db.posts.find())
        elif category is None:
            posts = list(mongo.db.posts.find({"author": author}))
        elif author is None:
            posts = list(mongo.db.posts.find({"category": category}))
        else:
            posts = list(mongo.db.posts.find(
                {"category": category, "author": author}))

        def get_date(item):
            return item.get('created')

        def get_likes(item):
            return item.get('likes')

        # Sort posts from new to old by default
        posts.sort(key=get_date, reverse=True)
        # Sort posts by date/time and number of likes (user's choice)
        if sort_by == "New to old":
            posts.sort(key=get_date, reverse=True)
        elif sort_by == "Old to new":
            posts.sort(key=get_date)
        elif sort_by == "Most popular":
            posts.sort(key=get_likes, reverse=True)
    if len(posts) == 0:
        no_posts = True
        post_top = None
    else:
        post_top = posts[0]
        posts.pop(0)
    return render_template(
        "post_main.html", users=users, posts=posts, categories=categories,
        post_top=post_top, no_posts=no_posts)



@app.route("/post_new", methods=["GET", "POST"])
def post_new():
    if session.get('user') is None:
        return permission_denied()
    categories = list(mongo.db.categories.find())
    if request.method == "POST":
        if list(request.files['photo']) == []:
            img_path = "/static/images/post_default.webp"
            img_id = "default"
            img_filename = "post_img_default.webp"
        else:
            try:
                Image.open(request.files['photo'])
            except UnidentifiedImageError:
                flash("Image type not supported.")
                return redirect(url_for("post_new"))
            posts = mongo.db.posts.find()
            img_id, img_filename, img_path = generate_photo("post", posts)
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
            "img_id": img_id,
            "img_filename": img_filename,
            "img_path": img_path
        }
        mongo.db.posts.insert_one(new_post)
        flash("New post added!")
        return redirect(url_for("index"))
    return render_template("post_new.html", categories=categories)


@app.route("/post_edit/<post_id>", methods=["GET", "POST"])
def post_edit(post_id):
    if session.get('user') is None:
        return permission_denied()
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    # Show 'post not available' error page
    if post is None:
        return redirect(url_for("alert", response="post error"))
    # Show page only to post author or admin
    if session["user"] != post["author"] and session["user"] != "Admin":
        return permission_denied()
    categories = list(mongo.db.categories.find())
    if request.method == "POST":
        if list(request.files['photo']) != [] and post["img_id"] != "default":
            MY_BUCKET.Object(post["img_filename"]).delete()
        try:
            Image.open(request.files['photo'])
        except UnidentifiedImageError:
            flash("Image type not supported.")
            return redirect(url_for("post_edit"))
        posts = mongo.db.posts.find()
        img_id, img_filename, img_path = generate_photo("post", posts)
        title = request.form.get("title")
        summary = request.form.get("summary")
        content = request.form.get("content")
        mongo.db.posts.update_one(
            {"_id": ObjectId(post_id)},
            {"$set": {"title": title, "summary": summary,
                      "content": content, "img_path": img_path,
                      "img_id": img_id, "img_filename": img_filename,
                      "update_date": datetime.today().timetuple()}})
        flash("Changes are saved !")
        return redirect(url_for('post_page', post_id=post_id))
    return render_template(
        "post_edit.html", post=post, categories=categories)


@app.route("/post_delete/<post_id>")
def post_delete(post_id):
    if session.get('user') is None:
        return permission_denied()
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    # Allow code to run only if post exists in database
    if post is None:
        return redirect(url_for("alert", response="post error"))
    # Allow only to post author or admin to delete post
    if post["author"] != session["user"] and session["user"] != "Admin":
        return permission_denied()
    users = list(mongo.db.users.find())
    # Delete post from 'liked_posts' list for all users
    # in users collection
    for user in users:
        if ObjectId(post_id) in user["liked_posts"]:
            user["liked_posts"].remove(post["_id"])
            mongo.db.users.update_one(
                {"username": user["username"]},
                {"$set": {"liked_posts": user["liked_posts"]}})
    # Delete post image filepath for all except default images
    if post["img_id"] != "default":
        MY_BUCKET.Object(post["img_filename"]).delete()
    # Delete post from database
    mongo.db.posts.delete_one({"_id": ObjectId(post_id)})
    flash("Post deleted!")
    return redirect(url_for("post_main"))


@app.route("/post_page/<post_id>")
def post_page(post_id):
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    # Allow code to run only if post exists in database
    if post is None:
        return redirect(url_for("alert", response="post error"))
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

    if session.get('user') is None:
        liked_post = None
        user = None
    else:
        user = mongo.db.users.find_one({"username": session["user"]})

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
    if session.get('user') is None:
        return permission_denied()
    user = mongo.db.users.find_one({"username": session["user"]})
    post = mongo.db.posts.find_one({"_id": ObjectId(post_id)})
    # Call function only if post exists
    if post is None:
        return redirect(url_for("alert", response="post error"))
    # # Prevent post author or admin from calling the function
    if post["author"] == session["user"] or session["user"] == "Admin":
        return permission_denied()
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


@app.route("/dog_main", methods=["GET", "POST"])
def dog_main():
    # Sort dogs by date/time
    dogs = sorted(
        list(mongo.db.dogs.find()), key=lambda k: k['created'], reverse=True)
    # Returns to index if no dogs
    if len(dogs) == 0:
        no_dogs = True
        flash("There are no dogs to show!")
        return redirect(url_for("index"))
    else:
        no_dogs = False
    # total number of dogs in DB
    tot_len = len(dogs)
    cur_len = len(dogs)
    if request.method == "POST":
        name = request.form.get("name").lower()
        gender = request.form.get("gender")
        size = request.form.get("size")
        gwith = request.form.getlist("good_with")
        if request.form.get("name") != "":
            dogs = list(mongo.db.dogs.find({"name": {"$regex": name}}))
            # Sort dogs by date/time
            dogs = sorted(dogs, key=lambda k: k['created'], reverse=True)
        # Get dogs matching requested age
        if request.form.get("age") is not None:
            if request.form.get("age") == "0-3":
                dogs = [item for item in dogs if int(item["age"]) <= 3]
            elif request.form.get("age") == "4-7":
                dogs = [item for item in dogs if 3 < int(item["age"]) < 8]
            else:
                dogs = [item for item in dogs if int(item["age"]) > 7]
        # Get dogs matching requested gender
        if request.form.get("gender") is not None:
            dogs = [item for item in dogs if item["gender"] == gender]
        # Get dogs matching requested size
        if request.form.get("size") is not None:
            dogs = [item for item in dogs if item["size"] == size]
        # Iterate through dogs_copy list and save changes to dogs list
        if request.form.getlist("good_with") != []:
            dogs_copy = dogs.copy()
            for item in gwith:
                for dog in dogs_copy:
                    if item not in dog["good_with"]:
                        try:
                            dogs.remove(dog)
                        except ValueError:
                            pass
        # Number of dogs after all filters are applied
        cur_len = len(dogs)

    if len(dogs) == 0:
        no_dogs = True
        dog_top = None
    else:
        dog_top = dogs[0]
        dogs.pop(0)

    return render_template(
        "dog_main.html", dogs=dogs, tot_len=tot_len, cur_len=cur_len,
        no_dogs=no_dogs, dog_top=dog_top)



@app.route("/dog_new", methods=["GET", "POST"])
def dog_new():
    if session.get('user') is None:
        return permission_denied()
    user = mongo.db.users.find_one({"username": session["user"]})
    # Prevent users with incomplete info from posting dog ads
    if (user["fname"] == "" or
            user["lname"] == "" or
            user["phone"] == "" or
            user["about"] == ""):
        user_info = False
    else:
        user_info = True

    if request.method == "POST":
        if list(request.files['photo']) == []:
            img_path = "/static/images/dog_default.webp"
            img_id = "default"
            img_filename = "dog_img_default.webp"
        else:
            try:
                Image.open(request.files['photo'])
            except UnidentifiedImageError:
                flash("Image type not supported.")
                return redirect(url_for("dog_new"))
            dogs = mongo.db.dogs.find()
            img_id, img_filename, img_path = generate_photo("dog", dogs)
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
            "owner_id": user["_id"],
            "img_id": img_id,
            "img_filename": img_filename,
            "img_path": img_path
        }
        mongo.db.dogs.insert_one(dog)
        flash("New dog added!")
        return redirect(url_for("dog_main"))
    return render_template("dog_new.html", user_info=user_info)


@app.route("/dog_edit/<dog_id>", methods=["GET", "POST"])
def dog_edit(dog_id):
    if session.get('user') is None:
        return permission_denied()

    user = mongo.db.users.find_one({"username": session["user"]})
    dog = mongo.db.dogs.find_one({"_id": ObjectId(dog_id)})
    # Allow code to run only if dog exists in database
    if dog is None:
        return redirect(url_for("alert", response="dog error"))
    #  Allow only original poster or admin to see the page
    if user["_id"] != dog["owner_id"] and session["user"] != "Admin":
        return permission_denied()

    if request.method == "POST":
        if list(request.files['photo']) != [] and dog["img_id"] != "default":
            MY_BUCKET.Object(dog["img_filename"]).delete()
        try:
            Image.open(request.files['photo'])
        except UnidentifiedImageError:
            flash("Image type not supported.")
            return redirect(url_for("dog_edit"))
        dogs = mongo.db.dogs.find()
        img_id, img_filename, img_path = generate_photo("dog", dogs)
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
                      "greeting": greeting, "good_with": good_with, 
                      "img_path": img_path, "img_filename": img_filename,
                      "img_id": img_id}})
        flash("Changes are saved !")
        return redirect(url_for('dog_page', dog_id=dog_id))
    return render_template("dog_edit.html", dog=dog)


@app.route("/dog_delete/<dog_id>")
def dog_delete(dog_id):
    if session.get('user') is None:
        return permission_denied()
    user = mongo.db.users.find_one({"username": session["user"]})
    dog = mongo.db.dogs.find_one({"_id": ObjectId(dog_id)})
    users = list(mongo.db.users.find())
    # Allow code to run only if dog exists in database
    if dog is None:
        return redirect(url_for("alert", response="dog error"))
    # Allow only dog owner or admin to delete the dog
    if user["_id"] != dog["owner_id"] and session["user"] != "Admin":
        return permission_denied()

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
    # Delete only images uploaded by users, not default system images
    if dog["img_id"] != "default":
        MY_BUCKET.Object(dog["img_filename"]).delete()
    # Remove dog from database
    mongo.db.dogs.delete_one({"_id": ObjectId(dog_id)})
    flash("Dog sucessfully removed from database !")
    return redirect(url_for('dog_main'))


@app.route("/dog_page/<dog_id>")
def dog_page(dog_id):
    dog = mongo.db.dogs.find_one({"_id": ObjectId(dog_id)})
    # Allow code to run only if dog exists in database
    if dog is None:
        return redirect(url_for("alert", response="dog error"))
    if session.get('user') is None:
        adoption_request = None
        user_info = None
        flash(
            """
            In order to apply for dog adoption you need to have \
            registered account and provide all necessary details \
            about yourself. Please register before applying.
            """)
    else:
        user = mongo.db.users.find_one({"username": session["user"]})
    # Prevent users with incomplete profile from adopting
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
    if session.get('user') is None:
        return permission_denied()
    user = mongo.db.users.find_one({"username": session["user"]})
    dog = mongo.db.dogs.find_one({"_id": ObjectId(dog_id)})
    # Allow code to run only if dog exists in database
    if dog is None:
        return redirect(url_for("alert", response="dog error"))
    # Prevent users with incomplete profile to call function
    if (user["fname"] == "" or
        user["lname"] == "" or
        user["phone"] == "" or
            user["about"] == ""):
        return permission_denied()
    # Allow everyone except dog owner or admin to call this function
    if user["_id"] == dog["owner_id"] or session["user"] == "Admin":
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
    if session.get('user') is None:
        return permission_denied()
    user = mongo.db.users.find_one({"username": session["user"]})
    dog = mongo.db.dogs.find_one({"_id": ObjectId(dog_id)})
    # Allow code to run only if dog exists in database
    if dog is None:
        return redirect(url_for("alert", response="dog error"))
    # Allow everyone except dog owner or admin to call this function
    if user["_id"] == dog["owner_id"] or session["user"] == "Admin":
        return permission_denied()
    # Delete users request from database
    user["adoption_requests"].remove(dog["_id"])
    mongo.db.messages.delete_one({"dog_id": dog_id})
    mongo.db.users.update_one(
        {"username": session["user"]},
        {"$set": {"adoption_requests": user["adoption_requests"]}})
    flash("Application sucessfully withdrawn !")
    return redirect(
        url_for('dog_page', dog_id=dog_id))


@app.route("/inbox")
def inbox():
    if session.get('user') is None:
        return permission_denied()

    # Get all messages / adoption requests
    admin_msgs = list(mongo.db.messages.find(
        {"type": "standard", "send_to": "Admin"}))
    admin_reqs = list(mongo.db.messages.find(
        {"type": "adoption", "send_to": "Admin"}))
    user_msgs = list(mongo.db.messages.find({"send_to": session["user"]}))

    # Sort messages from new to old
    def get_date(item):
        return item.get('sent_on')

    admin_msgs.sort(key=get_date, reverse=True)
    admin_reqs.sort(key=get_date, reverse=True)
    user_msgs.sort(key=get_date, reverse=True)
    # Get number of unread messages / adoption requests
    admin_unread_msgs = len(list(mongo.db.messages.find(
        {"type": "standard", "send_to": "Admin", "status": "unread"})))
    admin_unread_reqs = len(list(mongo.db.messages.find(
        {"type": "adoption", "send_to": "Admin", "status": "unread"})))
    user_unread_msgs = len(list(mongo.db.messages.find(
        {"send_to": session["user"], "status": "unread"})))

    return render_template(
        "inbox.html", admin_msgs=admin_msgs, admin_reqs=admin_reqs,
        user_msgs=user_msgs, admin_unread_msgs=admin_unread_msgs,
        admin_unread_reqs=admin_unread_reqs,
        user_unread_msgs=user_unread_msgs)


@app.route("/message/<msg_id>")
def message(msg_id):
    if session.get('user') is None:
        return permission_denied()
    message_item = mongo.db.messages.find_one({"_id": ObjectId(msg_id)})
    # Allow user to open mesage only if message exists
    if message_item is None:
        return redirect(url_for("alert", response="message error"))
    # Allow only intended receivers to see the message
    if session["user"] != message_item["send_to"]:
        return permission_denied()
    # Dog variable is needed by adoption requests
    try:
        dog = mongo.db.dogs.find_one(
            {"_id": ObjectId(message_item["dog_id"])})
        dog_id = message_item["dog_id"]
    # If normal message dog variable is none
    except KeyError:
        dog = None
        dog_id = None
    # Message status in database is changed from 'unread' to 'read'
    mongo.db.messages.update_one(
        {"_id": ObjectId(msg_id)},
        {"$set": {"status": "read"}})
    return render_template(
        "message.html", message=message_item, dog=dog, dog_id=dog_id)


@app.route("/reply/<receiver>/<msg_id>", methods=["GET", "POST"])
def reply(receiver, msg_id):
    if session.get('user') is None:
        return permission_denied()
    user = mongo.db.users.find_one({"username": session["user"]})
    orig_msg = mongo.db.messages.find_one({"_id": ObjectId(msg_id)})
    # Alow only intended receiver to reply to message
    if session["user"] != orig_msg["send_to"]:
        return permission_denied()
    # Puts 'Re:' to message subject when replying
    if orig_msg["subject"][0:3] == "Re:":
        subject = orig_msg["subject"]
    else:
        subject = f"Re: {orig_msg['subject']}"
    # Standard message
    if orig_msg["type"] == "standard":
        message_item = {
            "sent_by": user["username"],
            "send_to": receiver,
            "sent_on": datetime.today().timetuple(),
            "create_date": datetime.now().strftime("%d/%m/%Y"),
            "create_time": datetime.now().strftime("%H:%M"),
            "subject": subject,
            "message": request.form.get("message"),
            "registered": True,
            "status": "unread",
            "replied": False,
            "type": "standard"
        }
    # Adoption request message
    else:
        message_item = {
            "sent_by": user["username"],
            "send_to": receiver,
            "sent_on": datetime.today().timetuple(),
            "create_date": datetime.now().strftime("%d/%m/%Y"),
            "create_time": datetime.now().strftime("%H:%M"),
            "subject": subject,
            "message": request.form.get("message"),
            "dog_name": orig_msg["dog_name"],
            "dog_id": orig_msg["dog_id"],
            "sender_fname": orig_msg["sender_fname"],
            "sender_lname": orig_msg["sender_lname"],
            "sender_email": orig_msg["sender_email"],
            "sender_phone": orig_msg["sender_phone"],
            "registered": True,
            "status": "unread",
            "replied": False,
            "type": "adoption"
        }
    mongo.db.messages.update_one(
        {"_id": ObjectId(msg_id)},
        {"$set": {"replied": True}})
    mongo.db.messages.insert_one(message_item)
    return redirect(url_for("alert", response="message sent"))


@app.route("/message_delete/<msg_id>")
def message_delete(msg_id):
    if session.get('user') is None:
        return permission_denied()
    message_item = mongo.db.messages.find_one({"_id": ObjectId(msg_id)})
    # Call function only if message exists
    if message_item is None:
        return redirect(url_for("alert", response="message error"))
    # Allow only intended receiver to delete message
    if session["user"] != message_item["send_to"]:
        return permission_denied()
    mongo.db.messages.delete_one({"_id": ObjectId(msg_id)})
    flash("Message deleted !")
    return redirect(url_for('inbox'))


@app.context_processor
def global_vars():
    if session.get('user') is None:
        user = False
    else:
        user = True

    unread_msgs = 0
    unread_reqs = 0

    if user:
        # Get the number of unread messages in inbox
        unread_msgs = len(list(mongo.db.messages.find(
            {"subject": {"$ne": "Adoption"}, "send_to": session["user"],
                "status": "unread"})))
        # Get the number of unread adoption requests (admin only)
        unread_reqs = len(list(mongo.db.messages.find(
            {"subject": "Adoption", "status": "unread"})))
    return {
        # msgs_reqs are for admin only
        'msgs': unread_msgs,
        'msgs_reqs': unread_msgs + unread_reqs}


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP"),
        port=int(os.environ.get("PORT")),
        debug=True)
