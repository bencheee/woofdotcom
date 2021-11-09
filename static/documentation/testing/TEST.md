# Manual testing

Testing is done for all pages on the website by explaining what is the purpose of each page, expected outcome of back end code and then logging if the result is ‘pass’ or ‘fail’. Same is used in testing of the python functions. Forms are tested to make sure correct data is sent to the server side. Also, page restrictions are tested as part of the defensive programming principles to minimize number of bugs and problems.

## 1. Pages tests

### 1.1 user_register

This page allows user to create own account.

Expected behaviour:

* If username already exists in database, error message is shown.
* If email already exists in database, error message is shown.
* If provided passwords do not match, error message is shown
* If data is valid, new document is added to ‘users’ collection in database and user is redirected to index page.

**Test result:** All tests passed

**Form validation test:** Results 

Testing screenshots:

![example1](/static/documentation/testing/images/001.webp)
![example2](/static/documentation/testing/images/002.webp)
![example3](/static/documentation/testing/images/003.webp)
![example4](/static/documentation/testing/images/004.webp)

### 1.2 user_login

This page allows user to log in to own account.

Expected behaviour:

* If username does not exist in database, error message is shown.
* If password is not correct, error message is shown.
* If logged in successfully, user is added to session cookie and redirected to index page.

**Test result:** All tests passed

**Form validation test:** Results 

Testing screenshots:

![example5](/static/documentation/testing/images/005.webp)
![example6](/static/documentation/testing/images/006.webp)

### 1.3 user_profile

This page allows the user to change password or to edit profile info.

Expected behaviour:

* If current password is invalid, error message is shown.
* If new passwords do not match, error message is shown.
* If data is valid, update password record in a document of ‘users’ collection.
* If data is valid, update all changed records in a document of ‘users’ collection.

**Test result:** All tests passed

**Form validation test:** Results 

Testing screenshots:

![example7](/static/documentation/testing/images/007.webp)
![example8](/static/documentation/testing/images/008.webp)
![example9](/static/documentation/testing/images/009.webp)
![example10](/static/documentation/testing/images/010.webp)

### 1.4 index

This page shows latest posts and dog ads.

Expected behaviour:

* If there are no posts to show, info message is displayed in ‘Latest posts’ section.
* If there are no dogs to show, info message is displayed in ‘Newest dogs’ section.
* All documents from posts / dogs collection are sorted from newest to oldest.
* Only first 3 items from sorted posts / dogs collection are displayed.
* If user is not logged in, register section is displayed at the bottom of the page.

**Test result:** All tests passed

Testing screenshots:

![example11](/static/documentation/testing/images/065.webp)
![example12](/static/documentation/testing/images/013.webp)
![example13](/static/documentation/testing/images/014.webp)
![example14](/static/documentation/testing/images/015.webp)

### 1.5 post_main

This page shows all posts stored in the database and allows user to perform post search by providing search criteria. All posts are sorted from newest to oldest by default.

Expected behaviour:

* If there are no posts, info message is displayed.
* If filter criteria is given, posts are filtered to match the criteria.
* If sort criteria is given, posts are sorted to match the criteria.

**Test result:** All tests passed

**Forms validation test:** There is no data validation implemented since all inputs are limited to predefined options.

Testing screenshots:

![example15](/static/documentation/testing/images/066.webp)
![example16](/static/documentation/testing/images/017.webp)

### 1.6 dog_main

This page shows all dogs stored in the database and allows user to perform dog search by providing search criteria. All dogs are sorted from newest to oldest by default.

Expected behaviour:

* If there are no dogs, info message is displayed.
* If filter criteria is given, dogs are filtered to match the criteria.
* If search criteria is dog’s name, dogs are filtered to all names that contain given string

**Test result:** All tests passed

**Forms validation test:** There is no data validation implemented since all inputs are limited to predefined options.

Testing screenshots:

![example17](/static/documentation/testing/images/067.webp)
![example18](/static/documentation/testing/images/019.webp)

### 1.7 post_page

This page shows a specific post.

Expected behaviour:

