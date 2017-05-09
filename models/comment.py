from google.appengine.ext import ndb
from models import Post, User


class Comment(ndb.Model):
    content = ndb.TextProperty(required=True)
    author = ndb.StringProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True, required=True)
    post_key = ndb.KeyProperty(kind=Post, required=True)
    user_key = ndb.KeyProperty(kind=User, required=True)
