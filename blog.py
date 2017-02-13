import os
import webapp2
import jinja2
import re
import random
from string import letters
import hashlib
import hmac
import time

from google.appengine.ext import ndb

# configure jinja2 template engine
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

#### MODELS ####
class User(ndb.Model):
    username = ndb.StringProperty(required = True)
    pw_hash = ndb.StringProperty(required = True)
    email = ndb.StringProperty()


class Post(ndb.Model):
    subject = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    author = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True, required=True)
    user_key = ndb.KeyProperty(kind=User, required=True)


class Like(ndb.Model):
    post_key = ndb.KeyProperty(kind=Post, required=True)
    user_key = ndb.KeyProperty(kind=User, required=True)


class Comment(ndb.Model):
    content = ndb.TextProperty(required=True)
    author = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True, required=True)
    post_key = ndb.KeyProperty(kind=Post, required=True)
    user_key = ndb.KeyProperty(kind=User, required=True)


#### BLOG STUFF ####

def valid_username(username):
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return USER_RE.match(username)

def valid_password(password):
    PASSWORD_RE = re.compile(r"^.{3,20}$")
    return PASSWORD_RE.match(password)

def valid_email(email):
    EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")
    return not email or EMAIL_RE.match(email)

def make_salt(length=5):
    return ''.join(random.choice(letters) for x in range(length))

def make_pw_hash(username, password, salt=None):
    salt = salt or make_salt()
    h = hashlib.sha256(username + password + salt).hexdigest()
    return '%s,%s' % (salt, h)

def confirm_pw(user, password):
    if not user:
        return False
    username = user.username
    pw_hash = user.pw_hash
    salt = pw_hash.split(',')[0]
    return make_pw_hash(username, password, salt) == pw_hash

secret = "bananabread"
def make_secure_val(value):
    return '%s|%s' % (value, hmac.new(secret, value).hexdigest())

def check_secure_val(secure_value):
    value = secure_value.split('|')[0]
    if secure_value == make_secure_val(value):
        return value


class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))

    def initialize(self, *a, **kw):
        '''Get the logged in user'''
        webapp2.RequestHandler.initialize(self, *a, **kw)
        user_id = self.read_secure_cookie('user_id')
        self.user = user_id and User.get_by_id(int(user_id))

    def set_secure_cookie(self, name, value):
        secure_val = make_secure_val(value)
        self.response.set_cookie(name, secure_val)

    def read_secure_cookie(self, cookie_name):
        cookie_val = self.request.cookies.get(cookie_name)
        if cookie_val:
            return check_secure_val(cookie_val)

    def login(self, user):
        user_id = user.key.id()
        self.set_secure_cookie('user_id', str(user_id))
        self.redirect('/welcome')

class PostIndex(Handler):
    def get(self):
        posts = Post.query()
        self.render('post-index.html',
                    posts=posts,
                    user=self.user)


class PostNew(Handler):
    def get(self):
        if not self.user:
            return self.redirect('/login')

        self.render('post-new.html', user=self.user)

    def post(self):
        if not self.user:
            return self.redirect('/login')

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
    def get(self, post_id):
        p = Post.get_by_id(int(post_id))

        p.like_count = Like.query(Like.post_key==p.key).count()
        p.comments = Comment.query(Comment.post_key==p.key) \
                            .order(Comment.created).fetch()

        self.render('post-show.html',
                    post=p,
                    user=self.user)


class PostDelete(Handler):
    def get(self, post_id):

        if not self.user:
            return self.redirect('/login')

        post_id = int(post_id)
        p = Post.get_by_id(post_id)

        if self.user.key == p.author:
            p.delete()

            time.sleep(0.2) # give the ndb operation time to complete
            self.redirect('/')

        else:
            error = "You do not have permission to perform this action."
            p.comments = Comment.query(Comment.post_key==p.key) \
                                .order(Comment.created).fetch()
            return self.render('post-show.html',
                               error=error,
                               post=p,
                               user=self.user)

class PostEdit(Handler):
    def get(self, post_id):
        if not self.user:
            return self.redirect('/login')

        p = Post.get_by_id(int(post_id))

        # confirm that the user is the post author
        if self.user.username == p.author:
            self.render('post-edit.html', post=p)
        else:
            error = "You do not have permission to perform this action."
            p.comments = Comment.query(Comment.post_key==p.key) \
                                .order(Comment.created).fetch()

            return self.render('post-show.html',
                               error=error,
                               user=self.user,
                               post=p)

    def post(self, post_id):
        if not self.user:
            return self.redirect('/login')

        p = Post.get_by_id(int(post_id))

        p.subject = self.request.get('subject')
        p.content = self.request.get('content')
        p.put()

        self.redirect('/' + post_id)


class PostLike(Handler):
    def get(self, post_id):
        if not self.user:
            return self.redirect('/login')

        p = Post.get_by_id(int(post_id))
        p.like_count = Like.query(Like.post_key == p.key).count()
        p.comments = Comment.query(Comment.post_key==p.key) \
                            .order(Comment.created).fetch()

        if self.user.key == p.user_key:
            error = "You cannot like your own post."

            return self.render('post-show.html',
                               error=error,
                               post=p,
                               user = self.user)

        # if the current user has already liked this post, display error
        if Like.query(Like.post_key==p.key, Like.user_key==self.user.key).get():
            error = "You have already liked this post."
            return self.render('post-show.html',
                               error=error,
                               post=p,
                               user = self.user)


        l = Like(post_key=p.key, user_key=self.user.key)
        l.put()

        time.sleep(0.2) # give the ndb operation time to complete
        self.redirect('/' + post_id)


class PostComment(Handler):
    def post(self, post_id):
        if not self.user:
            return self.redirect('/login')
        # grab the content, user, etc. related to the comment
        content = self.request.get('content')
        post = Post.get_by_id(int(post_id))

        # create the comment
        c = Comment(user_key=self.user.key,
                    content=content,
                    author=self.user.username,
                    post_key=post.key)
        c.put()

        time.sleep(0.2) # give the ndb operation time to complete
        return self.redirect('/' + post_id)


class Signup(Handler):
    def get(self):
        self.render('signup-form.html')

    def post(self):
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
    def get(self):
        if self.user:
            self.render('welcome.html', user=self.user)
        else:
            self.redirect('/signup')


class Login(Handler):
    def get(self):
        self.render('login-form.html')

    def post(self):
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
        self.response.set_cookie('user_id', '')
        self.redirect('/login')


#### SERVER STUFF ####
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