* If user is anonymous, edit, delete and like buttons are hidden.
* If user is author of the post or admin, edit and delete buttons are shown.
* If user is author of the post or admin, like button is hidden.
* If user is logged in but not author of the post, edit and delete buttons are hidden but like button is shown.
* If like button is clicked for the first time, post like counter will increase by one.
* If like button is clicked again, post like counter will decrease by one.

**Test result:** All tests passed

Testing screenshots:

![example19](/static/documentation/testing/images/021.webp)
![example20](/static/documentation/testing/images/022.webp)
![example21](/static/documentation/testing/images/023.webp)
![example22](/static/documentation/testing/images/024.webp)

### 1.8 dog_page

This page shows a specific dog page.

Expected behaviour:

* If user is anonymous, edit, delete and adoption buttons are hidden.
* If user is anonymous, warning message is shown about adoption requirements.
* If user is admin, info about dog owner is shown.
* If user is author of the dog ad or admin, edit and delete buttons are shown.
* If user is author of the dog ad or admin, adoption button is hidden.
* If user is logged in, but not author of the dog ad, edit and delete buttons are hidden.
* If user is logged in but does not have full profile, adoption button is hidden.
* If user is logged in and has full profile, adoption button is shown.
* If adoption button is clicked for the first time, adopt request message will be sent to admin and message will be shown to the user.
* If adoption button is clicked again, adopt request message will be withdrawn and message will be shown to the user.

**Test result:** All tests passed

Testing screenshots:

![example23](/static/documentation/testing/images/025.webp)
![example24](/static/documentation/testing/images/026.webp)
![example25](/static/documentation/testing/images/027.webp)
![example26](/static/documentation/testing/images/028.webp)
![example27](/static/documentation/testing/images/029.webp)
![example28](/static/documentation/testing/images/030.webp)
![example29](/static/documentation/testing/images/031.webp)

### 1.9 post_new

This page allows user to add new post and to upload image from own machine.

Expected behaviour:

* If file is not an image file type, error message is shown.
* If image is uploaded, it is resized, converted to webp format and saved to cloud storage.
* If image is not uploaded, default image is added to the post.
* If data is valid, add new document to ‘posts’ collection in database and redirect user to the post page.

**Test result:** All tests passed

**Form validation test:** Results 

Testing screenshots:

![example30](/static/documentation/testing/images/032.webp)
![example31](/static/documentation/testing/images/033.webp)

### 1.10 dog_new

This page allows user to add new dog ad and to upload image from own machine.

Expected behaviour:

* If file is not an image file type, error message is shown.
* If image is uploaded, it is resized, converted to webp format and saved to cloud storage.
* If image is not uploaded, default image is added to the dog ad.
* If data is valid, add new document to ‘dogs’ collection in database and redirect user to the dog page.

**Test result:** All tests passed

**Form validation test:** Results 

Testing screenshots:

![example32](/static/documentation/testing/images/034.webp)

### 1.11 post_edit

This page allows post author or admin to edit post and to change post image.

Expected behaviour:

* If file is not an image file type, error message is shown.
* If image is uploaded, it is resized, converted to webp format and saved to cloud storage.
* If image is uploaded and previous image is not default system image, previous image is deleted from the cloud.
* If image is not uploaded, previous image stays the same.
* If data is valid, update document from ‘posts’ collection in database and redirect user to the post page. Also, ‘last update’ tag is added to the page.

**Test result:** All tests passed

**Form validation test:** Results 

Testing screenshots:

![example33](/static/documentation/testing/images/037.webp)
![example34](/static/documentation/testing/images/038.webp)

### 1.12 dog_edit

This page allows dog owner or admin to edit dog ad and to change dog image.

Expected behaviour:

* If file is not an image file type, error message is shown.
* If image is uploaded, it is resized, converted to webp format and saved to cloud storage.
* If image is uploaded and previous image is not default system image, previous image is deleted from the cloud.
* If image is not uploaded, previous image stays the same.
* If data is valid, update document from ‘dogs’ collection in database and redirect user to the dog page.

**Test result:** All tests passed

**Form validation test:** Results 

Testing screenshots:

