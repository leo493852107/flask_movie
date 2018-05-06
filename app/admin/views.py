#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "leo"
__time__ = "2018-04-27"

import os
import uuid
from datetime import datetime
from flask import render_template, redirect, url_for, flash, session, request
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash
from . import admin
from app.admin.forms import LoginForm, TagForm, MovieForm, PreviewForm, PasswordForm
from app.models import Admin, Tag, Movie, Preview, User, Comment, MovieFav, OperationLog, AdminLog, Userlog
from functools import wraps
from app import db, app


@admin.context_processor
def tpl_extra():
    """
    上下文应用处理器
    """
    data = dict(
        online_time=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    return data


def admin_login_req(f):
    """
    登录装饰器
    """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "admin" not in session:
            return redirect(url_for("admin.login", next=request.url))
        return f(*args, **kwargs)

    return decorated_function


def change_file_name(file_name):
    """
    修改文件名称
    """
    file_info = os.path.splitext(file_name)
    file_name = datetime.now().strftime("%Y%m%d%H%M%S") + str(uuid.uuid4().hex) + file_info[-1]
    return file_name


@admin.route("/")
@admin_login_req
def index():
    return render_template("admin/index.html")


@admin.route("/login/", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=data["account"]).first()
        if not admin.check_password(data["password"]):
            flash("密码错误!", category="error")
            return redirect(url_for("admin.login"))
        session["admin"] = data["account"]
        session["admin_id"] = admin.id
        # 记录到 管理员登录日志
        admin_log = AdminLog(
            admin_id=admin.id,
            ip=request.remote_addr,
        )
        db.session.add(admin_log)
        db.session.commit()
        return redirect(request.args.get("next") or url_for("admin.index"))

    return render_template("admin/login.html", form=form)


@admin.route("/logout/")
@admin_login_req
def logout():
    session.pop("admin", None)
    session.pop("admin_id", None)
    return redirect(url_for("admin.login"))


@admin.route("/password/", methods=["GET", "POST"])
@admin_login_req
def password():
    """
    修改密码
    """
    form = PasswordForm()
    if form.validate_on_submit():
        data = form.data
        admin = Admin.query.filter_by(name=session["admin"]).first()
        admin.password = generate_password_hash(data["new_password"])
        db.session.add(admin)
        db.session.commit()
        flash("修改密码成功，请重新登录！", category="ok")
        return redirect(url_for("admin.logout"))
    return render_template("admin/password.html", form=form)


@admin.route("/tag/add/", methods=["GET", "POST"])
@admin_login_req
def tag_add():
    form = TagForm()
    if form.validate_on_submit():
        data = form.data
        tag = Tag.query.filter_by(name=data["name"]).count()
        if tag == 1:
            flash("标签名称已经存在!", category="error")
            return redirect(url_for("admin.tag_add"))
        tag = Tag(
            name=data["name"]
        )
        db.session.add(tag)
        db.session.commit()
        flash("添加标签成功!", category="ok")
        oplog = OperationLog(
            admin_id=session["admin_id"],
            ip=request.remote_addr,
            reason="添加标签 %s" % data["name"],
        )
        db.session.add(oplog)
        db.session.commit()
        redirect(url_for("admin.tag_add"))
    return render_template("admin/tag_add.html", form=form)


@admin.route("/tag/list/<int:page>/", methods=["GET"])
@admin_login_req
def tag_list(page):
    """
    标签列表
    """
    if page is None:
        page = 1
    page_data = Tag.query.order_by(
        Tag.add_time.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/tag_list.html", page_data=page_data)


@admin.route("/tag/edit/<int:id>", methods=["GET", "POST"])
@admin_login_req
def tag_edit(id=None):
    """
    编辑标签
    """
    form = TagForm()
    tag = Tag.query.get_or_404(id)
    if form.validate_on_submit():
        data = form.data
        tag_count = Tag.query.filter_by(name=data["name"]).count()
        if tag.name != data["name"] and tag_count == 1:
            flash("名称已经存在!", "error")
            return redirect(url_for("admin.tag_edit", id=id))
        tag.name = data["name"]
        db.session.add(tag)
        db.session.commit()
        flash("修改标签成功!", "ok")
        redirect(url_for("admin.tag_edit", id=id))
    return render_template("admin/tag_edit.html", form=form, tag=tag)


@admin.route("/tag/del/<int:id>", methods=["GET"])
@admin_login_req
def tag_del(id=None):
    """
    删除标签
    """
    tag = Tag.query.filter_by(id=id).first_or_404()
    db.session.delete(tag)
    db.session.commit()
    flash("删除标签成功!", category="ok")
    return redirect(url_for("admin.tag_list", page=1))


@admin.route("/movie/add/", methods=["GET", "POST"])
@admin_login_req
def movie_add():
    form = MovieForm()
    if form.validate_on_submit():
        data = form.data
        url_file_name = secure_filename(form.url.data.filename)
        logo_file_name = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config["UP_DIR"]):
            os.makedirs(app.config["UP_DIR"])
            os.chmod(app.config["UP_DIR"], "rw")
        url = change_file_name(url_file_name)
        form.url.data.save(app.config["UP_DIR"] + url)
        logo = change_file_name(logo_file_name)
        form.logo.data.save(app.config["UP_DIR"] + logo)
        movie = Movie(
            title=data["title"],
            url=url,
            info=data["info"],
            logo=logo,
            star=int(data["star"]),
            play_num=0,
            comment_num=0,
            tag_id=int(data["tag_id"]),
            area=data["area"],
            length=data["length"],
            release_time=data["release_time"],
        )
        db.session.add(movie)
        db.session.commit()
        flash("添加电影成功!", category="ok")
        return redirect(url_for("admin.movie_add"))
    return render_template("admin/movie_add.html", form=form)


@admin.route("/movie/list/<int:page>/", methods=["GET"])
@admin_login_req
def movie_list(page=None):
    if page == None:
        page = 1
    page_data = Movie.query.join(Tag).filter(
        Tag.id == Movie.tag_id
    ).order_by(
        Movie.add_time.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/movie_list.html", page_data=page_data)


@admin.route("/movie/del/<int:id>", methods=["GET"])
@admin_login_req
def movie_del(id=None):
    """
    删除电影
    """
    movie = Movie.query.get_or_404(int(id))
    db.session.delete(movie)
    db.session.commit()
    flash("删除电影成功!", category="ok")
    return redirect(url_for("admin.movie_list", page=1))


@admin.route("/movie/edit/<int:id>", methods=["GET", "POST"])
@admin_login_req
def movie_edit(id=None):
    """
    编辑电影
    """
    form = MovieForm()
    form.url.validators = []
    form.logo.validators = []
    movie = Movie.query.get_or_404(int(id))
    if request.method == "GET":
        form.info.data = movie.info
        form.tag_id.data = movie.tag_id
        form.star.data = movie.star
    if form.validate_on_submit():
        data = form.data
        movie_count = Movie.query.filter_by(title=data["title"]).count()
        if movie_count == 1 and movie.title != data["title"]:
            flash("片名已经存在!", "error")

            return redirect(url_for("admin.movie_edit", id=id))
        if not os.path.exists(app.config["UP_DIR"]):
            os.makedirs(app.config["UP_DIR"])
            os.chmod(app.config["UP_DIR"], "rw")

        if form.url.data != "" and form.url.data.filename != "":
            url_file_name = secure_filename(form.url.data.filename)
            movie.url = change_file_name(url_file_name)
            form.url.data.save(app.config["UP_DIR"] + movie.url)

        if form.logo.data != "" and form.logo.data.filename != "":
            logo_file_name = secure_filename(form.logo.data.filename)
            movie.logo = change_file_name(logo_file_name)
            form.logo.data.save(app.config["UP_DIR"] + movie.logo)

        movie.title = data["title"]
        movie.info = data["info"]
        movie.tag_id = data["tag_id"]
        movie.star = data["star"]
        movie.area = data["area"]
        movie.length = data["length"]
        movie.release_time = data["release_time"]
        db.session.add(movie)
        db.session.commit()
        flash("修改电影成功!", "ok")
        redirect(url_for("admin.movie_edit", id=id))
    return render_template("admin/movie_edit.html", form=form, movie=movie)


@admin.route("/preview/add/", methods=["GET", "POST"])
@admin_login_req
def preview_add():
    form = PreviewForm()
    if form.validate_on_submit():
        data = form.data
        logo_file = secure_filename(form.logo.data.filename)
        if not os.path.exists(app.config["UP_DIR"]):
            os.makedirs(app.config["UP_DIR"])
            os.chmod(app.config["UP_DIR"], "rw")
        logo = change_file_name(logo_file)
        form.logo.data.save(app.config["UP_DIR"] + logo)
        preview = Preview(
            title=data["title"],
            logo=logo,
        )
        db.session.add(preview)
        db.session.commit()
        flash("增加预告成功!", "ok")
        redirect(url_for("admin.preview_add"))
    return render_template("admin/preview_add.html", form=form)


@admin.route("/preview/list/<int:page>/", methods=["GET"])
@admin_login_req
def preview_list(page=None):
    if page == None:
        page = 1
    page_data = Preview.query.order_by(
        Preview.add_time.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/preview_list.html", page_data=page_data)


@admin.route("/preview/del/<int:id>", methods=["GET"])
@admin_login_req
def preview_del(id=None):
    """
    删除预告
    """
    preview = Preview.query.get_or_404(int(id))
    db.session.delete(preview)
    db.session.commit()
    flash("删除预告成功!", category="ok")
    return redirect(url_for("admin.preview_list", page=1))


@admin.route("/preview/edit/<int:id>/", methods=["GET", "POST"])
@admin_login_req
def preview_edit(id):
    form = PreviewForm()
    form.logo.validators = []
    preview = Preview.query.get_or_404(int(id))
    if request.method == "GET":
        form.title.data = preview.title

    if form.validate_on_submit():
        data = form.data
        if form.logo.data != "" and form.logo.data.filename != "":
            logo_file_name = secure_filename(form.logo.data.filename)
            preview.logo = change_file_name(logo_file_name)
            form.logo.data.save(app.config["UP_DIR"] + preview.logo)

        preview.title = data["title"]

        db.session.add(preview)
        db.session.commit()
        flash("修改预告成功!", "ok")
        redirect(url_for("admin.preview_edit", id=id))
    return render_template("admin/preview_edit.html", form=form, preview=preview)


@admin.route("/user/list/<int:page>/", methods=["GET"])
@admin_login_req
def user_list(page=None):
    if page == None:
        page = 1
    page_data = User.query.order_by(
        User.add_time.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/user_list.html", page_data=page_data)


@admin.route("/user/view/<int:id>/", methods=["GET"])
@admin_login_req
def user_view(id=None):
    user = User.query.get_or_404(int(id))
    return render_template("admin/user_view.html", user=user)


@admin.route("/user/del/<int:id>", methods=["GET"])
@admin_login_req
def user_del(id=None):
    """
    删除用户
    """
    user = User.query.get_or_404(int(id))
    db.session.delete(user)
    db.session.commit()
    flash("删除用户成功!", category="ok")
    return redirect(url_for("admin.user_list", page=1))


@admin.route("/comment/list/<int:page>/", methods=["GET"])
@admin_login_req
def comment_list(page):
    if page == None:
        page = 1
    page_data = Comment.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == Comment.movie_id,
        User.id == Comment.user_id,
    ).order_by(
        Comment.add_time.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/comment_list.html", page_data=page_data)


@admin.route("/comment/del/<int:id>", methods=["GET"])
@admin_login_req
def comment_del(id=None):
    """
    删除评论
    """
    comment = Comment.query.get_or_404(int(id))
    db.session.delete(comment)
    db.session.commit()
    flash("删除评论成功!", category="ok")
    return redirect(url_for("admin.comment_list", page=1))


@admin.route("/moviecol/list/<int:page>/", methods=["GET"])
@admin_login_req
def moviecol_list(page=None):
    if page is None:
        page = 1
    page_data = MovieFav.query.join(
        Movie
    ).join(
        User
    ).filter(
        Movie.id == MovieFav.movie_id,
        User.id == MovieFav.user_id,
    ).order_by(
        MovieFav.add_time.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/moviecol_list.html", page_data=page_data)


@admin.route("/moviecol/del/<int:id>", methods=["GET"])
@admin_login_req
def moviecol_del(id=None):
    """
    删除收藏
    """
    movie_col = MovieFav.query.get_or_404(int(id))
    db.session.delete(movie_col)
    db.session.commit()
    flash("删除收藏成功!", category="ok")
    return redirect(url_for("admin.moviecol_list", page=1))


@admin.route("/oplog/list/<int:page>/", methods=["GET"])
@admin_login_req
def oplog_list(page=None):
    if page is None:
        page = 1
    page_data = OperationLog.query.join(
        Admin
    ).filter(
        Admin.id == OperationLog.admin_id,
    ).order_by(
        OperationLog.add_time.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/oplog_list.html", page_data=page_data)


@admin.route("/adminloginlog/list/<int:page>/", methods=["GET"])
@admin_login_req
def adminloginlog_list(page=None):
    if page is None:
        page = 1
    page_data = AdminLog.query.join(
        Admin
    ).filter(
        Admin.id == AdminLog.admin_id,
    ).order_by(
        AdminLog.add_time.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/adminloginlog_list.html", page_data=page_data)


@admin.route("/userloginlog/list/<int:page>/", methods=["GET"])
@admin_login_req
def userloginlog_list(page=None):
    if page is None:
        page = 1
    page_data = Userlog.query.join(
        User
    ).filter(
        User.id == Userlog.user_id,
    ).order_by(
        Userlog.add_time.desc()
    ).paginate(page=page, per_page=10)
    return render_template("admin/userloginlog_list.html", page_data=page_data)


@admin.route("/auth/add/")
@admin_login_req
def auth_add():
    return render_template("admin/auth_add.html")


@admin.route("/auth/list/")
@admin_login_req
def auth_list():
    return render_template("admin/auth_list.html")


@admin.route("/role/add/")
@admin_login_req
def role_add():
    return render_template("admin/role_add.html")


@admin.route("/role/list/")
@admin_login_req
def role_list():
    return render_template("admin/role_list.html")


@admin.route("/admin/add/")
@admin_login_req
def admin_add():
    return render_template("admin/admin_add.html")


@admin.route("/admin/list/")
@admin_login_req
def admin_list():
    return render_template("admin/admin_list.html")
