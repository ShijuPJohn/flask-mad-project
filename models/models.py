from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
class User(db.Model):
    __tablename__ = "user"
    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    username = db.Column(db.String, unique=True)
    email = db.Column(db.String, unique=True)


class Article(db.Model):
    __tablename__ = "article"
    article_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    title = db.Column(db.String)
    content = db.Column(db.String)


class ArticleAuthors(db.Model):
    __tablename__ = "article_authors"
    article_id = db.Column(db.Integer, db.ForeignKey("article.article_id"), primary_key=True, nullable=False, )
    user_id = db.Column(db.Integer, db.ForeignKey("user.user_id"), primary_key=True, nullable=False, )