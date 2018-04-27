#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "leo"
__time__ = "2018-04-27"

from datetime import datetime


from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pymysql
from werkzeug.security import generate_password_hash

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "mysql+pymysql://root:@127.0.0.1:3306/flask_movie"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = True

db = SQLAlchemy(app)


class User(db.Model):
    """
    会员
    """
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True)
    phone = db.Column(db.String(100), unique=True)
    info = db.Column(db.Text)
    face = db.Column(db.String(100), unique=True)
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)
    uuid = db.Column(db.String(255), unique=True)
    # 会员日志外键关系关联
    user_logs = db.relationship('Userlog', backref='user')
    comments = db.relationship('Comment', backref='user')
    movie_favs = db.relationship('MovieFav', backref='user')

    def __repr__(self):
        return '<User %r>' % self.name


class Userlog(db.Model):
    """
    会员日志
    """
    __tablename__ = "user_log"
    id = db.Column(db.Integer, primary_key=True)
    # 所属会员
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    ip = db.Column(db.String(100))
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<Userlog %r>' % self.id


class Tag(db.Model):
    """
    标签
    """
    __tablename__ = "tag"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)
    # 外键关联
    movies = db.relationship("Movie", backref='tag')

    def __repr__(self):
        return '<Tag %r>' % self.name


class Movie(db.Model):
    """
    电影
    """
    __tablename__ = "movie"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), unique=True)
    url = db.Column(db.String(255), unique=True)
    info = db.Column(db.Text)
    logo = db.Column(db.String(255), unique=True)
    star = db.Column(db.SmallInteger)
    play_num = db.Column(db.BigInteger)
    comment_num = db.Column(db.BigInteger)
    tag_id = db.Column(db.Integer, db.ForeignKey('tag.id'))
    area = db.Column(db.String(255))
    length = db.Column(db.String(100))
    release_time = db.Column(db.Date)
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)
    comments = db.relationship("Comment", backref='movie')
    movie_favs = db.relationship("MovieFav", backref='movie')

    def __repr__(self):
        return '<Movie %r>' % self.title


class Preview(db.Model):
    """
    上映预告
    """
    __tablename__ = "preview"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), unique=True)
    logo = db.Column(db.String(255), unique=True)
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<Preview %r>' % self.title


class Comment(db.Model):
    """
    评论
    """
    __tablename__ = "comment"
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<Comment %r>' % self.id


class MovieFav(db.Model):
    """
    电影收藏
    """
    __tablename__ = "movie_fav"
    id = db.Column(db.Integer, primary_key=True)
    movie_id = db.Column(db.Integer, db.ForeignKey('movie.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<MovieFav %r>' % self.id


class Auth(db.Model):
    """
    权限
    """
    __tablename__ = "auth"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    url = db.Column(db.String(255), unique=True)
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<Auth %r>' % self.name


class Role(db.Model):
    """
    角色
    """
    __tablename__ = "role"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    auths = db.Column(db.String(600))
    url = db.Column(db.String(255), unique=True)
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<Role %r>' % self.name


class Admin(db.Model):
    """
    管理员
    """
    __tablename__ = "admin"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    is_super = db.Column(db.SmallInteger)   # 0 超级管理员
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))
    uuid = db.Column(db.String(255), unique=True)
    admin_logs = db.relationship("AdminLog", backref='admin')
    operation_logs = db.relationship("OperationLog", backref='admin')

    def __repr__(self):
        return '<Admin %r>' % self.name


class AdminLog(db.Model):
    """
    管理员登录日志
    """
    __tablename__ = "admin_log"
    id = db.Column(db.Integer, primary_key=True)
    # 所属管理员工
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    ip = db.Column(db.String(100))
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<AdminLog %r>' % self.id


class OperationLog(db.Model):
    """
    管理员操作日志
    """
    __tablename__ = "operation_log"
    id = db.Column(db.Integer, primary_key=True)
    # 所属管理员工
    admin_id = db.Column(db.Integer, db.ForeignKey('admin.id'))
    ip = db.Column(db.String(100))
    reason = db.Column(db.String(600))  # 操作原因
    add_time = db.Column(db.DateTime, index=True, default=datetime.now)

    def __repr__(self):
        return '<OperationLog %r>' % self.id


if __name__ == '__main__':
    # db.create_all()

    # role = Role(
    #     name="超级管理员",
    #     auths="",
    # )
    # db.session.add(role)
    # db.session.commit()

    password = input()
    admin = Admin(
        name='leo',
        password=generate_password_hash(password),
        is_super=0,
        role_id=1,
    )
    db.session.add(admin)
    db.session.commit()
