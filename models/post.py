from google.appengine.ext import ndb
from models import User


class Post(ndb.Model):
    subject = ndb.StringProperty(required=True)
    content = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True, required=True)
    user_key = ndb.KeyProperty(kind=User, required=True)