![example35](/static/documentation/testing/images/068.webp)

### 1.13 dog_surrender

This page shows tips for the user when surrendering a dog.

Expected behaviour:

* If user is anonymous or registered but with incomplete info, message is shown about restrictions to post an ad. Link for rehomig form is hidden.
* If user is registered and has full profile, link for rehoming is shown.

**Test result:** All tests passed

Testing screenshots:

![example36](/static/documentation/testing/images/035.webp)
![example37](/static/documentation/testing/images/036.webp)

### 1.14 inbox

This page shows all messages sent to the user. Messages are sorted from newest to oldest by default.

Expected behaviour:

* Number of unread messages in the header title changes dynamically.
* If message status changes from ‘unread’ to ‘read’, style of message box changes too.
* If user has replied to a message, ‘replied’ icon is attached to the message box.
* If user is admin, ‘requests’ tab is added to separate standard messages from adoption messages.
* If message is sent by anonymous user, ‘unregisterd user’ tag is added to the message box.

**Test result:** All tests passed

Testing screenshots:

![example38](/static/documentation/testing/images/043.webp)
![example39](/static/documentation/testing/images/044.webp)

### 1.15 message

This page shows the message content and info about the sender. User can reply to the message and delete the message.

Expected behaviour:

*In case message receiver is standard user:*

* ‘sent by’, ‘sent on’ and message content are shown on the page.

*In case message receiver is admin:*

* If message is standard and sent by registered user, ‘sent by’, ‘sent on’ and ‘message content are shown.
* If message is standard and sent by anonymous user, ‘first name’, ‘email address’ and message content are shown. Reply button is hidden and info is displayed with message to contact the user via email client.
* If message is adoption request, ‘applicant info’ is shown instead of the message.
* If message is adoption request and dog is deleted from the database, ‘dog not available’ tag is added to the message.

**Test result:** All tests passed

**Form validation test:** Results 

Testing screenshots:

![example40](/static/documentation/testing/images/045.webp)
![example41](/static/documentation/testing/images/046.webp)
![example42](/static/documentation/testing/images/047.webp)
![example43](/static/documentation/testing/images/048.webp)
![example44](/static/documentation/testing/images/049.webp)

### 1.16 alert

Shows a message on the screen depending on the received response formthe server.

Expected behaviour:

* If response = ‘dog error’, show ‘dog not found’ message and link to ‘dog_main’.
* If reposnse = ‘post error’, shows ‘post not found’ message and link to ‘post_main’.
* If response = ’message error’, shows ‘message not found’ message and link to ‘inbox’.
* If response = ‘message sent’, shows ‘message sent’ message. If message was sent by registered user shows link for ‘inbox’ otherwise shows link for ‘index’.
* If response = ‘page error’, shows ‘something went wrong’ message and link to ‘index’.

**Test result:** All tests passed

Testing screenshots:

![example45](/static/documentation/testing/images/050.webp)
![example46](/static/documentation/testing/images/051.webp)
![example47](/static/documentation/testing/images/052.webp)
![example48](/static/documentation/testing/images/053.webp)
![example49](/static/documentation/testing/images/054.webp)
![example50](/static/documentation/testing/images/055.webp)

### 1.17 contact

This page allows users to send messages to admin inbox.

Expected behaviour:

* If user is registered, ‘subject’ and ‘message’ inputs are only form  inputs.
* If user is anonymous, ‘first name’ and ‘email’ input fields are added to the form.

**Test result:** All tests passed

**Form validation test:** Results 

Testing screenshots:

![example51](/static/documentation/testing/images/056.webp)
![example52](/static/documentation/testing/images/057.webp)

## 2. Functions tests

### 2.1 post_delete

This function deletes the post from the database.

Expected behaviour:

* If previous image is not default system image, previous image is deleted from the cloud.
* If post object id was included in ‘liked posts’ record in any of the documents in ‘users’ collection, it is removed.
* Post is deleted from ‘posts’ collection in database.

**Test result:** All tests passed

Testing screenshots:

![example53](/static/documentation/testing/images/039.webp)
![example54](/static/documentation/testing/images/040.webp)

