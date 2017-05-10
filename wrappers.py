from functools import wraps
from models import Post


def confirm_post_exists(f):
    """Return 404 if post does not exist"""
    @wraps(f)
    def wrapper(self, post_id, *args, **kwargs):
        post = Post.get_by_id(int(post_id))
        if post:
            return f(self, post_id, post, *args, **kwargs)
        else:
            return self.error(404)
    return wrapper


def confirm_logged_in(f):
    """Redirects to the login page if user is not logged in"""
    @wraps(f)
    def wrapper(self, *args, **kwargs):
        if self.user:
            return f(self, *args, **kwargs)
        else:
            return self.redirect('/login')
    return wrapper


