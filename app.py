import os
import random
from io import BytesIO
from datetime import datetime
from PIL import Image, UnidentifiedImageError
from flask import (
    Flask, flash, render_template,
    redirect, request, session, url_for)
from flask_pymongo import PyMongo
from bson.objectid import ObjectId
from werkzeug.security import generate_password_hash, check_password_hash
import cloudinary
import cloudinary.uploader
if os.path.exists("env.py"):
    import env

# Configure flask app
app = Flask(__name__)

app.config["MONGO_DBNAME"] = os.environ.get("MONGO_DBNAME")
app.config["MONGO_URI"] = os.environ.get("MONGO_URI")
app.secret_key = os.environ.get("SECRET_KEY")

# Configure Cloudinary
cloudinary.config(cloudinary_url=os.environ.get("CLOUDINARY_URL"))

# Connect database with the app
mongo = PyMongo(app)


@app.errorhandler(403)
@app.errorhandler(404)
def page_error(e):
    """Error handler for most common error codes"""
    return redirect(url_for("alert", response="page error"))


@app.errorhandler(500)
def server_error(e):
    import traceback
    return f"<pre>{traceback.format_exc()}</pre>", 500


def permission_denied():
    """Flashes permission denied message and redirects to index page"""
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
    public_id = f"{item}_img_{img_id}"
    img_filename = f"{public_id}.webp"
    while True:
        image_exists = False
        for i in collection:
            if i["img_id"] == img_id:
                image_exists = True
        if image_exists:
            img_id = round(random.random() * 1000000)
            public_id = f"{item}_img_{img_id}"
            img_filename = f"{public_id}.webp"
        else:
            buffer = BytesIO()
            image.save(buffer, 'webp')
            buffer.seek(0)
            result = cloudinary.uploader.upload(
                buffer, public_id=public_id, resource_type='image')
            img_path = result['secure_url']
            break
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
    """Routes to alert.html

    Args:
        response (string): Value is returned to Jinja template which
            then decides on which message to display on screen

    Returns:
        render_template for alert.html
    """
    response_received = response
    return render_template("alert.html", response=response_received)


@app.route("/user_register", methods=["GET", "POST"])
def user_register():
    """Routes to user_register.html

    In case of POST request gets the data from the form and stores it
    in database. Checks if username or email already exist in database,
    and checks if inputted passwords match.

    Returns:
        render template for user_register.html
        redirect to index.html if sucessfully registered
        redirect to user_register.html if passwords don't match or
            username / email already exist in database
        call permission_denied function if there is user in session
    """
    if session.get('user') is not None:
        return permission_denied()
    if request.method == "POST":
        # Check if username/email exist
        existing_user = mongo.db.users.find_one(
            {"username": request.form.get("username")})
        existing_email = mongo.db.users.find_one(
            {"email": request.form.get("email")})
        if existing_user:
            flash("Username already in use!", "error")
            return redirect(url_for("user_register"))
        if existing_email:
            flash("Email already in use!", "error")
            return redirect(url_for("user_register"))
        # Check if passwords match
        password1 = request.form.get("password")
        password2 = request.form.get("password2")
        if password1 != password2:
            flash("Passwords don't match!", "error")
            return redirect(url_for("user_register"))
        # Save user details to database
        new_user = {
            "username": request.form.get("username"),
            "password": generate_password_hash(request.form.get("password")),
            "email": "",
            "fname": "",
            "lname": "",
            "phone": "",
            "about": "",
            "liked_posts": [],
            "adoption_requests": []
        }
        mongo.db.users.insert_one(new_user)
        flash("You are now registered!")
        return redirect(url_for("user_login"))
    return render_template("user_register.html")


@app.route("/user_login", methods=["GET", "POST"])
def user_login():
    """Routes to user_login.html and adds user to the session

    In case of POST request gets the data from the form and checks if
    document for specified user exists in database. If so, checks if
    provided password matches the password record from user document in
    database.

    Returns:
        render template for user_login.html
        redirect to index.html if sucessfully logged in
        redirect to user_login.html if provided password don't match
            with the one in database or if username couldn't be found
            in database.
        call permission_denied function if there is no user in session
    """
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
    """Routes to index.html and removes user from the session

    Returns:
        redirect to index.html
        call permission_denied function if there is no user in session
    """
    if session.get('user') is None:
        return permission_denied()
    session.pop("user")
    flash("You have been logged out sucessfully!")
    return redirect(url_for("index"))


@app.route("/user_profile", methods=["GET", "POST"])
def user_profile():
    """Routes to user_profile.html

    In case of POST request there are two forms on the page. First form
    changes the password, and second form updates user details.

    Returns:
        render_template for user_profile.html
        call permission_denied function if there is no user in session
    """
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
                return redirect(url_for("user_profile"))
            else:
                flash("New passwords don't match!")
                return redirect(url_for("user_profile"))
        else:
            flash("Current password wrong!")
            return redirect(url_for("user_profile"))
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
        return redirect(url_for("user_profile"))
    return render_template("user_profile.html", user=user)


@app.route("/dog_surrender")
def dog_surrender():
    """Routes to dog_surrender.html"""
    if session.get('user') is None:
        user_info = None
        flash(
            "You have to be logged in in order to place an ad for rehoming \
            a dog.")
    else:
        # Prevent users with incomplete info from posting dog ads
        user = mongo.db.users.find_one({"username": session["user"]})
        if (user["fname"] == "" or
                user["lname"] == "" or
                user["phone"] == "" or
                user["about"] == ""):
            user_info = False
            flash(
                "To post new dog ads you need to complete your profile. \
                You can do this in your account settings under 'optional \
                info' section.")
        else:
            user_info = True
    return render_template("dog_surrender.html", user_info=user_info)


@app.route("/contact", methods=["GET", "POST"])
def contact():
    """Routes to contact.html

    In case of POST request makes new document of 'messages' collection
    in database.

    Returns:
        render_template for contact.html
        redirect to alert.html when message is sent
        call permission_denied function to prevent admin from seeing the page
    """
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
    """Routes to post_main.html

    In case of POST request, searches for documents in posts collection
    from database by specific criteria. Sorts documents by 'created' or
    'likes' records.

    Returns:
        render template for post_main.html
    """
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
        # Filter posts by category and author
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
    """Routes to post_new.html and creates new post

    In case of POST request checks if user has uploaded the photo. If
    not, sets up image parameters as default image. If yes, calls
    generate_photo fuction. Creates new_post dictionary and uploads it
    as new document in 'posts' collection in database.

    Returns:
        render template for post_new.html
        redirect to post_main.html when post is uploaded to database
        call permission_denied function if there is no user in session

    Raises:
        UnidentifiedImageError - Prevents user from uploading non image
            documents. Returns redirect to post_new.html.
    """
    if session.get('user') is None:
        return permission_denied()
    categories = list(mongo.db.categories.find())
    if request.method == "POST":
        photo = request.files['photo']
        if photo.filename == "":
            img_path = "/static/images/post_default.webp"
            img_id = "default"
            img_filename = "post_img_default.webp"
        else:
            try:
                Image.open(photo)
            except UnidentifiedImageError:
                flash("Image type not supported.", "error")
                return redirect(url_for("post_new"))
            posts = mongo.db.posts.find()
            img_id, img_filename, img_path = generate_photo("post", posts)
        # Create new post and upload to database
        temp_id = round(random.random() * 1000000)
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
            "img_path": img_path,
            "temp_id": temp_id
        }
        mongo.db.posts.insert_one(new_post)
        flash("New post added!")
        # temp_id is used to identify the just added post, in order to get
        # post_id from database so post_page can be called. temp_id record is
        # deleted from database immediately after post_id is obtained
        new_db_post = mongo.db.posts.find_one({"temp_id": temp_id})
        post_id = new_db_post["_id"]
        mongo.db.posts.update_one(
            {"temp_id": temp_id},
            {"$unset": {"temp_id": ""}})
        return redirect(url_for("post_page", post_id=post_id))
    return render_template("post_new.html", categories=categories)


@app.route("/post_edit/<post_id>", methods=["GET", "POST"])
def post_edit(post_id):
    """Routes to post_edit.html and modifies the post

    Gets document from 'posts' collection in database and pre populates
    the form on the page. In case of POST request, modifies 'post'
    document in database. In case new photo is uploaded, deletes old
    photo from cloud.

    Args:
        post_id (str): '_id' record of document from 'posts' collection
            in database

    Returns:
        render_template for post_edit.html
        redirect to post_page.html when modified post is uploaded to
            the database
        call permission_denied function if not requested by
            admin or post author, or if there is no user in session
        redirect to alert.html if requested 'post' document does not
            exist in database

    Raises:
        UnidentifiedImageError - Prevents user from uploading non image
            documents. Returns redirect to post_new.html.
    """
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
        photo = request.files['photo']
        if photo.filename != "" and post["img_id"] != "default":
            cloudinary.uploader.destroy(post["img_filename"].rsplit('.', 1)[0])
        if photo.filename != "":
            try:
                Image.open(photo)
            except UnidentifiedImageError:
                flash("Image type not supported.", "error")
                return redirect(url_for("post_edit", post_id=post_id))
            posts = mongo.db.posts.find()
            img_id, img_filename, img_path = generate_photo("post", posts)
        else:
            img_id = post["img_id"]
            img_filename = post["img_filename"]
            img_path = post["img_path"]
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
    """Deletes document from 'posts' collection in database

    Checks 'liked_posts' record of all documents from 'users' collection
    in database. If it contains provided post_id, then this post_id is
    deleted from the list. Deletes photo from cloud.

    Args:
        post_id (str): '_id' record of document from 'posts' collection
            in database

    Returns:
        render_template for post_main.html
        call permission_denied function if not requested by
            admin or post author
        redirect to alert.html if requested 'post' document does not
            exist in database
        call permission_denied function if there is no user in session
    """
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
        cloudinary.uploader.destroy(post["img_filename"].rsplit('.', 1)[0])
    # Delete post from database
    mongo.db.posts.delete_one({"_id": ObjectId(post_id)})
    flash("Post deleted!")
    return redirect(url_for("post_main"))


