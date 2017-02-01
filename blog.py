import os
import webapp2
import jinja2

from google.appengine.ext import db

# configure jinja2 template engine
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

#### MODELS ####
class Post(db.Model):
    subject = db.StringProperty(required = True)
    content = db.TextProperty(required = True)
    created = db.DateTimeProperty(auto_now_add = True,
                                  required = True)


#### BLOG STUFF ####
class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


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


#### SERVER STUFF ####
routes = [
           ('/', PostIndex),
           ('/newpost', PostNew),
           ('/(\d+)', PostShow),
         ]

app = webapp2.WSGIApplication(routes=routes, debug=True)
