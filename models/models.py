from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import DateTime, func

db = SQLAlchemy()

follows_followedby = db.Table("follows_followedby",
                              db.Column("user", db.Integer, db.ForeignKey("user.id")),
                              db.Column("follows", db.Integer, db.ForeignKey("user.id"))
                              )


class User(UserMixin, db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String, unique=True)
    imageUrl = db.Column(db.String, nullable=True, default="static/uploads/user_thumbs/pro_img1.png")
    follows = db.relationship("User", secondary=follows_followedby,
                              primaryjoin=follows_followedby.c.user == id,
                              secondaryjoin=follows_followedby.c.follows == id,
                              backref="User")

    followers = db.relationship("User", secondary=follows_followedby,
                                primaryjoin=follows_followedby.c.follows == id,
                                secondaryjoin=follows_followedby.c.user == id,
                                viewonly
                                =True)

    posts = db.relationship("Post", backref="author")
    comments = db.relationship("Comment", backref="author")

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    def __str__(self):
        return "User object" + self.email


class Comment(db.Model):
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    comment = db.Column(db.String, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    post_id = db.Column(db.Integer, db.ForeignKey("post.id"), nullable=False)

    def __str__(self):
        return "Comment with content: " + self.comment


class Post(db.Model):
    __tablename__ = "post"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    title = db.Column(db.String, nullable=False)
    description = db.Column(db.String, nullable=True)
    imageUrl = db.Column(db.String, nullable=True, default="static/uploads/post_thumbs/default_post.png")
    time_created = db.Column(DateTime(timezone=True), server_default=func.now())
    time_updated = db.Column(DateTime(timezone=True), onupdate=func.now())
    author_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    likes = db.Column(db.Integer, default=0, nullable=False)
    comments = db.relationship("Comment", backref="Post")

    def __str__(self):
        return "Post with title : " + self.title
