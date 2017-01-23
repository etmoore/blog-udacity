import os
import webapp2
import jinja2

# configure jinja2 template engine
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dir),
                               autoescape=True)

#### BLOG STUFF ####
class Handler(webapp2.RequestHandler):

    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

    def render_str(self, template, **params):
        t = jinja_env.get_template(template)
        return t.render(params)

    def render(self, template, **kw):
        self.write(self.render_str(template, **kw))


class HomePage(Handler):
    def get(self):
        self.write('hello world')


class BlogIndex(Handler):
    def get(self):
        self.render('blog-index.html')


class NewPost(Handler):
    def get(self):
        self.render('blog-new.html')


routes = [
           ('/', HomePage),
           ('/blog', BlogIndex),
           ('/newpost', NewPost),
         ]

app = webapp2.WSGIApplication(routes=routes, debug=True)