@app.route("/post_page/<post_id>")
def post_page(post_id):
    """Routes to post.html

    Args:
        post_id (str): '_id' record of document from 'posts' collection
            in database

    Returns:
        render_template for post.html
        redirect to alert.html if requested 'post' document does not
            exist in database
    """
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
    """Updates number of likes for the post

    Gets 'likes' record of document from 'posts' collection in
    database and updates it. Updates 'liked_posts' record of document
    from 'users' collection.

    Args:
        post_id (str): '_id' record of document from 'posts' collection
            in database

    Returns:
        redirect for post.html
        call permission_denied function if requested by admin or
            post author
        redirect to alert.html if requested 'post' document does not
            exist in database
        call permission_denied function if there is no user in session
    """
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
    """Routes to dog_main.html

    Sorts documents from 'dogs' collection from newest to oldest. In
    case of POST request, creates new list depending on search criteria
    received in form.

    Returns:
        render_template for dogs_main.html
        redirect to index.html if dogs collection in database is empty

    Raises:
        ValueError - Does not return value. Used to prevent error if
            document is not found in 'dogs' collection in database.
    """
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
    """Routes to dog_new.html

    In case of POST request checks if user has uploaded the photo. If
    not, sets up image parameters as default image. If yes, calls
    generate_photo fuction. Creates new_dog dictionary and uploads it
    as new document in 'dogs' collection in database.

    Returns:
        render template for dog_new.html
        redirect to dog_main.html when post is uploaded to database
        call permission_denied function if there is no user in session

    Raises:
        UnidentifiedImageError - Prevents user from uploading non image
            documents. Returns redirect to dog_new.html.
    """
    if session.get('user') is None:
        return permission_denied()
    user = mongo.db.users.find_one({"username": session["user"]})
    # Prevent users with incomplete info from posting dog ads
    if (user["fname"] == "" or
            user["lname"] == "" or
            user["phone"] == "" or
            user["about"] == ""):
        return permission_denied()
    if request.method == "POST":
        photo = request.files['photo']
        if photo.filename == "":
            img_path = "/static/images/dog_default.webp"
            img_id = "default"
            img_filename = "dog_img_default.webp"
        else:
            try:
                Image.open(photo)
            except UnidentifiedImageError:
                flash("Image type not supported.", "error")
                return redirect(url_for("dog_new"))
            dogs = mongo.db.dogs.find()
            img_id, img_filename, img_path = generate_photo("dog", dogs)
        # Create new dog entry and upload to database
        temp_id = round(random.random() * 1000000)
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
            "img_path": img_path,
            "temp_id": temp_id
        }
        mongo.db.dogs.insert_one(dog)
        flash("New dog added!")
        # temp_id is used to identify the just added dog, in order to get
        # dog_id from database so dog_page can be called. temp_id record is
        # deleted from database immediately after dog_id is obtained
        new_db_dog = mongo.db.dogs.find_one({"temp_id": temp_id})
        dog_id = new_db_dog["_id"]
        mongo.db.dogs.update_one(
            {"temp_id": temp_id},
            {"$unset": {"temp_id": ""}})
        return redirect(url_for("dog_page", dog_id=dog_id))
    return render_template("dog_new.html")


@app.route("/dog_edit/<dog_id>", methods=["GET", "POST"])
def dog_edit(dog_id):
    """Routes to dog_edit.html

    Gets document from 'dogs' collection in database and pre populates
    the form on the page. In case of POST request, modifies 'dog'
    document in database. In case new photo is uploaded, deletes old
    photo from cloud.

    Args:
        dog_id (str): '_id' record of document from 'dogs' collection
            in database

    Returns:
        render_template for dog_edit.html
        redirect to dog.html when edited dog is uploaded to database
        call permission_denied function if not requested by
            admin or dog owner, or if there is no user in session
        redirect to alert.html if requested 'post' document does not
            exist in database

    Raises:
        UnidentifiedImageError - Prevents user from uploading non image
            documents. Returns redirect to dog_new.html.
    """
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
        photo = request.files['photo']
        if photo.filename != "" and dog["img_id"] != "default":
            cloudinary.uploader.destroy(dog["img_filename"].rsplit('.', 1)[0])
        if photo.filename != "":
            try:
                Image.open(photo)
            except UnidentifiedImageError:
                flash("Image type not supported.", "error")
                return redirect(url_for("dog_edit", dog_id=dog_id))
            dogs = mongo.db.dogs.find()
            img_id, img_filename, img_path = generate_photo("dog", dogs)
        else:
            img_id = dog["img_id"]
            img_filename = dog["img_filename"]
            img_path = dog["img_path"]
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
    """Deletes the dog record from posts collection in database

    Checks 'liked_posts' record of all documents from 'users' collection
    in database. If it contains provided dog_id, then this dog_id is
    deleted from the list. Deletes photo from cloud.

    Args:
        dog_id (str): '_id' record of document from 'dogs' collection
            in database

    Returns:
        render_template for dog_main.html
        call permission_denied function if not requested by
            admin or dog owner, or if there is no user in session
        redirect to alert.html if requested 'post' document does not
            exist in database
    """
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
                "subject": (f"Re: Adoption - {dog['name'].capitalize()}"),
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
        {"$set": {"adoption_requests": user["adoption_requests"]}})
    # Delete only images uploaded by users, not default system images
    if dog["img_id"] != "default":
        cloudinary.uploader.destroy(dog["img_filename"].rsplit('.', 1)[0])
    # Remove dog from database
    mongo.db.dogs.delete_one({"_id": ObjectId(dog_id)})
    flash("Dog sucessfully removed from database !")
    return redirect(url_for('dog_main'))


@app.route("/dog_page/<dog_id>")
def dog_page(dog_id):
    """Routes to dog_page.html

    Args:
        dog_id (str): '_id' record of document from 'dogs' collection
            in database

    Returns:
        render_template for dog_page.html
        redirect to alert.html if requested 'dog' document does not
            exist in database
    """
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
    """Creates dog adoption request for the user

    Saves new adoption request as a document of 'messages' collection
    in database. Adds 'dog_id' to 'adoption_requests' record of
    document in 'users' collection in database.

    Args:
        dog_id (str): '_id' record of document from 'dogs' collection
            in database

    Returns:
        redirect to dog.html
        call permission_denied function if not requested by admin or
        dog owner, or if user object in database does not have full
        info (fname, lname, phone, about)
        call permission_denied function if there is no user in session
    """
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
    """Removes dog adoption request for the user

    Deletes adoption request represented as a document of 'messages'
    collection in database. Removes 'dog_id' from 'adoption_requests'
    record of document in 'users' collection in database.

    Args:
        dog_id (str): '_id' record of document from 'dogs' collection
            in database

    Returns:
        redirect to dog_page.html
        call permission_denied function if not requested by
            admin or dog owner, or if there is no user in session
    """
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
    return redirect(url_for('dog_page', dog_id=dog_id))


@app.route("/inbox")
def inbox():
    """Routes to inbox.html

    Displays all messages on the page from newest to oldest. Messages
    are divided separately for users and admin, and admin messages are
    divided into standard messages and adoption requests.

    Returns:
        render_template for inbox.html
    """
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
    """Routes to message.html

    Returns:
        render_template for message.html
        call permission_denied function if there is no user in session

    Raises:
        KeyError - In case of normal message (not adoption request),
            value of 'dog' and 'dog_id' variables is set to None.

    """
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
    """Sends reply message

    Creates and uploads new document to 'messages' collection in
    database. Message type can be normal or adoption request.

    Args:
        receiver (str): username to which reply is sent
        msg_id (str): '_id' record of original message from database

    Returns:
        redirect to alert.html when message is sent
        call permission_denied function if current user is not intended
            receiver, or if there is no user in session
    """
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
    """Deletes the message from database

    Returns:
        redirect to inbox.html
        redirect to alert.html if requested 'post' document does not
            exist in database
        call permission_denied function if message is not intended for
            current user, or if there is no user in session

    Raises:
        KeyError - Prevents logged out users from calling the function.
            Calls permission_denied function instead.
    """
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
    """Gets number of unread messages in inbox

    Returns:
        msgs (int): number of unread messages for standard user
        msgs_reqs (int): total number of messages + adoption requests
            for admin
    """
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


_POST_IMGS = [
    "https://images.dog.ceo/breeds/retriever-golden/n02099601_3004.jpg",
    "https://images.dog.ceo/breeds/labrador/n02099712_4323.jpg",
    "https://images.dog.ceo/breeds/husky/n02110185_10047.jpg",
    "https://images.dog.ceo/breeds/beagle/n02088364_10108.jpg",
    "https://images.dog.ceo/breeds/poodle-standard/n02113799_2280.jpg",
    "https://images.dog.ceo/breeds/bulldog-english/n02096585_1380.jpg",
]
_DOG_IMGS = [
    "https://images.dog.ceo/breeds/retriever-golden/n02099601_7771.jpg",
    "https://images.dog.ceo/breeds/husky/n02110185_11364.jpg",
    "https://images.dog.ceo/breeds/beagle/n02088364_13776.jpg",
    "https://images.dog.ceo/breeds/labrador/n02099712_7003.jpg",
    "https://images.dog.ceo/breeds/spaniel-cocker/n02102318_5978.jpg",
    "https://images.dog.ceo/breeds/poodle-standard/n02113799_4063.jpg",
]

