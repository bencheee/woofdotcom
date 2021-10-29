# woof(dot)com

[Click for live website demo](http://woofdotcom.herokuapp.com/)

**woof(dot)com** is web portal for dog lovers and it is part of my 3nd milestone project in **Code Institute's Full Stack Software Development Course**. This site is intended for all dog lovers to share their posts with community, to find new homes for their dogs in case they can not keep them anymore, and for those who would like to adopt a dog.

---

## 1. USER EXPERIENCE (UX)

### 1.1 User Stories

#### 1.1.1 First time visitors's goals

- *As a first time visitor*, I want to clearly see the purpose of the site and to easily navigate throughout the site

- *As a first time visitor*, I want to see dog content which is divided into easily understandable and well structured sections.

- *As a first time visitor*, I want to be able to use search tools to filter content by specific criteria

- *As a first time visitor*, I want to be able to contact the site owner

- *As a first time visitor*, I want to be able to create account which will give me more options on the site

#### 1.1.2 Frequent user's goals

- *As a frequent user*, I want to be able to write my own content and to share it with other users of the site

- *As a frequent user*, I want to be able to add dogs and their info to the dog database on the site

- *As a frequent user*, I want to be able to edit or delete all the content created by myself at any time

- *As a frequent user*, I want to be able to give positive feedback to other users who are posting their content to the site

- *As a frequent user*, I want to be able to send and withdraw applications for adopting dogs

- *As a frequent user*, I want to be able to easily communicate with site owner or admin

- *As a frequent user*, I want to be able to make changes to my profile

#### 1.1.3 Site owner's goals

- *As a site owner*, I want to provide a platform for users to shair their knowledge, experiences, advices and passion for dogs

- *As a site owner*, I want to provide service and support for dog owners to re-home their dogs if they can not keep them for any reason anymore

- *As a site owner*, I want to make all data easily accessible and to implement tools for more detailed searches

- *As a site owner*, I want to provide messaging tools between site users and myself as integrated part of the site

- *As a site owner*, I want to promote social media links to grow the community

---

## 2. WIREFRAMES

- [Mobile view](static/documentation/wireframes/mobile.pdf)
- [Tablet view](static/documentation/wireframes/tablet.pdf)
- [Desktop view](static/documentation/wireframes/desktop.pdf)

---

## 3. TECHNOLOGIES USED

### 3.1 Languages

- [HTML5](https://en.wikipedia.org/wiki/HTML5)
- [CSS3](https://en.wikipedia.org/wiki/CSS) 
- [JavaScript](https://en.wikipedia.org/wiki/JavaScript)
- [Python 3.8](https://en.wikipedia.org/wiki/Python_(programming_language))

### 3.2 Frameworks, libraries and programs

- [Balsamiq](https://balsamiq.com/) was used to create the wireframes during the site design process.

- [jQuery](https://jquery.com/) was used along with JavaScript to manipulate the DOM, CSS and handle JavaScript events in easier way.

- [Flask](https://flask.palletsprojects.com/en/2.0.x/) is a micro web framework written in Python which was used to create this app.

- [Heroku](https://www.heroku.com/) is a cloud platform which was used to deploy the project.

- [Google Fonts](https://fonts.google.com/) were used to import 'Frederick the Great' and 'Libre Franklin' fonts which were used throughout the site.

- [Gitpod](https://www.gitpod.io/) was used to write all the HTML, CSS, JavaScript and Python code for the site.

- [Git](https://git-scm.com/) was used for version control by utilizing the Gitpod terminal to commit to Git and Push to GitHub

- [GitHub](https://github.com/) is used to store the projects code after being pushed from Git.

- [Photopea](https://www.photopea.com/) is free online photo editor which was used to edit and optimize background image, logo and all card images.

- [Font Awesome](https://fontawesome.com/) was used to add icons for aesthetic and UX purposes.

- [Autoprefixer](https://autoprefixer.github.io/) was used to add prefixes to CSS properties which are not supported by some browsers.

---

## 4. DESIGN

---

## 5. TESTING

---

## 6. DEPLOYMENT

### 6.1 Creating repository on GitHub

Repository for this project was created using following steps:

1. Sign in to [GitHub account](https://github.com/bencheee) and click on the "New" button in the top right corner of the page

![Deployment 1](/static/documentation/deployment/001.png)

2. Choose Code Institute gitpod template from dropdown menu, type in the repository name and click on "Create repository" button at the bottom of the page

![Deployment 2](/static/documentation/deployment/002.png)

### 6.2 Deploying project on Heroku

This project was deployed to GitHub Pages using following steps:

1. Sign in to [Heroku](https://www.heroku.com/) and create new app by clicking on "New" button in top right corner

![Deployment 3](/static/documentation/deployment/003.png)

2. Choose app name and region and click on "Create app" button

![Deployment 4](/static/documentation/deployment/004.png)

3. Go to "Settings" tab and and click on "Reveal Config Vars" button. Update all variables from env.py file.

![Deployment 5](/static/documentation/deployment/005.png)

4. Click on "Deploy" tab and choose GitHub as deployment method

![Deployment 6](/static/documentation/deployment/006.PNG)

5. Enter GitHub repository name and click on "Search" button. When repository is loaded click on "Connect" button.

![Deployment 7](/static/documentation/deployment/007.PNG)

![Deployment 8](/static/documentation/deployment/008.PNG)

6. Choose main branch and click on "Enable Automatic Deploys" button. Click on "Deploy Branch" button.

![Deployment 9](/static/documentation/deployment/009.PNG)

*Make sure to have Procfile and requirements.txt updated in project repository, otherwise app will not run.
 
### 6.3 Forking repository

To fork the repository use the following steps:

1. Sign in to GitHub and open [woof(dot)com](https://github.com/bencheee/woofdotcom)

2. Click on the *Fork* icon in the top right corner of the page

![Deployment 10](/static/documentation/deployment/010.PNG)

### 6.4 Cloning repository

To make a local clone of the repository use the following steps:

1. Sign in to GitHub and open [woofdotcom](https://github.com/bencheee/woofdotcom)

2. At the top of the repository click on the *Code* icon

3. Copy the provided HTTPS link

4. Open Git Bash and change the current working directory to the location where the cloned directory should be made

5. Type *git clone* and then paste the copied URL

```
$ git clone https://github.com/bencheee/woofdotcom.git
```

6. Press *Enter* and local clone of the repository will be created

![Deployment 11](/static/documentation/deployment/011.png)

---

## 7. CREDITS

### 7.1 Acknowledgements

- My mentor for continuous helpful feedback

- Tutor support at Code Institute for their support 