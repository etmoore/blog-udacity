from google.appengine.ext import ndb

class User(ndb.Model):
    username = ndb.StringProperty(required=True)
    pw_hash = ndb.StringProperty(required=True)
    email = ndb.StringProperty()