_SEED_POSTS = [
    # ── Training ──────────────────────────────────────────────────────────────
    {"title": "5 Essential Commands Every Dog Should Know", "summary": "Teaching your dog basic commands is the foundation of a happy life together. Here are the five you should start with.", "content": "Starting with the basics is always the best approach.\n\n**1. Sit** – Hold a treat to your dog's nose, move your hand up so their bottom lowers, say 'Sit' and reward.\n\n**2. Stay** – Ask your dog to sit, open your palm and say 'Stay', step back and reward if they hold.\n\n**3. Come** – With a leash on, crouch and gently pull while saying 'Come'. Reward generously on arrival.\n\n**4. Down** – Hold a treat in a closed fist at their snout, move it to the floor. Their body will follow.\n\n**5. Leave it** – Show one treat-filled fist, say 'Leave it', reward from the other hand when they stop trying.\n\nShort frequent sessions beat long infrequent ones. Always end on a positive note!", "category": "Training", "author": "sarah_w", "likes": 24, "img": 0},
    {"title": "Advanced Recall: Getting Your Dog to Come Every Time", "summary": "A reliable recall could one day save your dog's life. Here is how to build one that holds up in any situation.", "content": "Recall is one of the most important skills your dog will ever learn, yet it is one of the most commonly neglected.\n\n**Start in a low-distraction environment.** Your garden or a quiet room is ideal. Use a long training lead (5–10 metres) so your dog has freedom but you maintain control.\n\n**Make coming back the best thing ever.** The moment your dog reaches you, throw a party. Use the highest-value treats you have – real chicken, cheese, sausage. Never call your dog to you for something unpleasant like nail clipping or bath time.\n\n**The two-toy game.** Call your dog, reward with toy one, then immediately produce toy two and throw it away from you. This teaches your dog that coming back doesn't mean the fun ends.\n\n**Proof it gradually.** Slowly increase distance, distraction, and duration. If your dog fails, you have moved too fast – go back a step.\n\n**Never punish a return.** Even if your dog took ten minutes to come back, reward them when they do. Punishment teaches them that coming back is a bad idea.", "category": "Training", "author": "sarah_w", "likes": 19, "img": 1},
    {"title": "Crate Training Done Right", "summary": "A crate, used correctly, gives your dog a safe haven they will choose willingly. Here is how to introduce one without stress.", "content": "Crate training is one of the most misunderstood topics in dog ownership. Done right, your dog will love their crate. Done wrong, it becomes a source of anxiety.\n\n**Choose the right size.** Your dog should be able to stand up, turn around, and lie down comfortably. Too large and they may toilet in one corner and sleep in the other.\n\n**Make it appealing from day one.** Toss treats inside without closing the door. Feed meals in or near the crate. Put a worn item of your clothing inside – your scent is comforting.\n\n**Build duration slowly.** Start with the door open, then closed for 30 seconds, then a minute, then five. Always let your dog out before they start to stress.\n\n**Never use it as punishment.** The crate should always be a positive place. Sending your dog there when you're angry destroys the association you've built.\n\n**Signs it's going well:** your dog goes in voluntarily, settles quickly, and is calm when you return. A dog that panics in the crate needs more gradual introduction, not more time locked in.", "category": "Training", "author": "Admin", "likes": 15, "img": 2},
    {"title": "How to Stop Your Dog Pulling on the Lead", "summary": "Lead pulling is one of the most common complaints from dog owners. The good news is it is entirely fixable with the right approach.", "content": "A dog that pulls on the lead makes walks unpleasant for both of you. The key is to understand why dogs pull – they want to get to the interesting thing ahead faster than you walk.\n\n**Stop and be a tree.** The moment the lead goes tight, stop completely. No forward movement until the lead is loose. Dogs quickly learn that pulling gets them nowhere.\n\n**Change direction.** When your dog forges ahead, calmly turn and walk the other way. Your dog must learn to pay attention to you, not just the environment.\n\n**Reward position.** Mark and reward your dog frequently for walking with a loose lead beside you. Reinforce the position you want, not just the absence of pulling.\n\n**Use the right equipment.** Front-clip harnesses or head collars can help manage pulling while you train. Avoid retractable leads – they teach dogs that pulling extends their range.\n\n**Be consistent.** Every person who walks your dog must follow the same rules. One walk where pulling is allowed undoes significant training progress.", "category": "Training", "author": "emma_r", "likes": 33, "img": 3},
    {"title": "Clicker Training: A Beginner's Guide", "summary": "Clicker training is one of the most effective and dog-friendly methods available. Here is everything you need to get started.", "content": "A clicker is a small handheld device that makes a distinctive click sound. In clicker training, the click marks the exact moment your dog does something right.\n\n**Why it works.** The click is faster and more precise than verbal praise. Dogs learn exactly which behaviour earned the reward, which speeds up learning dramatically.\n\n**Charging the clicker.** Before you start training behaviours, your dog needs to understand that click = treat. Click once, immediately give a treat. Repeat 20–30 times across a few short sessions. You'll know it's working when your dog's ears perk up at the sound.\n\n**The golden rule: click ends the behaviour.** The moment you click, the behaviour is done and the treat is coming. You can't click late – if you miss the moment, don't click.\n\n**Keep sessions short.** Five minutes is plenty, especially for young dogs. End every session on a success.\n\n**What to train.** Sit, down, and touch (nose to hand) are great starter behaviours. Once your dog understands the clicker, you can teach almost anything.", "category": "Training", "author": "sarah_w", "likes": 28, "img": 4},
    {"title": "Teaching Your Dog to Walk Off-Lead Safely", "summary": "Off-lead freedom is one of the greatest gifts you can give your dog. Here is how to get there safely and responsibly.", "content": "Before you unclip the lead, there are some non-negotiables: a solid recall, a calm response to other dogs, and a reliable 'stop' or 'wait' cue.\n\n**Start in secure areas.** A fully fenced field or secure garden lets you practise without the risk of your dog running off. Many areas rent out secure dog fields by the hour – they're ideal for early off-lead work.\n\n**Keep your dog engaged with you.** Don't just stand there while your dog explores. Move around, call them back frequently, play with them. You need to be more interesting than the environment.\n\n**Read the environment.** Before unclipping, scan for potential hazards: traffic, livestock, unfamiliar dogs, children. Off-lead freedom is a privilege that requires judgment.\n\n**Know the rules.** Many public spaces require dogs to be on lead. Always follow local bylaws and signage.\n\n**If in doubt, keep them on lead.** A long line (5–10 metres) gives your dog more freedom while you maintain a safety net. There is no shame in using one.", "category": "Training", "author": "mike_d", "likes": 22, "img": 5},
    # ── Health ────────────────────────────────────────────────────────────────
    {"title": "How to Spot Signs of a Healthy Dog", "summary": "Regular at-home health checks help you catch problems early. Learn what a healthy dog looks, feels and smells like.", "content": "**Eyes** – Bright and clear, no persistent discharge. A little sleep crust in the morning is normal.\n\n**Ears** – Clean and odour-free. Head shaking or pawing at ears can indicate infection or mites.\n\n**Coat** – Shiny and smooth. Dullness, bald patches or excessive shedding can signal nutritional deficiencies or skin conditions.\n\n**Weight** – You should feel ribs easily without pressing hard, but not see them prominently.\n\n**Gums** – Pink and moist. Press them and colour should return within two seconds. Pale, white, blue or yellow gums are emergencies.\n\n**Energy** – Know your dog's normal baseline. Sudden lethargy or unusual hyperactivity both warrant attention.\n\n**Bathroom habits** – Regular, firm stools. Diarrhoea lasting 24+ hours, blood in urine or stool, or straining to toilet needs a vet.\n\nA monthly five-minute check keeps you in tune with your dog's health and makes vet visits more productive.", "category": "Health", "author": "mike_d", "likes": 31, "img": 1},
    {"title": "Vaccinations: What Your Dog Needs and When", "summary": "Vaccinations protect your dog and the dogs they meet. Here is what every owner needs to know about the schedule.", "content": "Core vaccines protect against the most dangerous and widespread diseases. Your vet will advise on the exact schedule for your region.\n\n**Core vaccines (UK):**\n- Distemper, parvovirus, adenovirus (hepatitis) – given as a combined vaccine\n- Leptospirosis – given separately, annual booster required\n\n**Optional vaccines depending on lifestyle:**\n- Kennel cough (Bordetella/parainfluenza) – required by most boarding kennels\n- Rabies – required for travel abroad\n\n**Puppy schedule.** First vaccine typically at 8 weeks, second at 10–12 weeks. Most puppies can go out one week after their second vaccination.\n\n**Adult boosters.** Some components are boosted annually, others every three years. Your vet will remind you, but it's worth keeping your own records.\n\n**Titre testing.** Blood tests can check immunity levels, sometimes avoiding unnecessary boosters. Discuss with your vet if you prefer a more tailored approach.", "category": "Health", "author": "mike_d", "likes": 26, "img": 0},
    {"title": "Common Dog Allergies: Signs and Solutions", "summary": "Allergies in dogs are more common than many owners realise. Learn to spot the signs and how to get your dog relief.", "content": "Dogs can be allergic to environmental triggers, food ingredients, or contact allergens. Unlike humans, who typically get hay fever symptoms, dogs usually show allergies through their skin.\n\n**Common signs:** excessive itching (especially paws, ears, groin, armpits), recurring ear infections, red or inflamed skin, hair loss from scratching, scooting.\n\n**Environmental allergies** (atopy) – triggered by pollen, dust mites, mould. Often seasonal at first, becoming year-round over time. Managed with antihistamines, medicated shampoos, or prescription medication.\n\n**Food allergies** – the most common culprits are proteins: beef, chicken, dairy, wheat. Diagnosis requires a strict elimination diet for 8–12 weeks. This means nothing except the new food – no treats, flavoured medications, or shared scraps.\n\n**Contact allergies** – reactions to grass, cleaning products, or certain fabrics. Often affects the paws and belly.\n\n**What to do:** keep a diary of flare-ups to identify patterns, then work with your vet to narrow down the cause. Resist the urge to change foods without a plan – it makes diagnosis harder.", "category": "Health", "author": "Admin", "likes": 18, "img": 2},
    {"title": "Dental Care for Dogs: Why It Matters", "summary": "Dental disease affects the majority of dogs over three years old. Neglecting your dog's teeth has consequences far beyond bad breath.", "content": "By age three, 80% of dogs show signs of dental disease. Left untreated, it can lead to pain, tooth loss, and bacteria entering the bloodstream, potentially affecting the heart, kidneys and liver.\n\n**Signs of dental problems:** bad breath (beyond normal 'dog breath'), brown or yellow tartar buildup, red or swollen gums, pawing at the mouth, dropping food, reluctance to chew.\n\n**Brushing – the gold standard.** Daily brushing with a dog toothbrush and dog-safe toothpaste (never human toothpaste – xylitol is toxic) is the most effective prevention. Start slowly: let your dog lick toothpaste off your finger, then introduce a brush over several weeks.\n\n**Alternatives if brushing isn't possible:** dental chews, water additives, dental diets (specially formulated kibble), and raw bones (with appropriate supervision).\n\n**Professional scale and polish.** Your vet can assess dental health at annual check-ups and recommend a professional clean under anaesthetic when needed. It's a routine procedure.", "category": "Health", "author": "mike_d", "likes": 21, "img": 3},
    {"title": "Fleas, Ticks and Worms: A Complete Guide", "summary": "Parasites are unpleasant for dogs and owners alike. Here is everything you need to know about prevention and treatment.", "content": "**Fleas** are the most common parasite. Signs: scratching, small black 'flea dirt' in the coat, tapeworm segments (fleas carry tapeworm larvae). Treatment: prescription-strength spot-on or tablet treatments. Crucially, treat the home too – 95% of fleas live in carpets and furniture, not on your dog.\n\n**Ticks** are blood-sucking arachnids found in long grass and woodland. They can transmit Lyme disease. Remove them promptly with a tick twister – never squeeze, burn or twist. Check your dog after rural walks, especially around the ears, between toes, and in the groin.\n\n**Roundworms** are present in most puppies. Adult dogs can pick them up from infected faeces or prey animals. Monthly treatment for hunting breeds, quarterly for others.\n\n**Tapeworms** come from ingesting fleas or hunting. Signs: rice-like segments around the tail area.\n\n**Lungworm** is contracted from eating slugs or snails (including accidentally). It is potentially fatal and requires specific prevention – standard wormers don't cover it. Check with your vet.\n\n**Year-round prevention is key.** Speak to your vet about a tailored parasite protocol for your dog's lifestyle.", "category": "Health", "author": "sarah_w", "likes": 35, "img": 4},
    {"title": "When to Visit the Vet: Signs Not to Ignore", "summary": "Knowing when something is a 'wait and see' situation and when it needs urgent veterinary attention could save your dog's life.", "content": "**Go immediately (emergency):**\n- Difficulty breathing, blue or white gums\n- Suspected poisoning or ingestion of a foreign object\n- Collapse or sudden inability to stand\n- Bloated, hard abdomen (possible bloat/GDV – life-threatening)\n- Seizures lasting more than five minutes\n- Eye injuries or sudden vision loss\n- Suspected broken bone\n- Uncontrolled bleeding\n\n**Urgent (same day):**\n- Vomiting or diarrhoea more than twice in 24 hours\n- Blood in vomit, urine or stool\n- Suspected urinary blockage (straining without producing urine)\n- Sudden swelling of face or neck\n- Limping that doesn't resolve after rest\n\n**Book a routine appointment:**\n- Persistent scratching or skin changes\n- Gradual weight loss or gain\n- Increased thirst or urination\n- Bad breath or dental concerns\n- Lumps, bumps or new growths\n\nWhen in doubt, call your vet and describe the symptoms. A two-minute phone call can save you hours of worry.", "category": "Health", "author": "mike_d", "likes": 41, "img": 5},
    # ── Nutrition ─────────────────────────────────────────────────────────────
    {"title": "Raw vs Kibble: What's Best for Your Dog?", "summary": "The debate between raw feeding and dry food has been going on for years. We break down the honest pros and cons.", "content": "**Kibble** – Convenient, long shelf life, nutritionally balanced if you choose a quality brand. Negatives: heavily processed, some brands use poor-quality fillers.\n\n**Raw (BARF)** – Biologically Appropriate Raw Food mimics what dogs eat in the wild. Potential benefits include improved coat, digestion and energy. Negatives: bacterial contamination risk for dogs and owners, requires careful nutritional planning, more expensive.\n\n**What most vets recommend:** high-quality kibble as a baseline. If introducing raw, use a pre-made balanced formula from a reputable supplier rather than DIY, especially when starting out.\n\n**The middle ground:** many owners feed quality kibble topped with fresh ingredients – a spoonful of natural yoghurt, some cooked veg, or a raw meaty bone a few times a week. This adds variety and enrichment without the full commitment to raw.\n\nWhatever you choose, transition over 7–10 days to avoid digestive upset.", "category": "Nutrition", "author": "Admin", "likes": 18, "img": 2},
    {"title": "Foods That Are Toxic to Dogs", "summary": "Some everyday human foods are dangerous or even fatal to dogs. Every owner should know this list.", "content": "**Immediately dangerous:**\n- **Xylitol** – artificial sweetener found in sugar-free gum, some peanut butters, toothpaste. Causes rapid blood sugar crash and liver failure.\n- **Grapes and raisins** – can cause acute kidney failure. Even small amounts in some dogs.\n- **Onions, garlic, leeks and chives** – damage red blood cells, causing anaemia. Cooked, raw or powdered forms are all toxic.\n- **Chocolate** – contains theobromine. Dark chocolate is most dangerous; white chocolate least (still not safe).\n- **Macadamia nuts** – cause weakness, tremors and fever.\n- **Alcohol** – even small amounts cause serious harm.\n\n**Caution foods:**\n- Cooked bones – can splinter and cause internal injuries\n- Avocado – the flesh contains persin, toxic in large quantities\n- Corn on the cob – not toxic but a major choking/blockage risk\n- Nutmeg – toxic in large amounts\n- Raw dough – yeast expands in the stomach\n\n**If you suspect your dog has eaten something toxic:** call your vet or an animal poison helpline immediately. Time matters.", "category": "Nutrition", "author": "sarah_w", "likes": 67, "img": 3},
    {"title": "How Much Should You Feed Your Dog?", "summary": "Overfeeding is one of the leading causes of health problems in dogs. Getting portions right is simpler than you think.", "content": "Obesity in dogs has reached epidemic proportions – vets estimate that over 50% of dogs in the UK are overweight or obese. Extra weight puts strain on joints, heart, and respiratory system, and shortens life expectancy.\n\n**Start with the packet guidelines – but treat them as a starting point.** Feeding guides are based on ideal weight and average activity levels. Your dog may need more or less.\n\n**Factor in treats.** If your dog gets regular treats, reduce their main meal accordingly. Treats should make up no more than 10% of daily calorie intake.\n\n**The rib test.** You should be able to feel your dog's ribs easily without pressing hard, but not see them. If you have to press to find ribs, your dog is likely overweight.\n\n**Adjust based on body condition, not just weight.** A muscular dog and a fat dog can weigh the same. Learn to assess body condition score.\n\n**Feed twice a day.** Most adult dogs do best with two meals rather than one. It reduces hunger, prevents bloat in large breeds, and makes training easier.\n\n**Measure every meal.** 'Eyeballing' portions is the fastest route to an overweight dog.", "category": "Nutrition", "author": "mike_d", "likes": 23, "img": 4},
    {"title": "The Benefits of Omega-3 for Dogs", "summary": "Omega-3 fatty acids are one of the most well-researched supplements for dogs. Here is what the science says.", "content": "Omega-3 fatty acids – particularly EPA and DHA – have a remarkable range of benefits for dogs, backed by significant research.\n\n**Joint health.** Omega-3 has anti-inflammatory properties that can reduce joint pain and stiffness in dogs with arthritis. It is one of the few supplements with genuinely solid evidence behind it.\n\n**Skin and coat.** Dogs with dry, itchy or flaky skin often show significant improvement with omega-3 supplementation. It helps maintain the skin barrier and gives coats a healthy sheen.\n\n**Brain development.** DHA is critical for brain and eye development in puppies. Many quality puppy foods include it for this reason.\n\n**Heart health.** Studies suggest omega-3 may support cardiovascular health in dogs.\n\n**Best sources:** fish oil (look for products tested for heavy metals), salmon, sardines in water, and krill oil. Plant-based omega-3 (ALA from flaxseed) is less bioavailable for dogs.\n\n**Dosage:** follow the supplement's guidelines and speak to your vet, especially if your dog is on medication, as omega-3 can affect blood clotting at high doses.", "category": "Nutrition", "author": "emma_r", "likes": 17, "img": 5},
    {"title": "Homemade Dog Treats: Simple Healthy Recipes", "summary": "Homemade treats let you control exactly what goes into your dog's snacks. These three recipes are simple, healthy and dog-approved.", "content": "Making your own dog treats is easier than you think and gives you complete control over ingredients – ideal for dogs with allergies or sensitivities.\n\n**Peanut Butter and Banana Biscuits**\nIngredients: 1 ripe banana, 2 tbsp natural peanut butter (xylitol-free!), 100g oat flour\nMethod: Mash banana, mix in peanut butter, add flour until a dough forms. Roll to 1cm thickness, cut into shapes. Bake at 180°C for 15–20 minutes. Cool completely before serving.\n\n**Chicken and Sweet Potato Chews**\nIngredients: 1 chicken breast, 1 small sweet potato\nMethod: Slice sweet potato into 5mm strips. Slice chicken breast thinly. Bake at 100°C for 2–3 hours until dried and chewy. Store in the fridge for up to a week.\n\n**Frozen Yoghurt Bites**\nIngredients: Plain natural yoghurt (no sweeteners), blueberries or banana\nMethod: Mix fruit into yoghurt, spoon into an ice cube tray or silicone mould, freeze for 3+ hours. Great as a summer treat.\n\n**Storage:** homemade treats contain no preservatives. Baked treats keep for 3–5 days at room temperature or up to a month in the freezer.", "category": "Nutrition", "author": "sarah_w", "likes": 39, "img": 0},
    {"title": "How to Read a Dog Food Label", "summary": "Pet food labelling can be confusing and misleading. This guide will help you cut through the marketing and make better choices.", "content": "Walk into any pet shop and you'll be overwhelmed by packaging promising 'natural', 'premium', and 'grain-free' products. Here is how to actually evaluate what's inside.\n\n**Ingredients list.** Ingredients are listed by weight before cooking. 'Chicken' listed first sounds great, but water-heavy raw chicken loses much of its weight during processing. 'Chicken meal' (dried, concentrated chicken) may actually provide more protein even if listed lower.\n\n**Named protein sources.** Look for a specific named meat – 'chicken', 'salmon', 'lamb'. 'Meat and animal derivatives' is a catch-all that can include any animal parts.\n\n**Avoid foods where cereals appear multiple times** under different names (wheat, wheat flour, wheat gluten) – it's a way of disguising how much filler is present.\n\n**The AAFCO/FEDIAF statement.** Look for wording that the food is 'complete and balanced' and has been formulated to meet nutritional standards, or better yet, tested through feeding trials.\n\n**'Grain-free' is not automatically better.** Some dogs do better without grains, but grain-free diets have been linked to dilated cardiomyopathy in dogs in some studies. Discuss with your vet before switching.", "category": "Nutrition", "author": "Admin", "likes": 29, "img": 1},
    # ── Behaviour ─────────────────────────────────────────────────────────────
    {"title": "Understanding Dog Body Language", "summary": "Dogs communicate constantly through their bodies. Learning to read the signals transforms your relationship and prevents problems.", "content": "**The Tail** – A high, stiff wag signals arousal (not necessarily happiness). A low, loose wag indicates relaxation or submission. Tucked tail = fear.\n\n**The Eyes** – Soft, almond-shaped eyes mean a relaxed dog. Hard, round, unblinking eyes are a warning. Whale eye (whites showing) is a stress signal. Slow blinking is friendly.\n\n**The Ears** – Pinned flat against the head signals fear. Erect and angled forward signals alertness or arousal. Soft, slightly back signals contentment.\n\n**The Body** – A dog that crouches low is being submissive or fearful. A dog that leans forward is confident or assertive. Play bow (front end down, back up) is an invitation to play.\n\n**Calming signals** – Yawning, lip licking, sniffing the ground, shaking off, and turning away are signals your dog is uncomfortable or trying to de-escalate. Recognising these early prevents situations from escalating to growling or snapping.\n\n**The mouth** – A relaxed, slightly open mouth signals a happy dog. Tightly closed lips signal tension. A snarl is a warning – respect it rather than punishing it.", "category": "Behaviour", "author": "emma_r", "likes": 42, "img": 3},
    {"title": "Separation Anxiety: Causes and Solutions", "summary": "Separation anxiety is one of the most distressing behavioural problems for dogs and owners. Here is how to tackle it properly.", "content": "**What causes it?** A change in routine (return to work after lockdown is a classic trigger), rehoming, early weaning, or simply a strong attachment to one person.\n\n**Signs** – Destructive behaviour specifically when alone, excessive barking or howling, house soiling despite being toilet trained, pacing, excessive salivation, and shadowing you constantly when home.\n\n**What doesn't work:** getting another dog (often makes things worse), punishing the dog for destruction (they can't connect punishment with something that happened hours ago), or ignoring the problem hoping it resolves.\n\n**The science-backed approach:**\n\n**Systematic desensitisation** – Build up alone time second by second. Literally. Step outside for 10 seconds, come back. Work up slowly over days and weeks.\n\n**Independence exercises** – Teach your dog to settle on a mat while you're in the room. Build a positive association with alone time using food puzzles and enrichment.\n\n**Medication** – For moderate to severe cases, short-term medication prescribed by your vet can take the edge off anxiety enough for training to work.\n\n**Professional help** – A certified clinical animal behaviourist is the right person for serious cases. Your vet can refer you.", "category": "Behaviour", "author": "mike_d", "likes": 37, "img": 4},
    {"title": "Why Does My Dog Bark So Much?", "summary": "Excessive barking is one of the top complaints from dog owners and neighbours alike. Understanding the cause is the first step to solving it.", "content": "Dogs bark to communicate. Rather than simply stopping the bark, we need to understand what your dog is communicating.\n\n**Alert/alarm barking** – 'There is something outside!' Often triggered by passers-by, delivery drivers, or other dogs. Management: block sightlines, teach a 'thank you, enough' cue, use background noise to muffle triggers.\n\n**Demand barking** – 'Give me attention/food/a walk!' Dogs quickly learn that barking produces results. Solution: completely ignore the bark, reward the moment they're quiet. Consistency is everything.\n\n**Boredom/frustration barking** – Under-exercised or under-stimulated dogs bark more. Increase physical exercise and mental enrichment (sniff walks, food puzzles, training).\n\n**Separation-related barking** – See our article on separation anxiety for a full guide.\n\n**Fear or territorial barking** – More intense barking, often accompanied by other warning signals. Requires careful behaviour modification, potentially with professional support.\n\n**What doesn't work:** shouting at your dog to be quiet (you've joined in the barking!), punishment-based devices like shock collars (suppress the symptom, not the cause, and damage trust).", "category": "Behaviour", "author": "sarah_w", "likes": 31, "img": 5},
    {"title": "Socialising Your Puppy: The Critical Window", "summary": "The first 16 weeks of a puppy's life are the most important for shaping their future behaviour. Here is how to use that window wisely.", "content": "The socialisation period runs roughly from 3 to 16 weeks old. During this time, puppies are uniquely primed to accept new experiences as normal and safe. After this window closes, novel things become inherently suspicious.\n\n**What to expose them to:**\n- Different types of people (children, men with beards, people in high-vis, cyclists)\n- Different surfaces (grass, gravel, metal grilles, sand)\n- Different sounds (traffic, thunderstorms, hoovers, fireworks – use a sound CD at low volume)\n- Other animals (cats, livestock, other dogs of all sizes)\n- Being handled (ears, paws, mouth – essential for vet visits)\n\n**Quality over quantity.** Don't flood your puppy with experiences. Expose them to things at a comfortable distance and let them investigate at their own pace. Watch for calming signals and give them the option to retreat.\n\n**The vaccination dilemma.** Many puppies can't go on the ground in public before their vaccinations are complete. Carry them in public, arrange puppy classes (reputable ones require proof of first vaccination), and visit the homes of vaccinated dogs.\n\n**Ongoing socialisation.** The window may close at 16 weeks, but socialisation should never stop. Keep exposing your dog to new experiences throughout their life.", "category": "Behaviour", "author": "mike_d", "likes": 45, "img": 0},
    {"title": "Understanding and Preventing Resource Guarding", "summary": "Resource guarding is a normal dog behaviour that can become dangerous if not managed correctly. Here is what every owner needs to know.", "content": "Resource guarding is a dog's way of communicating 'this is mine and I'm worried you'll take it.' It is a completely normal evolutionary behaviour – in the wild, a dog that didn't guard its food didn't eat.\n\n**What can be guarded:** food, toys, chews, sleeping spots, water bowls, and even people.\n\n**Warning signs (mild to severe):** eating faster when you approach, stiffening, hard stare, whale eye, low growl, snarl, snap, bite.\n\n**Never punish a growl.** A growl is communication. Punishing it removes the warning without removing the discomfort that caused it. You end up with a dog that bites without warning.\n\n**The swap and trade approach.** Teach your dog that your approach near their resources predicts good things. Drop high-value treats near them as you walk past. Practice trading: offer a treat to take the item, give it back. This teaches that you approaching means good things, not loss.\n\n**Management first.** While you're working on behaviour modification, manage the environment: feed your dog in a quiet space where they won't be disturbed, put high-value chews away when children are around.\n\n**Seek professional help** for moderate to severe cases, especially in households with children.", "category": "Behaviour", "author": "emma_r", "likes": 28, "img": 1},
    {"title": "Why Dogs Chew and How to Redirect It", "summary": "Chewing is a natural and necessary dog behaviour. The key is channelling it towards the right things.", "content": "Chewing releases endorphins, relieves stress, keeps jaws strong, and helps clean teeth. Trying to stop your dog chewing entirely is both impossible and counterproductive. The goal is to redirect it.\n\n**Why dogs chew the wrong things:**\n- Boredom or insufficient exercise\n- Anxiety (especially separation-related)\n- Teething in puppies (up to 6 months)\n- Lack of appropriate outlets\n- Opportunity – items left within reach\n\n**Management comes first.** Don't leave shoes, children's toys, or phone chargers within reach. Baby gates, crates, and closed doors are your friends while your dog is young or new to your home.\n\n**Provide plenty of appropriate outlets:**\n- Bully sticks, deer antlers, raw bones\n- Rubber chew toys (Kong, Nylabone)\n- Stuffed Kongs (fill with peanut butter or wet food and freeze)\n- Cardboard boxes – many dogs love to shred them\n\n**Interrupt and redirect, don't just punish.** If you catch your dog chewing something inappropriate, calmly remove the item without drama and offer an appropriate chew. Reward them when they engage with it.", "category": "Behaviour", "author": "Admin", "likes": 20, "img": 2},
    # ── Lifestyle ─────────────────────────────────────────────────────────────
    {"title": "The Best Dog-Friendly Hiking Tips", "summary": "Exploring the outdoors with your dog is one of life's great pleasures. Here are our tips for a safe and enjoyable adventure.", "content": "**Before you go** – Check the trail permits dogs and whether they need to be on lead. Research the distance and terrain; a 10km mountain hike may suit a young Husky but not a senior Pug.\n\n**What to pack** – Collapsible water bowl and enough water for both of you, high-value snacks, poop bags (leave no trace), a tick remover, dog-safe first aid supplies, and their ID tag.\n\n**On the trail** – Let your dog sniff freely; this is mentally tiring in the best way. Take regular breaks, especially in warm weather. Watch for excessive panting, lagging behind, or seeking shade – all signs of overheating.\n\n**Hot weather caution** – Paw pads can burn on hot ground. If the tarmac is too hot for your bare hand for more than five seconds, it's too hot for paw pads.\n\n**After the hike** – Check paws for cuts, thorns, or foreign objects. Thoroughly check the coat for ticks, especially around ears, between toes, groin, and armpits. A tired dog is the best kind of dog.", "category": "Lifestyle", "author": "sarah_w", "likes": 29, "img": 4},
    {"title": "Travelling with Your Dog: A Stress-Free Guide", "summary": "Whether by car, train or plane, travelling with a dog requires planning. Here is how to make every journey as smooth as possible.", "content": "**By car** – Dogs must be restrained under UK law. A crash-tested harness, secured crate, or dog guard are the main options. Never let your dog travel loose or with their head out of the window. For longer journeys, stop every two hours for water, a toilet break, and a stretch.\n\n**Car sickness** – Some dogs vomit from motion sickness; others show it through drooling and restlessness. Travel on an empty stomach, keep the car cool and ventilated, and face your dog forward if possible. Medication from your vet can help in severe cases.\n\n**By train** – Most UK rail operators allow dogs free of charge, though rules vary. Dogs should be on a lead at all times and must not occupy seats during busy periods.\n\n**Holidays** – An increasing number of UK holiday cottages, hotels and campsites are dog-friendly. Always check the specific rules (lead requirements, no-go areas) before you arrive.\n\n**Abroad** – Travelling to EU countries requires a pet passport or AHC health certificate, microchip, up-to-date rabies vaccination, and – when returning to the UK – a tapeworm treatment timed to the return journey.", "category": "Lifestyle", "author": "emma_r", "likes": 34, "img": 5},
    {"title": "Indoor Games to Keep Your Dog Entertained", "summary": "Rainy days don't have to mean a bored dog. These indoor games provide serious mental and physical stimulation.", "content": "Mental stimulation can be just as tiring as physical exercise – sometimes more so. These games are perfect for bad weather days, recovery periods, or dogs that can't exercise freely.\n\n**The muffin tin game.** Place treats in some cups of a muffin tin and cover all cups with tennis balls. Your dog has to figure out which ones are hiding the prize.\n\n**Hide and seek.** Ask your dog to sit-stay, hide somewhere in the house, then call them. Reward enthusiastically when they find you. Graduate to hiding treats or toys around the house.\n\n**Nose work.** Hide a specific scented item in increasingly difficult locations and let your dog use their nose to find it. Dogs have up to 300 million olfactory receptors – give them a workout.\n\n**Trick training.** Ten minutes of learning a new trick like 'spin', 'wave', or 'tidy your toys' provides tremendous mental stimulation and deepens your bond.\n\n**Stuffed Kongs.** Fill with a mix of kibble, peanut butter, banana, and yoghurt, then freeze. A frozen Kong can occupy a dog for 20–30 minutes.\n\n**Cardboard destruction box.** Put treats inside a cardboard box stuffed with scrunched paper and let your dog go to town. Embrace the mess.", "category": "Lifestyle", "author": "Admin", "likes": 26, "img": 0},
    {"title": "How to Choose the Right Dog for Your Lifestyle", "summary": "The wrong breed or age match is one of the leading reasons dogs are surrendered to rescues. Here is how to get it right from the start.", "content": "Every dog deserves a home matched to their needs, and every owner deserves a dog suited to their lifestyle. Taking time to get this right prevents heartbreak on both sides.\n\n**Honest self-assessment.** How much time can you genuinely commit to exercise per day – not your ideal, your realistic average? Do you have outdoor space? Do you have children, cats, or other dogs? How much space do you have at home? Are you home most of the day or out for long hours?\n\n**Breed traits are real.** A working Husky needs hours of exercise daily. A Border Collie needs a job or it will create its own. A Basset Hound will follow its nose into traffic given the chance. Research the group your chosen breed belongs to and what they were bred for.\n\n**Age matters.** Puppies are enormous work – think new baby level. Adolescents (6 months to 2 years) are often overlooked and may have some habits to work on but also have great long-term potential. Adult dogs often arrive house-trained and with a known personality.\n\n**Rescue vs breeder.** There is no wrong answer if done responsibly. A reputable rescue will match you carefully. A responsible breeder health-tests their dogs and offers lifetime support.", "category": "Lifestyle", "author": "mike_d", "likes": 38, "img": 1},
    {"title": "Setting Up the Perfect Dog-Friendly Home", "summary": "A few thoughtful adjustments can make your home safer, more comfortable, and more enriching for your dog.", "content": "**Safety first.** Get down to your dog's level and look for hazards: trailing cables, toxic houseplants (lilies, poinsettia, aloe vera), accessible bins (especially kitchen bins with food waste), medications left on surfaces, and small objects that could be swallowed.\n\n**Toxic plants to remove:** lilies (especially dangerous for cats but harmful to dogs too), daffodil bulbs, azalea, rhododendron, sago palm, autumn crocus.\n\n**Their own space.** Every dog needs a safe haven where they won't be disturbed – a crate, a dog bed in a quiet corner, or a specific room. Teach children to respect this space absolutely.\n\n**Flooring.** Slippery floors are a serious issue for older dogs and some breeds. Yoga mats, carpet runners, and non-slip socks for dogs can all help.\n\n**Garden security.** Check your fence thoroughly for gaps – a determined dog can squeeze through surprisingly small spaces. Check the base of fences, gates, and any gaps under decking or sheds.\n\n**Enrichment.** Make your home interesting for your dog: scatter feeding in the garden, sniff boxes, chews available at appropriate times. A house that engages your dog's senses is one where they're less likely to find their own entertainment.", "category": "Lifestyle", "author": "sarah_w", "likes": 22, "img": 2},
    {"title": "Dog Sports: Agility, Flyball and Canicross", "summary": "Dog sports are a fantastic way to exercise your dog's body and mind while building an extraordinary bond. Could you and your dog be champions?", "content": "Dog sports have exploded in popularity and there truly is something for every dog and owner combination.\n\n**Agility** – Dogs navigate a timed obstacle course including jumps, tunnels, weave poles, and seesaws guided by their handler. Fast, exciting, and brilliant for building communication. Border Collies dominate at elite level, but every breed and mix can participate at club level.\n\n**Flyball** – A relay race where dogs jump hurdles, hit a box that launches a ball, catch it, and race back over the hurdles. Incredibly fast-paced and hugely popular. Ball-obsessed dogs of any breed tend to love it.\n\n**Canicross** – Cross-country running with your dog attached to you via a bungee lead and waist belt. Your dog learns to pull you (in a controlled way!) while you run together. Perfect for active owners with energetic dogs.\n\n**Scentwork/Nosework** – Dogs search for a specific scent hidden in boxes, vehicles, or outdoor environments. Low-impact, suitable for all ages and fitness levels, and deeply satisfying for the dog.\n\n**Rally Obedience** – Like obedience but more relaxed; you navigate a course with your dog completing exercises at each station. Great for dogs building confidence.\n\n**How to get started:** search for local clubs, go and watch before committing, and check your dog is physically suitable (vet check advised before high-impact sports).", "category": "Lifestyle", "author": "emma_r", "likes": 30, "img": 3},
]

