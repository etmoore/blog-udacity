from google.appengine.ext import ndb
from models import Post, User


class Like(ndb.Model):
    post_key = ndb.KeyProperty(kind=Post, required=True)
    user_key = ndb.KeyProperty(kind=User, required=True)
