from google.appengine.ext import ndb
from models import Post, User


class Comment(ndb.Model):
    content = ndb.TextProperty(required=True)
    created = ndb.DateTimeProperty(auto_now_add=True, required=True)
    post_key = ndb.KeyProperty(kind=Post, required=True)
    user_key = ndb.KeyProperty(kind=User, required=True)

    def get_author(self):
        user = User.query(User.key == self.user_key).get()
        return user.username