_SEED_DOGS = [
    {"name": "buddy",   "gender": "Male",   "age": "3", "size": "Large",  "good_with": ["Kids", "Dogs", "Cats"], "description": "Buddy is a gorgeous 3-year-old Golden Retriever with a heart of gold. He loves everyone he meets and has never met a stranger. Fully house trained, great on the lead, and knows his basic commands. Surrendered when his owner moved abroad — he is looking for a loving forever home.", "greeting": "Hi, I'm Buddy! I love fetch, belly rubs, and stealing socks. I promise to be your best friend forever!", "owner": "Admin", "img": 0},
    {"name": "luna",    "gender": "Female", "age": "2", "size": "Large",  "good_with": ["Dogs"], "description": "Luna is an energetic and intelligent 2-year-old Husky who needs an experienced owner who understands the breed. Stunning to look at and a joy to be around once exercised. Needs 2+ hours of activity daily and a secure garden. High prey drive — not suitable for homes with cats.", "greeting": "Howwooo! I'm Luna and I have enough energy for the both of us. Take me hiking and I'll love you forever.", "owner": "emma_r", "img": 1},
    {"name": "charlie", "gender": "Male",   "age": "5", "size": "Small",  "good_with": ["Kids", "Dogs", "Cats"], "description": "Charlie is a sweet, gentle 5-year-old Beagle who adores company. Great with children and other pets — the perfect family dog. Loves sniffing on long walks. Fully vaccinated, neutered, and microchipped. A real gem looking for his forever sofa.", "greeting": "Hi there! I'm Charlie. I might follow my nose into trouble sometimes, but I always come back for cuddles.", "owner": "mike_d", "img": 2},
    {"name": "max",     "gender": "Male",   "age": "1", "size": "Large",  "good_with": ["Dogs"], "description": "Max is a bouncy 1-year-old Labrador full of life and mischief. Still very much a puppy at heart, he needs a home that can continue his training. Knows sit, down and is working on recall. Would thrive with an active family.", "greeting": "HELLO! Is it walkies time? What about now? I'm Max and every moment is the BEST MOMENT EVER!", "owner": "Admin", "img": 3},
    {"name": "rosie",   "gender": "Female", "age": "4", "size": "Medium", "good_with": ["Kids", "Dogs", "Cats"], "description": "Rosie is a calm and affectionate 4-year-old Cocker Spaniel who loves being close to her people. Well-mannered, great in the car, fantastic with children and animals. Previously a therapy dog with impeccable manners.", "greeting": "Hello, lovely. I'm Rosie. I'll sit nicely, I won't bark, and I'll look at you with these eyes until you give me a biscuit.", "owner": "sarah_w", "img": 4},
    {"name": "pepper",  "gender": "Female", "age": "6", "size": "Medium", "good_with": ["Kids", "Cats"], "description": "Pepper is a sophisticated 6-year-old Standard Poodle with a hilarious personality. Incredibly smart, quick to learn, trained in agility, and hypoallergenic — wonderful for families with allergies. Rehomed due to owner's health problems.", "greeting": "Bonjour! I'm Pepper. I'm smart, I'm stylish, and I'm probably already training you without you knowing.", "owner": "mike_d", "img": 5},
    {"name": "bella",   "gender": "Female", "age": "2", "size": "Medium", "good_with": ["Dogs"], "description": "Bella is a whip-smart 2-year-old Border Collie with incredible energy and focus. She needs a working home or one committed to dog sports — agility or flyball would be ideal. She is not a sofa dog, but in the right hands she is extraordinary.", "greeting": "I'm Bella. I'm watching you. I'm always watching. Throw the ball.", "owner": "emma_r", "img": 0},
    {"name": "oscar",   "gender": "Male",   "age": "4", "size": "Large",  "good_with": ["Kids", "Dogs"], "description": "Oscar is a loyal and confident 4-year-old German Shepherd looking for an experienced handler. He is well-socialised with dogs and children but can be selective with strangers — he just needs time to trust. He's obedient, protective, and deeply devoted once he bonds.", "greeting": "I'm Oscar. I'll guard your house, herd your family, and lie at your feet. I just need someone worthy of my loyalty.", "owner": "Admin", "img": 1},
    {"name": "daisy",   "gender": "Female", "age": "3", "size": "Small",  "good_with": ["Kids", "Cats"], "description": "Daisy is an adorable 3-year-old Dachshund with a personality three times her size. She loves cuddles, sunny spots, and going on adventures at her own pace. Good with gentle children and cats. Not great with boisterous dogs.", "greeting": "I'm Daisy. Small in size, massive in personality. I'll expect the sofa and approximately 80% of the duvet.", "owner": "sarah_w", "img": 2},
    {"name": "milo",    "gender": "Male",   "age": "2", "size": "Large",  "good_with": ["Kids", "Dogs"], "description": "Milo is a playful and affectionate 2-year-old Boxer who doesn't know his own strength. He loves people — especially children — and adores other dogs. He needs patient owners who will continue his training. His enthusiasm for life is utterly infectious.", "greeting": "HI HI HI HI! I'm Milo! Are you my new family? I'm going to love you SO much. Fair warning: I lean.", "owner": "mike_d", "img": 3},
    {"name": "coco",    "gender": "Female", "age": "5", "size": "Small",  "good_with": ["Kids", "Dogs", "Cats"], "description": "Coco is a charming 5-year-old Pug looking for a quiet, comfortable home. She is gentle, affectionate, and gets along with absolutely everyone. She does have the typical brachycephalic breathing quirks so needs walks in cool conditions and no strenuous exercise.", "greeting": "I'm Coco. I snore, I snort, and I'll steal your heart. I require two walks a day, three meals of attention, and full sofa rights.", "owner": "sarah_w", "img": 4},
    {"name": "theo",    "gender": "Male",   "age": "3", "size": "Large",  "good_with": ["Kids", "Dogs"], "description": "Theo is a confident, friendly 3-year-old Labrador who is an absolute pleasure to walk and live with. House trained, travels well, and has basic obedience. His previous family is emigrating — their loss could be your gain.", "greeting": "I'm Theo. I'm the Labrador of your dreams: food motivated (who isn't?), easy to train, and reliably wonderful.", "owner": "Admin", "img": 5},
    {"name": "poppy",   "gender": "Female", "age": "1", "size": "Large",  "good_with": ["Kids", "Dogs", "Cats"], "description": "Poppy is a beautiful 1-year-old Golden Retriever with boundless energy and love to match. She is still in early training and needs a committed owner. Gets along brilliantly with children, other dogs, and even the resident cats at her foster home.", "greeting": "I'm Poppy! I don't know what personal space means yet but I'm working on it. In the meantime: cuddles?", "owner": "emma_r", "img": 0},
    {"name": "loki",    "gender": "Male",   "age": "3", "size": "Large",  "good_with": ["Dogs"], "description": "Loki is a handsome and mischievous 3-year-old Husky. He is affectionate with his people but an absolute Houdini — any home must have Fort Knox-level fencing. Needs 2+ hours of exercise daily and mental stimulation to prevent chaos.", "greeting": "I'm Loki. God of mischief, escape artist, and surprisingly good at making friends. (The fence damage was definitely someone else.)", "owner": "Admin", "img": 1},
    {"name": "nala",    "gender": "Female", "age": "4", "size": "Small",  "good_with": ["Kids", "Dogs", "Cats"], "description": "Nala is a sweet-natured 4-year-old Beagle with a nose that never stops working. She is calm indoors, great with other animals, and loves children. Needs a secure garden — her nose will lead her anywhere if given the chance.", "greeting": "I'm Nala. I'll find every treat you've ever lost, locate the squirrel three gardens over, and snuggle you like it's my profession.", "owner": "mike_d", "img": 2},
    {"name": "rex",     "gender": "Male",   "age": "7", "size": "Large",  "good_with": ["Kids", "Dogs"], "description": "Rex is a calm, dignified 7-year-old German Shepherd looking for a quiet forever home to retire in. He has given years as a working assistance dog and now deserves a comfortable life with walks, routine, and genuine love. Excellent with children.", "greeting": "I'm Rex. I've done my duty. Now I'd like a warm bed, steady walks, and someone to appreciate me. I've earned it.", "owner": "sarah_w", "img": 3},
    {"name": "ruby",    "gender": "Female", "age": "2", "size": "Medium", "good_with": ["Kids", "Dogs", "Cats"], "description": "Ruby is a lively 2-year-old Cocker Spaniel with a wagging tail that never stops. She is eager to please, quick to learn, and absolutely loves water. A family looking for an active companion dog will find her perfect.", "greeting": "I'm Ruby! I am ALWAYS happy to see you. ALWAYS. Morning, noon, or night — pure joy, every single time.", "owner": "Admin", "img": 4},
    {"name": "archie",  "gender": "Male",   "age": "4", "size": "Medium", "good_with": ["Kids", "Cats"], "description": "Archie is a distinguished 4-year-old Standard Poodle who is as clever as he is handsome. Trained to a high level and surprisingly energetic for his composed demeanour. Hypoallergenic. Not always keen on other dogs but wonderful with children and cats.", "greeting": "I'm Archie. I prefer the term 'distinguished' to 'posh'. I have excellent manners and I expect the same in return.", "owner": "emma_r", "img": 5},
    {"name": "molly",   "gender": "Female", "age": "6", "size": "Medium", "good_with": ["Dogs"], "description": "Molly is a focused and intelligent 6-year-old Border Collie who needs a job to be happy. She excels at agility and would love to continue training. She is not suitable for a home with young children or cats, but with the right active owner she is an extraordinary companion.", "greeting": "I'm Molly. I've been herding the family cat for six years and I need a proper job. Also, the cat needs a break.", "owner": "mike_d", "img": 0},
    {"name": "bruno",   "gender": "Male",   "age": "5", "size": "Large",  "good_with": ["Kids", "Dogs"], "description": "Bruno is a big-hearted 5-year-old Boxer who loves nothing more than people and play. He is well-trained, travels well, and is brilliant with children. A bit selective with unknown dogs but fine with dogs he knows. He needs an active family who can give him the exercise his breed demands.", "greeting": "I'm Bruno. I will sit on you. This is non-negotiable. I'm a lap dog, I've just been misinformed about my size.", "owner": "sarah_w", "img": 1},
    {"name": "skye",    "gender": "Female", "age": "2", "size": "Small",  "good_with": ["Cats"], "description": "Skye is a petite and independent 2-year-old Dachshund who prefers the company of cats to most dogs. She is quiet, clean, and surprisingly well-behaved for her age. Ideal for a calmer household without boisterous animals or very young children.", "greeting": "I'm Skye. I'm a very serious dog with important napping to do. The cat is my best friend. I judge others.", "owner": "Admin", "img": 2},
    {"name": "finn",    "gender": "Male",   "age": "2", "size": "Large",  "good_with": ["Kids", "Dogs"], "description": "Finn is an enthusiastic 2-year-old Labrador who lives life at full volume. He is in training and improving daily — his foster family is thrilled with his progress. He needs someone who can channel his energy positively. Best in a house with a garden.", "greeting": "I'm Finn! I knocked over the Christmas tree but I'm VERY sorry. Mostly sorry. I've been working on my sit though!", "owner": "emma_r", "img": 3},
    {"name": "tilly",   "gender": "Female", "age": "3", "size": "Large",  "good_with": ["Kids", "Dogs", "Cats"], "description": "Tilly is a gentle 3-year-old Golden Retriever who radiates calm happiness. She is the dog everyone wants — gentle, obedient, good with everyone, low drama. She was surrendered by an elderly owner who could no longer manage the exercise requirements.", "greeting": "Hello. I'm Tilly. I am simply a very good dog. That's it. That's the greeting.", "owner": "mike_d", "img": 4},
    {"name": "zeus",    "gender": "Male",   "age": "4", "size": "Large",  "good_with": ["Dogs"], "description": "Zeus is a powerful and striking 4-year-old Husky who needs a highly experienced owner. He is challenging, intelligent, and relentlessly energetic. He is not for first-time owners. For the right active, experienced owner, he will be the adventure partner of a lifetime.", "greeting": "I'm Zeus. I have reviewed your application. I'll be in touch. (Bring snacks to the interview.)", "owner": "sarah_w", "img": 5},
    {"name": "penny",   "gender": "Female", "age": "6", "size": "Small",  "good_with": ["Kids", "Dogs", "Cats"], "description": "Penny is a calm and loving 6-year-old Beagle looking for a quiet home to enjoy her golden years. She is well past her chaotic puppy phase and is now a relaxed, affectionate companion who enjoys gentle walks and long naps. Wonderful with children and everyone she meets.", "greeting": "I'm Penny. I've done the energetic thing. I'm now exclusively in my soft life era and I'm looking for someone to share it with.", "owner": "Admin", "img": 0},
    {"name": "beau",    "gender": "Male",   "age": "1", "size": "Large",  "good_with": ["Dogs"], "description": "Beau is a stunning 1-year-old German Shepherd puppy who is all potential and personality. He is bright, engaged, and learning fast. He needs an experienced owner committed to his development. With the right guidance he will be an exceptional dog.", "greeting": "I'm Beau. I'm very impressive for my age. My foster family says so constantly. I'm choosing to believe them.", "owner": "emma_r", "img": 1},
    {"name": "bonnie",  "gender": "Female", "age": "7", "size": "Medium", "good_with": ["Kids", "Cats"], "description": "Bonnie is a gentle 7-year-old Cocker Spaniel looking for a quiet retirement home. She is low-maintenance, clean, and deeply loving. Gets on beautifully with cats and gentle children. Was reluctantly rehomed when her owner moved into care.", "greeting": "I'm Bonnie. Seven years of good behaviour and I still ended up here. I deserve every biscuit you own.", "owner": "mike_d", "img": 4},
    {"name": "dexter",  "gender": "Male",   "age": "3", "size": "Medium", "good_with": ["Kids", "Dogs", "Cats"], "description": "Dexter is a cheerful, outgoing 3-year-old Poodle mix with boundless enthusiasm for life. He is friendly with everyone and everything, quick to learn new tricks, and one of those dogs that genuinely makes everyone smile. Hypoallergenic coat is a bonus.", "greeting": "I'm Dexter! I've met three people today and they're all my best friends now. You're next, I can tell.", "owner": "sarah_w", "img": 5},
    {"name": "willow",  "gender": "Female", "age": "1", "size": "Medium", "good_with": ["Dogs"], "description": "Willow is a bright-eyed 1-year-old Border Collie puppy with all the potential in the world and the energy to match. She needs a dedicated owner who wants to do dog sports or working activities. Given direction and stimulation, she will be unstoppable.", "greeting": "I'm Willow. I'm very smart. I've already trained my foster carer. I'm told this is 'not the goal'. I disagree.", "owner": "Admin", "img": 0},
    {"name": "tank",    "gender": "Male",   "age": "6", "size": "Large",  "good_with": ["Kids", "Dogs"], "description": "Tank is a 6-year-old Boxer whose name is misleading — he is a gentle giant with impeccable manners. He loves children, gets on well with calm dogs, and is happiest when he's with his people. He does snore quite loudly. This is non-negotiable.", "greeting": "I'm Tank. The name was someone else's idea. I am a sensitive soul who wants cuddles and a garden to zoom around in occasionally.", "owner": "emma_r", "img": 1},
]


