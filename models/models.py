from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

follows_followedby = db.Table("follows_followedby",
                              db.Column("user", db.Integer, db.ForeignKey("user.id")),
                              db.Column("follows", db.Integer, db.ForeignKey("user.id"))
                              )


class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=True)
    password = db.Column(db.String, unique=True)
    follows = db.relationship("User", secondary=follows_followedby,
                              primaryjoin=follows_followedby.c.user == id,
                              secondaryjoin=follows_followedby.c.follows == id,
                              backref="User")

    followers = db.relationship("User", secondary=follows_followedby,
                                primaryjoin=follows_followedby.c.follows == id,
                                secondaryjoin=follows_followedby.c.user == id,
                                viewonly
                                =True)

    # articles = db.relationship("Post", backref="article")

    def __init__(self, username, email, password):
        self.username = username
        self.email = email
        self.password = password

    def __str__(self):
        return "User object" + self.email

# class Post(db.Model):
#     __tablename__ = "article"
#     id = db.Column(db.Integer, autoincrement=True, primary_key=True)
#     title = db.Column(db.String)
#     description = db.Column(db.String)
#     imageUrl = db.Column(db.String)
#     timeStamp = db.Column(db.DateTime)
#     author = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
#
#
# class ArticleAuthors(db.Model):
#     __tablename__ = "article_authors"
#     article_id = db.Column(db.Integer, db.ForeignKey("article.article_id"), primary_key=True, nullable=False, )
#     user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), primary_key=True, nullable=False, )
