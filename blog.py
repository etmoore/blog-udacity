import os
import webapp2
import jinja2
import time

from models import User, Post, Like, Comment
from wrappers import (confirm_logged_in, confirm_post_exists,
                      confirm_user_owns_post, confirm_like_allowed)
from helpers import (valid_username, valid_password, valid_email,
                     make_pw_hash, confirm_pw, make_secure_val,
                     check_secure_val)

# configure jinja2 template engine
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)


class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        """Write to self.response."""
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        """Generate template string."""
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        """Render template given filename."""
        self.write(self.render_str(template, **kw))

    def initialize(self, *a, **kw):
        """Assign the logged in user to self.user."""
        webapp2.RequestHandler.initialize(self, *a, **kw)
        user_id = self.read_secure_cookie('user_id')
        self.user = user_id and User.get_by_id(int(user_id))

    def set_secure_cookie(self, name, value):
        """Set a secure cookie given a name and value."""
        secure_val = make_secure_val(value)
        self.response.set_cookie(name, secure_val)

    def read_secure_cookie(self, cookie_name):
        """Decrypt secure cookie and return its value."""
        cookie_val = self.request.cookies.get(cookie_name)
        if cookie_val:
            return check_secure_val(cookie_val)

    def login(self, user):
        """Set a secure cookie with the user's id."""
        user_id = user.key.id()
        self.set_secure_cookie('user_id', str(user_id))
        self.redirect('/welcome')

    def error(self, status):
        self.render('error.html', status=status)


class PostIndex(Handler):
    def get(self):
        """Display the post index page."""
        posts = Post.query()
        self.render('post-index.html',
                    posts=posts,
                    user=self.user)


class PostNew(Handler):
    @confirm_logged_in
    def get(self):
        """Display the new post form."""
        self.render('post-new.html', user=self.user)

    @confirm_logged_in
    def post(self):
        """Save the new post."""
        subject = self.request.get('subject')
        content = self.request.get('content')

        p = Post(subject=subject,
                 content=content,
                 author=self.user.username,
                 user_key=self.user.key)
        p.put()

        permalink = "/%s" % p.key.id()
        self.redirect(permalink)


class PostShow(Handler):
    @confirm_post_exists
    def get(self, post_id, post):
        """Display the post show page."""
        post.like_count = Like.query(Like.post_key == post.key).count()
        post.comments = Comment.query(Comment.post_key == post.key) \
                               .order(Comment.created).fetch()

        self.render('post-show.html',
                    post=post,
                    user=self.user)


class PostDelete(Handler):
    @confirm_logged_in
    @confirm_post_exists
    def get(self, post_id, post):
        """Check permissions and delete post."""
        if self.user.username == post.author:
            post.key.delete()
            time.sleep(0.2)  # give the ndb operation time to complete
            self.redirect('/')

        else:
            error = "You do not have permission to perform this action."
            post.comments = Comment.query(Comment.post_key == post.key) \
                                   .order(Comment.created).fetch()
            return self.render('post-show.html',
                               error=error,
                               post=post,
                               user=self.user)


class PostEdit(Handler):
    @confirm_logged_in
    @confirm_post_exists
    @confirm_user_owns_post
    def get(self, post_id, post):
        """Display post edit form."""
        self.render('post-edit.html', post=post)

    @confirm_logged_in
    @confirm_post_exists
    @confirm_user_owns_post
    def post(self, post_id, post):
        """Save the edited post."""
        post.subject = self.request.get('subject')
        post.content = self.request.get('content')
        post.put()

        self.redirect('/' + post_id)


class PostLike(Handler):
    @confirm_logged_in
    @confirm_post_exists
    @confirm_like_allowed
    def get(self, post_id, post):
        """Create like."""
        like = Like(post_key=post.key, user_key=self.user.key)
        like.put()

        time.sleep(0.2)  # give the ndb operation time to complete
        self.redirect('/' + post_id)


class PostComment(Handler):
    @confirm_logged_in
    @confirm_post_exists
    def post(self, post_id, post):
        """Create a comment if the user is logged in."""
        # grab the content, user, etc. related to the comment
        content = self.request.get('content')

        # create the comment
        c = Comment(user_key=self.user.key,
                    content=content,
                    author=self.user.username,
                    post_key=post.key)
        c.put()
        time.sleep(0.2)  # give the ndb operation time to complete
        self.redirect('/' + post_id)


class Signup(Handler):
    def get(self):
        """Display the signup form."""
        self.render('signup-form.html')

    def post(self):
        """Create the user if info is valid, then log them in."""
        have_error = False
        username = self.request.get('username')
        password = self.request.get('password')
        verify = self.request.get('verify')
        email = self.request.get('email')

        params = dict(username=username, email=email)

        if not valid_username(username):
            params['error_username'] = "That's not a valid username."
            have_error = True

        if not valid_password(password):
            params['error_password'] = "That's not a valid password."
            have_error = True

        if verify != password:
            params['error_verify'] = "Your passwords didn't match."
            have_error = True

        if not valid_email(email):
            params['error_email'] = "That's not a valid email."
            have_error = True

        if User.query(User.username == username).get():
            params['error_duplicate'] = "User already exists"
            have_error = True

        if have_error:
            self.render('signup-form.html', **params)

        else:
            pw_hash = make_pw_hash(username, password)
            u = User(username=username,
                     pw_hash=pw_hash,
                     email=email)
            u.put()

            self.login(u)


class Welcome(Handler):
    """Display the welcome page."""
    @confirm_logged_in
    def get(self):
        self.render('welcome.html', user=self.user)


class Login(Handler):
    def get(self):
        """Display the login form"""
        self.render('login-form.html')

    def post(self):
        """Login the user, setting a secure cookie 'user_id'."""
        username = self.request.get('username')
        password = self.request.get('password')
        u = User.query(User.username == username).get()

        if confirm_pw(u, password):
            self.login(u)
        else:
            error = 'Invalid Credentials'
            self.render('login-form.html', error=error, username=username)


class Logout(Handler):
    def get(self):
        """Logout the user, erasing the user_id cookie"""
        self.response.set_cookie('user_id', '')
        self.redirect('/login')


# SERVER STUFF #
routes = [
    ('/', PostIndex),
    ('/newpost', PostNew),
    ('/(\d+)', PostShow),
    ('/(\d+)/delete', PostDelete),
    ('/(\d+)/edit', PostEdit),
    ('/(\d+)/like', PostLike),
    ('/(\d+)/comment', PostComment),
    ('/signup', Signup),
    ('/welcome', Welcome),
    ('/login', Login),
    ('/logout', Logout),
]

app = webapp2.WSGIApplication(routes=routes, debug=True)