def _seed_upload_and_insert_posts(start, end):
    for i in range(start, min(end, len(_SEED_POSTS))):
        p = _SEED_POSTS[i]
        public_id = f"post_img_{1001 + i}"
        result = cloudinary.uploader.upload(
            _POST_IMGS[p["img"]], public_id=public_id, resource_type="image")
        img_path = result["secure_url"]
        now = datetime.now()
        mongo.db.posts.insert_one({
            "title": p["title"], "summary": p["summary"],
            "content": p["content"], "category": p["category"],
            "author": p["author"],
            "created": now.timetuple(), "create_date": now.strftime("%d/%m/%Y"),
            "create_time": now.strftime("%H:%M"), "update_date": "",
            "likes": p["likes"], "img_id": 1001 + i,
            "img_filename": f"{public_id}.webp", "img_path": img_path,
        })


def _seed_upload_and_insert_dogs(start, end):
    for i in range(start, min(end, len(_SEED_DOGS))):
        d = _SEED_DOGS[i]
        public_id = f"dog_img_{2001 + i}"
        result = cloudinary.uploader.upload(
            _DOG_IMGS[d["img"]], public_id=public_id, resource_type="image")
        img_path = result["secure_url"]
        owner = mongo.db.users.find_one({"username": d["owner"]})
        now = datetime.now()
        mongo.db.dogs.insert_one({
            "name": d["name"], "gender": d["gender"], "age": d["age"],
            "size": d["size"], "good_with": d["good_with"],
            "description": d["description"], "greeting": d["greeting"],
            "created": now.timetuple(), "owner_id": owner["_id"],
            "img_id": 2001 + i,
            "img_filename": f"{public_id}.webp", "img_path": img_path,
        })


