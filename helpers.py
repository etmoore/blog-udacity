import re
import random
from string import letters
import hashlib
import hmac

def valid_username(username):
    """Confirm username is valid."""
    USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
    return USER_RE.match(username)

def valid_password(password):
    """Confirm password is valid."""
    PASSWORD_RE = re.compile(r"^.{3,20}$")
    return PASSWORD_RE.match(password)

def valid_email(email):
    """Confirm email is valid or not present."""
    EMAIL_RE = re.compile(r"^[\S]+@[\S]+.[\S]+$")
    return not email or EMAIL_RE.match(email)

def make_salt(length=5):
    """Create a random salt."""
    return ''.join(random.choice(letters) for x in range(length))

def make_pw_hash(username, password, salt=None):
    """Hash password."""
    salt = salt or make_salt()
    h = hashlib.sha256(username + password + salt).hexdigest()
    return '%s,%s' % (salt, h)

def confirm_pw(user, password):
    """Verify a password for a given user."""
    if not user:
        return False
    username = user.username
    pw_hash = user.pw_hash
    salt = pw_hash.split(',')[0]
    return make_pw_hash(username, password, salt) == pw_hash

secret = "bananabread"
def make_secure_val(value):
    """Create a secure value"""
    return '%s|%s' % (value, hmac.new(secret, value).hexdigest())

def check_secure_val(secure_value):
    """Confirm the cookie value matches its hash, if so, return the value."""
    value = secure_value.split('|')[0]
    if secure_value == make_secure_val(value):
        return value
