import os
import webapp2
import jinja2

# configure jinja2 template engine
template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir),
                               autoescape = True)

class Handler(webapp2.RequestHandler):
    def write(self, *a, **kw):
        self.response.out.write(*a, **kw)

class HomePage(Handler):
    def get(self):
        self.write("hello world")


routes = [
           ('/', HomePage),
         ]
app = webapp2.WSGIApplication(routes=routes, debug=True)