@app.route("/seed/woof-seed-2026/1")
def seed_step1():
    for col in ["users", "categories", "posts", "dogs", "messages"]:
        mongo.db[col].drop()
    mongo.db.categories.insert_many([{"category_name": c} for c in ["Training", "Health", "Nutrition", "Behaviour", "Lifestyle"]])
    mongo.db.users.insert_many([
        {"username": "Admin",   "password": generate_password_hash("Password1!"), "email": "admin@woofdotcom.com", "fname": "Admin", "lname": "User",    "phone": "000-000-0000", "about": "Site administrator and dog lover.",                            "liked_posts": [], "adoption_requests": []},
        {"username": "sarah_w", "password": generate_password_hash("Password1!"), "email": "sarah@example.com",   "fname": "Sarah", "lname": "Wilson",  "phone": "555-101-2020", "about": "Proud owner of two golden retrievers. Dog trainer for 8 years.", "liked_posts": [], "adoption_requests": []},
        {"username": "mike_d",  "password": generate_password_hash("Password1!"), "email": "mike@example.com",    "fname": "Mike",  "lname": "Davies",  "phone": "555-303-4040", "about": "Vet nurse and passionate advocate for dog adoption.",            "liked_posts": [], "adoption_requests": []},
        {"username": "emma_r",  "password": generate_password_hash("Password1!"), "email": "emma@example.com",    "fname": "Emma",  "lname": "Roberts", "phone": "555-505-6060", "about": "Lifelong dog owner. Love hiking with my huskies!",              "liked_posts": [], "adoption_requests": []},
    ])
    _seed_upload_and_insert_posts(0, 5)
    return "Step 1/12 done. Visit /seed/woof-seed-2026/2"