### 2.2 dog_delete

This function deletes the dog from the database.

Expected behaviour:

* If previous image is not default system image, previous image is deleted from the cloud.
* If dog object id was included in ‘adoption requests’ record in any of the documents in ‘users’ collection, generic message about dog deletion is sent to those users and then dog object id is removed from that record.
* Dog is deleted from ‘dogs’ collection in database.

**Test result:** All tests passed

Testing screenshots:

![example55](/static/documentation/testing/images/041.webp)
![example56](/static/documentation/testing/images/042.webp)
![example57](/static/documentation/testing/images/064.webp)

### 2.3 reply

This function sends a reply to an existing message in users inbox.

Expected behaviour:

* If original message subject starts with ‘Re:’, subject is not changed. Otherwise ‘Re:’ prefix is added to the message subject.
* New message document is created and saved to the database. Document records are different depending on type of original message which can be ‘standard’ or ‘adoption’.
* If message is sent, user is redirected to ‘alert’ page which shows ‘message sent’ message.

**Test result:** All tests passed

Testing screenshots:

![example58](/static/documentation/testing/images/053.webp)

### 2.4 message_delete

This function deletes the message from the database.

Expected behaviour:

* Deletes the message from the ‘messages’ collection from the database
* Shows ‘message deleted’ message.

**Test result:** All tests passed

Testing screenshots:

![example59](/static/documentation/testing/images/058.webp)
![example60](/static/documentation/testing/images/059.webp)

### 2.5 generate_photo

This function uploads the image from users machine, converts it to fixed size and webp format. Saves the image with unique file name to cloud storage.

Expected behaviour:

* If img_id already exists, generates new img_id.
* Generates new filename with unique img_id.
* Saves image to cloud service.
* Returns unique image identifiers so they can be manipulated by other functions.

**Test result:** All tests passed

Testing screenshots:

![example61](/static/documentation/testing/images/060.webp)

### 2.6 adopt

This function sends dog adoption request to admin inbox.

Expected behaviour:

* Message document is saved to ‘messages’ collection in database.
* Dog object id is added to ‘adoption requests’ record in user document from ‘users’ collection.
* Message about successfull application is shown to the user.

**Test result:** All tests passed

Testing screenshots:

![example62](/static/documentation/testing/images/061.webp)

### 2.7 adopt_undo

This function withdraws dog adoption application and deletes request from admin inbox.

Expected behaviour:

* Message document is deleted from ‘messages’ collection in database.
* Dog object id is removed from ‘adoption requests’ record in user document from ‘users’ collection.
* Message about withdrawn application is shown to the user.

**Test result:** All tests passed

Testing screenshots:

![example63](/static/documentation/testing/images/062.webp)

### 2.8 global_vars

This function returns variables which contain number of unread messages in inbox for admin and standard users. This variables are used by base.html to show this numbers in navigation bar by the inbox link.

**Test result:** All tests passed

Testing screenshots:

![example64](/static/documentation/testing/images/063.webp)

## 3. Form validation

All forms on the website are tested to ensure correct data is passed on to the server side. Expected input and and result of the test outcome is logged for each form.

### 3.1 user_register

On submit, form method is POST and the ‘user_register’ python function is called. Also on submit, javascript ‘setLocalRegister’ function is called to store all form values to local storage. This enables to pre fill the form values in case server returns an error caused by invalid input and page has to refresh.

Expected inputs:

* Username (required) is between 4 and 16 characters long, does not contain spaces or special characters 
* Email address (required) is in correct email format
* Password (required) is between 8 and 16 characters long and does not contain spaces

**All tests passed!**

### 3.2 user_login

On submit, form method is POST and the ‘user_login’ python function is called. 

Expected inputs:

* Username (required) does not have any validation restrictions*
* Password (required) does not have any validation restrictions*

**All tests passed!**

### 3.3 user_profile

There are two forms on this page. First form allows user to change password only, and the other form allows change of profile information. If previous data exists, info in form 2 is pre populated on load. On submit, method is POST and the ‘user_login’ python function is called for both forms. 

Expected inputs for Form 1:

* Username is pre populated and disabled by default
* Email is pre populated and disabled by default
* Password (required) is between 8 and 16 characters long and does not contain spaces

Expected inputs for Form2:

* First name (required) is between 2 and 20 characters long, does not contain spaces, numbers or special characters 
* Last name (required) is between 2 and 20 characters long, does not contain spaces, numbers or special characters 
* Phone is exactly 10 numbers long, it starts with 08 and third number is 3, 5, 7 or 9
* About is min 10 and max 10000 characters long

**All tests passed!**

### 3.4 post_main

On submit, form method is POST and the ‘post_main’ python function is called.  

Expected inputs:

* Category does not have any validation restrictions*
* Author name does not have any validation restrictions*
* Sort by does not have any validation restrictions*

### 3.5 dog_main

On submit, form method is POST and the ‘dog_main’ python function is called.

Expected inputs:

* Dog name does not have any validation restrictions*
* Dog age does not have any validation restrictions*
* Dog gender does not have any validation restrictions*
* Dog size does not have any validation restrictions*
* Checkbox inputs do not have any validation restrictions*

### 3.6 post_new / post_edit

On submit, form method is POST and the ‘post_new / post_edit’ python function is called. Also on submit, javascript ‘setLocalPost’ function is called to store all form values to local storage. This enables to pre fill the form values in case server returns an error caused by invalid input and page has to refresh. Enctype of the form is set to 'multipart/form-data' to allow photos to be uploaded. If post_edit function is called, all form fields are pre populated from the database.

Expected inputs:

* Select category (required) does not have any validation restrictions and all options are pre populated by documents in 'categories' collection from database
* Post title (required) is between 2 and 25 characters long
* Summary (required) is min 10 and max 150 characters long
* Post content (required) is min 250 and max 10000 characters long
* Upload photo - validation is done within python code

**All tests passed!**

### 3.7 dog_new / dog_edit

On submit, form method is POST and the ‘dog_new / dog_edit’ python function is called. Also on submit, javascript ‘setLocalDog’ function is called to store all form values to local storage. This enables to pre fill the form values in case server returns an error caused by invalid input and page has to refresh. Enctype of the form is set to 'multipart/form-data' to allow photos to be uploaded.  If dog_edit function is called, all form fields are pre populated from the database.

Expected inputs:

* Dog name (required) is between 2 and 15 characters long
* Gender (required) has two options - 'male' and 'female'
* Age (required) is between 1 and 2 characters long, only numbers allowed
* Size (required) has three options - 'small', 'medium' and 'large'
* Other options is a checkbox input with four options - 'Good with kids', 'Suitable for families', 'Good with other pets', and 'Prefers one owner'
* Greeting (required) is min 10 and max 150 characters long
* Dog description (required) is min 150 and max 10000 characters long
* Upload photo - validation is done within python code

**All tests passed!**

### 3.8 message_reply

On submit, form method is POST and the ‘reply’ python function is called. Also, 'receiver' and 'msg_id' variables are sent to the server side for further actions.

Expected inputs:

* Message (required) is max 10000 characters long.

**All tests passed!**

### 3.9 contact

Expected inputs:

* First name (required) is between 2 and 20 characters long, does not contain spaces or special characters 
* Email address (required) is in correct email format
* Subject (required) is max 40 characters long
* Message (required) is max 10000 characters long

**All tests passed!**

## 4. User permissions

Goal of this test is to make sure that certain pages and functions can be accessed only by authorized users. To perform this test, a temporary halper page was made. This page contained links to all pages / functions and it made testing process much faster.

All tests were made for following scenarios:

* If user who is trying to get access is anonymous (not registered or logged in)
* If user who is trying to get access is registered
* If registered user is author of posted content
* If registered user is not author of posted content
* If registered user has full profile info
* If registered user does not have full profile info
* If user is admin

**Screenshot of testing table with links:**

![testing table links](/static/documentation/testing/images/069.webp)

**Results of all tests:**

![testing pages permissions](/static/documentation/testing/images/070.webp)

![testing functions permissions](/static/documentation/testing/images/071.webp)
