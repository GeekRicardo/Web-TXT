#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File     :  main.py
@Time     :  2020/06/14 12:55:40
@Author   :  Ricardo
@Version  :  1.0
@Desc     :  小说阅读以及txt小说解析到数据库
'''

# import lib here
from flask import Flask, request, render_template, make_response, send_from_directory, redirect, url_for, session, jsonify, Response
from flask_dropzone import Dropzone
# from flask_paginate import Pagination
from datetime import timedelta
import os

from redis import Redis

from model import app, db, TXT, Chapter

dropzone = Dropzone(app)
redis = Redis(host='ali.sshug.cn', db=8, decode_responses=True)


app.config[
    'SQLALCHEMY_DATABASE_URI'] = "mysql://root:ricardo@ali.sshug.cn:3307/Ricardo?charset=utf8"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = timedelta(seconds=5)
app.secret_key = 's82;asdf4idsdf'
app.config['SESSION_TYPE'] = 'filesystem'

path = './static/txt/'
isDay = 'false'
fontsize = 18
is_login_require = True

def login_require(func):
    """
    """
    def decorator(*args, **kwargs):
        if is_login_require:
            # 现在是模拟登录，获取用户名，项目开发中获取session
            username = session.get('username', None)
            # 判断用户名存在且用户名是什么的时候直接那个视图函数
            if(username == 'ricardo'):
                return func(*args, **kwargs)
            else:
                username = request.cookies.get("username")
                if(username == 'ricardo'):
                    return func(*args, **kwargs)
                # 如果没有就重定向到登录页面
                return redirect(url_for("login"))

        else:
            return func(*args, **kwargs)
# decorator.__name__ = func.__name__
    return decorator

@app.route('/')
def index():
    txts = db.session.query(TXT)
    history = None
    if redis.get('txtid'):
        history = '/show/' + str(redis.get('txtid')) + '/' + str(redis.get('chapterid'))
        return render_template('index.html', txts = txts, history=history)
    return render_template('index.html', txts = txts)


@app.route('/login', methods=['get', 'post'])
def login():
    if(request.method == 'GET'):
        return render_template("login.html")
    else:
        username = request.form['username']
        pwd = request.form['pwd']
        response = make_response(redirect('/'))
        if(username == 'ricardo' and pwd == 'qqqqq'):
            session['username'] = 'ricardo'
            response.set_cookie('username', 'ricardo',
                                max_age=10 * 60 * 60 * 24 * 365)
        return response


@app.route('/file', methods=['POST'], endpoint='upload')
@login_require
def upload():
    # user = get_user()
    # print(str(user))
    # if user.Level > 99:
    #     # redirect('getfilelist',
    #     return render_template('index.html', msg='无权限')
    f = request.files.get('file')  # 获取文件对象
    f.save(os.path.join(path, f.filename))  # 保存文件

    parseTxt(f.filename)
    return 'ok'

def parseTxt(txt):
    txtTitle = txt.split('.txt')[0]
    txtObj = db.session.query(TXT).filter_by(title = txtTitle).first()
    if not txtObj:
        txtObj = TXT()
        txtObj.title = txtTitle
        db.session.add(txtObj)
        db.session.commit()
        txtObj = db.session.query(TXT).filter_by(title = txtObj.title).first()
    with open(path + txt, 'r', encoding='gbk') as f:
        chapter = Chapter()
        id = 1
        for line in f:
            if line[0] == '第' and '章' in line:
                db.session.add(chapter)
                db.session.commit()
                if chapter is not None:
                    print(chapter.title, "is done.")
                chapter = Chapter()
                chapter.title = line
                chapter.txtid = txtObj.id
                chapter.content += line
                chapter.chapter = id
                id += 1
            elif chapter:
                chapter.content += line


@app.route('/catalog/<int:txtid>', endpoint='getCatalog')
@login_require
def getCatalog(txtid):
    txt = db.session.query(TXT).filter_by(id=txtid).first()
    if txt:
        catalogs = db.session.query(Chapter.id, Chapter.title, Chapter.chapter, Chapter.txtid).filter_by(txtid=txtid)
        global isDay
        return render_template('catalog.html', catalogs = catalogs, txt = txt, isDay=isDay)
    else:
        return render_template('index.html', msg='无此小说.')


@app.route('/show/<int:txtid>/<int:chapterid>', endpoint='showChapter')
@login_require
def showChapter(txtid, chapterid):
    chapter = db.session.query(Chapter).filter_by(txtid=txtid, id=chapterid).first()
    if chapter:
        chapter.content = chapter.content.split('\n')
        global isDay
        global fontsize
        return render_template('chapter.html', chapter=chapter, txtid=txtid, isDay=isDay, fontsize=fontsize)
    else:
        return render_template('index.html', msg='错误✖.')

@app.route('/setDay/<int:day>', endpoint='setDayStat')
@login_require
def setDayStat(day):
    global isDay
    if(day == 1 ):
        isDay = 'false'
    elif(day == 0):
        isDay = 'true'
    return str(isDay)


@app.route('/setfont/<int:size>', endpoint='setFontSize')
@login_require
def setFontSize(size):
    global fontsize
    if(size == 1 ):
        fontsize += 2
    elif(size == 0):
        fontsize -= 2
    return str(fontsize)


@app.route('/favicon.ico')
def icon():
    return send_from_directory('static', 'favicon.ico')

if __name__ == "__main__":
    app.run('0.0.0.0', 8889, debug=True, threaded=True)