@app.route("/seed/woof-seed-2026/2")
def seed_step2():
    _seed_upload_and_insert_posts(5, 10)
    return "Step 2/12 done. Visit /seed/woof-seed-2026/3"

@app.route("/seed/woof-seed-2026/3")
def seed_step3():
    _seed_upload_and_insert_posts(10, 15)
    return "Step 3/12 done. Visit /seed/woof-seed-2026/4"

@app.route("/seed/woof-seed-2026/4")
def seed_step4():
    _seed_upload_and_insert_posts(15, 20)
    return "Step 4/12 done. Visit /seed/woof-seed-2026/5"

@app.route("/seed/woof-seed-2026/5")
def seed_step5():
    _seed_upload_and_insert_posts(20, 25)
    return "Step 5/12 done. Visit /seed/woof-seed-2026/6"

@app.route("/seed/woof-seed-2026/6")
def seed_step6():
    _seed_upload_and_insert_posts(25, 30)
    return "Step 6/12 done. Visit /seed/woof-seed-2026/7"

@app.route("/seed/woof-seed-2026/7")
def seed_step7():
    _seed_upload_and_insert_dogs(0, 5)
    return "Step 7/12 done. Visit /seed/woof-seed-2026/8"

@app.route("/seed/woof-seed-2026/8")
def seed_step8():
    _seed_upload_and_insert_dogs(5, 10)
    return "Step 8/12 done. Visit /seed/woof-seed-2026/9"

@app.route("/seed/woof-seed-2026/9")
def seed_step9():
    _seed_upload_and_insert_dogs(10, 15)
    return "Step 9/12 done. Visit /seed/woof-seed-2026/10"

@app.route("/seed/woof-seed-2026/10")
def seed_step10():
    _seed_upload_and_insert_dogs(15, 20)
    return "Step 10/12 done. Visit /seed/woof-seed-2026/11"

@app.route("/seed/woof-seed-2026/11")
def seed_step11():
    _seed_upload_and_insert_dogs(20, 25)
    return "Step 11/12 done. Visit /seed/woof-seed-2026/12"

@app.route("/seed/woof-seed-2026/12")
def seed_step12():
    _seed_upload_and_insert_dogs(25, 30)
    return "ALL DONE! 30 posts and 30 dogs loaded. Come back to remove the seed routes."


