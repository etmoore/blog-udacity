# Multi-User Blog
[link to live version](http://blog-project-udacity-158621.appspot.com/)

This is a Udacity Full Stack Nanodegree project that uses the webapp2 framework with the Jinja2 templating engine.
Bootstrap is used to provide some basic styling.

## Features
* Authentication: login, logout, signup
* Users must be logged in to modify posts or create comments.
* Users can create, edit, and delete posts. Users can only edit or delete their own posts.
* Users can like posts. Users cannot like their own posts or like a post multiple times.
* Users can comment on posts.

## How to run the app locally
1. Install the google cloud SDK.
1. Clone this repo locally.
1. Run the gcloud python appserver, passing in the project root path as an argument: `[path to gcloud SDK]/dev_appserver.py .`
1. Open localhost:8080 in your browser.
