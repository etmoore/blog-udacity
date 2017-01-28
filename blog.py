import os
import webapp2
import jinja2

from google.appengine.ext import db

# configure jinja2 template engine
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

#### MODELS ####
class Blog(db.Model):
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


class BlogIndex(Handler):
    def get(self):
        blogs = Blog.all()
        self.render('blog-index.html', blogs=blogs)


class NewPost(Handler):
    def get(self):
        self.render('blog-new.html')

    def post(self):
        subject = self.request.get('subject')
        content = self.request.get('content')

        b = Blog(subject=subject, content=content)
        b.put()

        self.redirect('/')


routes = [
           ('/', BlogIndex),
           ('/newpost', NewPost),
         ]

app = webapp2.WSGIApplication(routes=routes, debug=True)
