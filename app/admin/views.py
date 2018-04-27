#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "leo"
__time__ = "2018-04-27"


from . import admin


@admin.route("/")
def index():
    return "<h1>Admin</h1>"