@app.route("/seed/woof-seed-2026/1")
def seed_step1():
    """Step 1: drop all collections, create users + categories + posts 1-3."""
    for col in ["users", "categories", "posts", "dogs", "messages"]:
        mongo.db[col].drop()
    mongo.db.categories.insert_many([
        {"category_name": c} for c in
        ["Training", "Health", "Nutrition", "Behaviour", "Lifestyle"]
    ])
    mongo.db.users.insert_many([
        {"username": "Admin",   "password": generate_password_hash("Password1!"), "email": "admin@woofdotcom.com", "fname": "Admin", "lname": "User",    "phone": "000-000-0000", "about": "Site administrator and dog lover.",                       "liked_posts": [], "adoption_requests": []},
        {"username": "sarah_w", "password": generate_password_hash("Password1!"), "email": "sarah@example.com",   "fname": "Sarah", "lname": "Wilson",  "phone": "555-101-2020", "about": "Proud owner of two golden retrievers. Dog trainer for 8 years.", "liked_posts": [], "adoption_requests": []},
        {"username": "mike_d",  "password": generate_password_hash("Password1!"), "email": "mike@example.com",    "fname": "Mike",  "lname": "Davies",  "phone": "555-303-4040", "about": "Vet nurse and passionate advocate for dog adoption.",           "liked_posts": [], "adoption_requests": []},
        {"username": "emma_r",  "password": generate_password_hash("Password1!"), "email": "emma@example.com",    "fname": "Emma",  "lname": "Roberts", "phone": "555-505-6060", "about": "Lifelong dog owner. Love hiking with my huskies!",             "liked_posts": [], "adoption_requests": []},
    ])
    _insert_post({"title": "5 Essential Commands Every Dog Should Know", "summary": "Teaching your dog basic commands is the foundation of a happy life together. Here are the five commands you should start with.", "content": "Starting with the basics is always the best approach when training your dog.\n\n**1. Sit** – Hold a treat close to your dog's nose, move your hand up so their bottom lowers, say 'Sit' and reward.\n\n**2. Stay** – Ask your dog to sit, open your palm and say 'Stay', take steps back and reward if they hold.\n\n**3. Come** – With a leash on, crouch down and gently pull while saying 'Come'. Reward generously on arrival.\n\n**4. Down** – Hold a treat in a closed fist at their snout, move it to the floor. Their body will follow.\n\n**5. Leave it** – Show one treat-filled fist, say 'Leave it', and when they stop trying reward from the other hand.\n\nConsistency is key. Short frequent sessions beat long infrequent ones!", "category": "Training", "author": "sarah_w", "likes": 24, "img_url": "https://images.dog.ceo/breeds/retriever-golden/n02099601_3004.jpg", "public_id": "post_img_1001"})
    _insert_post({"title": "How to Spot Signs of a Healthy Dog", "summary": "Regular health checks at home can help you catch problems early. Learn what to look for to keep your dog in top shape.", "content": "As a dog owner, you're your pet's first line of defence.\n\n**Eyes** – Bright and clear with no persistent discharge.\n\n**Ears** – Clean and odour-free. Head shaking can indicate infection.\n\n**Coat** – Shiny and smooth. Dull fur can signal nutritional deficiencies.\n\n**Weight** – Feel ribs without pressing hard, but not see them.\n\n**Gums** – Pink and moist. Pale or white gums are a veterinary emergency.\n\n**Energy** – Know your dog's baseline. Sudden lethargy needs attention.\n\n**Bathroom** – Regular firm stools are a good sign. Diarrhoea lasting 24+ hours needs a vet.\n\nA monthly at-home check keeps you in tune with your dog's health!", "category": "Health", "author": "mike_d", "likes": 31, "img_url": "https://images.dog.ceo/breeds/labrador/n02099712_4323.jpg", "public_id": "post_img_1002"})
    _insert_post({"title": "Raw vs Kibble: What's Best for Your Dog?", "summary": "The debate between raw feeding and kibble has been going on for years. We break down the pros and cons of each approach.", "content": "Choosing how to feed your dog is one of the most debated topics in the dog community.\n\n**Kibble** – Convenient, long shelf life, nutritionally balanced if you choose a quality brand. Some use low-quality fillers.\n\n**Raw (BARF)** – Mimics natural diet, often improves coat and energy. Requires careful planning and has bacterial contamination risks.\n\n**What vets say** – Most recommend high-quality kibble as the baseline. Consult your vet before introducing raw.\n\n**The middle ground** – Quality kibble with occasional raw meaty bones or fresh food toppers.\n\nTransition slowly over 7–10 days whatever you choose.", "category": "Nutrition", "author": "Admin", "likes": 18, "img_url": "https://images.dog.ceo/breeds/husky/n02110185_10047.jpg", "public_id": "post_img_1003"})
    return "Step 1 done: users, categories, posts 1-3. Now visit /seed/woof-seed-2026/2"


@app.route("/seed/woof-seed-2026/2")
def seed_step2():
    """Step 2: posts 4-6."""
    _insert_post({"title": "Understanding Dog Body Language", "summary": "Dogs communicate constantly through their bodies. Learning to read the signals can transform your relationship with your dog.", "content": "Dogs can't speak our language but they're incredibly expressive.\n\n**The Tail** – High fast wag = excitement. Tucked tail = fear.\n\n**The Eyes** – Soft eyes = relaxed dog. Hard stare = warning. Whale eye (whites showing) = stress.\n\n**The Ears** – Pinned back = fear. Erect and forward = alertness. Relaxed = comfortable.\n\n**The Body** – Rolling over = submissive or wants belly rub. Raised hackles = arousal or fear.\n\n**Calming Signals** – Yawning, lip licking, and turning away mean your dog needs space. Catch these early to prevent escalation.", "category": "Behaviour", "author": "emma_r", "likes": 42, "img_url": "https://images.dog.ceo/breeds/beagle/n02088364_10108.jpg", "public_id": "post_img_1004"})
    _insert_post({"title": "The Best Dog-Friendly Hiking Tips", "summary": "Exploring the great outdoors with your dog is one of life's great pleasures. Here are our top tips for a safe adventure.", "content": "Hiking with your dog is one of the most rewarding experiences for both of you.\n\n**Before You Go** – Check the trail allows dogs, check your dog's fitness, ensure vaccinations and tick treatment are current.\n\n**What to Pack** – Collapsible water bowl, water, high-value snacks, poop bags, tick remover.\n\n**On the Trail** – Let your dog sniff freely – it's mentally tiring in the best way. Rest often in hot weather. Watch for excessive panting or lagging.\n\n**After the Hike** – Check paws for cuts. Check coat for ticks, especially around ears and between toes.\n\nA tired dog is a happy dog!", "category": "Lifestyle", "author": "sarah_w", "likes": 29, "img_url": "https://images.dog.ceo/breeds/poodle-standard/n02113799_2280.jpg", "public_id": "post_img_1005"})
    _insert_post({"title": "Separation Anxiety: Causes and Solutions", "summary": "Separation anxiety is one of the most common behavioural issues in dogs. Understanding it is the first step to helping your dog.", "content": "If your dog destroys things or howls when alone, they may have separation anxiety. It's treatable!\n\n**Causes** – Change in routine, rehoming, or traumatic experience. Some breeds are more prone.\n\n**Signs** – Destructive behaviour when alone, excessive vocalisation, house soiling, pacing, shadowing you.\n\n**Solutions**\n\n**Desensitise** – Build up alone time very gradually, starting with 30 seconds.\n\n**Low-key departures** – No big emotional goodbyes or excited greetings.\n\n**Enrichment** – A stuffed Kong only given when you leave creates positive association.\n\n**Exercise** – A well-exercised dog settles more easily.\n\n**Professional help** – A qualified behaviourist can make a real difference for severe cases.", "category": "Behaviour", "author": "mike_d", "likes": 37, "img_url": "https://images.dog.ceo/breeds/bulldog-english/n02096585_1380.jpg", "public_id": "post_img_1006"})
    return "Step 2 done: posts 4-6. Now visit /seed/woof-seed-2026/3"


@app.route("/seed/woof-seed-2026/3")
def seed_step3():
    """Step 3: dogs 1-3."""
    admin = mongo.db.users.find_one({"username": "Admin"})
    mike  = mongo.db.users.find_one({"username": "mike_d"})
    emma  = mongo.db.users.find_one({"username": "emma_r"})
    _insert_dog({"name": "buddy", "gender": "Male", "age": "3", "size": "Large", "good_with": ["Kids", "Dogs", "Cats"], "description": "Buddy is a gorgeous 3-year-old Golden Retriever with a heart of gold. He loves everyone he meets and has never met a stranger. Buddy is fully house trained, great on the lead, and knows his basic commands. He was surrendered when his owner moved abroad and is looking for a loving forever home.", "greeting": "Hi, I'm Buddy! I love fetch, belly rubs, and stealing socks. I promise to be your best friend forever!", "owner_id": admin["_id"], "img_url": "https://images.dog.ceo/breeds/retriever-golden/n02099601_7771.jpg", "public_id": "dog_img_2001"})
    _insert_dog({"name": "luna", "gender": "Female", "age": "2", "size": "Large", "good_with": ["Dogs"], "description": "Luna is an energetic and intelligent 2-year-old Husky who needs an experienced owner. She is stunning to look at and a joy to be around once exercised. Luna needs 2+ hours of activity daily and a secure garden. Not suitable for homes with cats.", "greeting": "Howwooo! I'm Luna and I have enough energy for the both of us. Take me hiking and I'll love you forever.", "owner_id": emma["_id"], "img_url": "https://images.dog.ceo/breeds/husky/n02110185_11364.jpg", "public_id": "dog_img_2002"})
    _insert_dog({"name": "charlie", "gender": "Male", "age": "5", "size": "Small", "good_with": ["Kids", "Dogs", "Cats"], "description": "Charlie is a sweet, gentle 5-year-old Beagle who adores company. He is great with children and other pets – the perfect family dog. Fully vaccinated, neutered, and microchipped. A real gem looking for his forever sofa.", "greeting": "Hi there! I'm Charlie. I might follow my nose into trouble sometimes, but I always come back for cuddles.", "owner_id": mike["_id"], "img_url": "https://images.dog.ceo/breeds/beagle/n02088364_13776.jpg", "public_id": "dog_img_2003"})
    return "Step 3 done: dogs 1-3. Now visit /seed/woof-seed-2026/4"


@app.route("/seed/woof-seed-2026/4")
def seed_step4():
    """Step 4: dogs 4-6."""
    admin = mongo.db.users.find_one({"username": "Admin"})
    sarah = mongo.db.users.find_one({"username": "sarah_w"})
    mike  = mongo.db.users.find_one({"username": "mike_d"})
    _insert_dog({"name": "max", "gender": "Male", "age": "1", "size": "Large", "good_with": ["Dogs"], "description": "Max is a bouncy 1-year-old Labrador full of life and mischief! Still very much a puppy at heart, he needs a home that can continue his training. Max would thrive with an active family who can give him the stimulation he needs.", "greeting": "HELLO! Is it walkies time? What about now? I'm Max and every moment is the BEST MOMENT EVER!", "owner_id": admin["_id"], "img_url": "https://images.dog.ceo/breeds/labrador/n02099712_7003.jpg", "public_id": "dog_img_2004"})
    _insert_dog({"name": "rosie", "gender": "Female", "age": "4", "size": "Medium", "good_with": ["Kids", "Dogs", "Cats"], "description": "Rosie is a calm and affectionate 4-year-old Cocker Spaniel who loves being close to her people. Well-mannered, great in the car, and fantastic with children and animals. Rosie was previously a therapy dog and has impeccable manners.", "greeting": "Hello, lovely. I'm Rosie. I'll sit nicely, I won't bark, and I'll look at you with these eyes until you give me a biscuit.", "owner_id": sarah["_id"], "img_url": "https://images.dog.ceo/breeds/spaniel-cocker/n02102318_5978.jpg", "public_id": "dog_img_2005"})
    _insert_dog({"name": "pepper", "gender": "Female", "age": "6", "size": "Medium", "good_with": ["Kids", "Cats"], "description": "Pepper is a sophisticated and playful 6-year-old Standard Poodle. Don't let the elegant appearance fool you – she is hilarious and loves to clown around. Incredibly smart, hypoallergenic, and wonderful for families with allergies.", "greeting": "Bonjour! I'm Pepper. I'm smart, I'm stylish, and I'm probably already training you without you knowing.", "owner_id": mike["_id"], "img_url": "https://images.dog.ceo/breeds/poodle-standard/n02113799_4063.jpg", "public_id": "dog_img_2006"})
    return "ALL DONE! 4 users, 5 categories, 6 posts, 6 dogs loaded. Passwords: Password1!"


if __name__ == "__main__":
    app.run(
        host=os.environ.get("IP", "0.0.0.0"),
        port=int(os.environ.get("PORT", 5000)),
        debug=False)
