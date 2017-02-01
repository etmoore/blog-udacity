import os
import webapp2
import jinja2
import re
import random
from string import letters
import hashlib
import hmac

from google.appengine.ext import db

# configure jinja2 template engine
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

#### MODELS ####
class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True, required = True)


class User(db.Model):
    username = db.StringProperty(required = True)
    pw_hash = db.StringProperty(required = True)
    email = db.StringProperty()


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

    def read_secure_cookie(self, cookie_name):
        cookie_val = self.request.cookies.get(cookie_name)
        if cookie_val:
            return check_secure_val(cookie_val)


class PostIndex(Handler):
    def get(self):
        posts = Post.all()
        self.render('post-index.html', posts=posts)


class PostNew(Handler):
    def get(self):
        self.render('post-new.html')

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        p = Post(subject=subject, content=content)
        p.put()

        permalink = "/%s" % p.key().id()
        self.redirect(permalink)


class PostShow(Handler):
    def get(self, post_id):
        post_id = int(post_id)
        post = Post.get_by_id(post_id)

        self.render('post-show.html', post=post)


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

        if have_error:
            self.render('signup-form.html', **params)

        else:
            pw_hash = make_pw_hash(username, password)
            u = User(username=username,
                     pw_hash=pw_hash,
                     email=email)
            u.put()

            # set cookie
            user_id = str(u.key().id())
            secure_cookie = make_secure_val(user_id)
            self.response.set_cookie('user_id', secure_cookie)

            self.redirect('/welcome')

class Welcome(Handler):
    def get(self):
        user_id = int(self.read_secure_cookie('user_id'))
        user = User.get_by_id(user_id)

        self.render('welcome.html', user=user)

#### SERVER STUFF ####
routes = [
           ('/', PostIndex),
           ('/newpost', PostNew),
           ('/(\d+)', PostShow),
           ('/signup', Signup),
           ('/welcome', Welcome),
         ]

app = webapp2.WSGIApplication(routes=routes, debug=True)
