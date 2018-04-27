#!/usr/bin/env python
# -*- coding: utf-8 -*-

__author__ = "leo"
__time__ = "2018-04-27"


from flask import Blueprint

home = Blueprint("home", __name__)

import app.home.views

