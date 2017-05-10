from functools import wraps
from models import Post, Comment, Like


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


def confirm_user_owns_post(f):
    """Displays error if the user is not the post owner."""
    @wraps(f)
    def wrapper(self, post_id, post, *args, **kwargs):
        if self.user.key == post.user_key:
            return f(self, post_id, post, *args, **kwargs)
        else:
            error = "You do not have permission to perform this action."
            post.comments = Comment.query(Comment.post_key == post.key) \
                                   .order(Comment.created).fetch()

            return self.render('post-show.html',
                               error=error,
                               user=self.user,
                               post=post)
    return wrapper


def confirm_like_allowed(f):
    """Displays error if the user has already liked a post or is post owner."""
    @wraps(f)
    def wrapper(self, post_id, post, *args, **kwargs):
        post.like_count = Like.query(Like.post_key == post.key).count()
        post.comments = Comment.query(Comment.post_key == post.key) \
                               .order(Comment.created).fetch()

        if self.user.key == post.user_key:
            error = "You cannot like your own post."
            return self.render('post-show.html',
                               error=error,
                               post=post,
                               user=self.user)

        if Like.query(Like.post_key == post.key,
                      Like.user_key == self.user.key).get():
            error = "You have already liked this post."
            return self.render('post-show.html',
                               error=error,
                               post=post,
                               user=self.user)

        else:
            return f(self, post_id, post, *args, **kwargs)
    return wrapper
