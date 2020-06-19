#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File     :  model.py
@Time     :  2020/06/14 12:56:26
@Author   :  Ricardo
@Version  :  1.0
@Desc     :  小说相关模型类
'''

# import lib here

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

db = SQLAlchemy(app)

class TXT(db.Model):
    __tablename__ = "txt"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    author = db.Column(db.String(50))

    def __str__(self):
        return "[{}] - ({})".format(self.title, self.author)

class Chapter(db.Model):
    __tablename__ = "chapter"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    chapter = db.Column(db.Integer)
    content = db.Column(db.Text)
    txtid = db.Column(db.Integer)

    def __init__(self):
        super().__init__()
        self.content = ''

    def __str__(self):
        return "[{}] - ({})".format(self.title, self.chapter)