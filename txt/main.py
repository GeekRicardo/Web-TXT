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
import datetime
import os
import requests
import threading
from bs4 import BeautifulSoup as Soup

from redis import Redis
import cn2an

from model import app, db, TXT, Chapter
from utils import *

dropzone = Dropzone(app)
redis = Redis(host='ali.sshug.cn', db=8, decode_responses=True)


app.config[
    'SQLALCHEMY_DATABASE_URI'] = "mysql://root:ricardo@ali.sshug.cn:3307/Ricardo?charset=utf8"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = datetime.timedelta(seconds=5)
app.secret_key = 's82;asdf4idsdf'
app.config['SESSION_TYPE'] = 'filesystem'

path = './static/txt/'
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
        return render_template('index.html', txts = txts)
    return render_template('index.html', txts = txts, history=history)


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
            if '第' in line and '章' in line and ('PS' not in line or 'ps' not in line):#and (str(line).split('第')[1].split('章')[0].isdigit() or type(cn2an.cn2an(str(line).split('第')[1].split('章')[0], 'smart')) == int):
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
        return txtObj.id

def updateChapter(txtid):
    """更新已有小说章节
    
    Keyword arguments:
    txtid -- 要更新的id
    Return: None
    """
    txt = db.session.query(TXT).filter_by(id=txtid).first()
    if(not txt.url):
        # 没有爬取过章节
        results = searcherTxt(txt.title)
        for r in results:
            if r['title'] == txt.title and r['author'] == txt.author:
                txt.update({'url': r['url']})
                db.session.commit()
    else:
        catalogs = db.session.query(Chapter.title)[-1]
        print(catalogs)
        results = getChapter(txt.url)
        lastC = catalogs.title.split('章')[1].strip()
        print(lastC)
        for c in results:
            print(c)
            if lastC in c:
                break
            else:
                results.remove(c)
        if results:
            for c in results:
                chapter = Chapter()
                chapter.content = getContent(c[1])
                chapter.txtid = txt.id
                chapter.title = c[0]
                # db.session.add(chapter)
                # db.session.commit()
                print('update.', c[0])


@app.route('/catalog/<int:txtid>', endpoint='getCatalog')
@login_require
def getCatalog(txtid):
    txt = db.session.query(TXT).filter_by(id=txtid).first()
    history = None
    if txt:
        # threading._start_new_thread(updateChapter, (txt.id, ))
        catalogs = db.session.query(Chapter.id, Chapter.title, Chapter.chapter, Chapter.txtid).filter_by(txtid=txtid)
        # history = '/show/' + str(txtid) + '/' + redis.get(str(txtid)) if redis.get(str(txtid)) is not None else None
        history = redis.get(str(txtid))
        return render_template('catalog.html', catalogs = catalogs, txt = txt, history=history)
    else:
        return render_template('index.html', msg='无此小说.')


@app.route('/show/<int:txtid>/<int:chapterid>', endpoint='showChapter', methods=['GET', 'POST'])
@login_require
def showChapter(txtid, chapterid):
    if(request.method == 'GET'):
        chapter = db.session.query(Chapter).filter_by(txtid=txtid, id=chapterid).first()
        if chapter:
            chapter.content = chapter.content.split('\n')
            oldchapter = redis.get(txtid) or -1
            if int(oldchapter) < chapterid:
                redis.set(str(txtid), chapterid)
            redis.set('txtid', txtid)
            isScroll = request.cookies.get('play') or 'stop'
            isDay = 'day' if request.cookies.get('isDay') == 'night' or request.cookies.get('isDay') == None else 'day'
            fontsize = request.cookies.get('size') or '16'
            return render_template('chapter.html', chapter=chapter, txtid=txtid, isDay=isDay, fontsize=fontsize, play=isScroll, nextchapterid=chapterid+1)
        else:
            # return render_template('index.html', msg='错误✖.')
            return redirect(url_for('index'))
    else:
        if(chapterid== -1):
            chapterid = redis.get(str(txtid))
        chapter = db.session.query(Chapter).filter_by(txtid=txtid, id=chapterid).first()
        if chapter:
            chapter.content = chapter.content.split('\n')
            oldchapter = redis.get(txtid) or -1
            if int(oldchapter) < chapterid:
                redis.set(str(txtid), chapterid)
            redis.set('txtid', txtid)
            return jsonify({
                'success': 0,
                'title': chapter.title,
                'content': chapter.content
            })
        else:
            return None


@app.route('/search', endpoint='searchTxt', methods=['GET', 'POST'])
def searchTxt():
    if request.method == 'GET':
        return render_template('search.html')
    else:
        title = request.form.get('title')
        if title:
            results = searcherTxt(title)
            if results:
                return render_template('catalog.html', results=results)
        else:
            return render_template('search.html', msg='参数错误')


@app.route('/download/book/<room>', endpoint='downloadTxt')
def downloadTxt(room):
    print('room', room)
    info, chapters = getChapter('/book/' + room)
    newtxt = TXT()
    newtxt.title = info['title']
    newtxt.author = info['author']
    newtxt.url = info['url']
    db.session.add(newtxt)
    db.session.flush()
    db.session.commit()
    for c in chapters:
        chapter = Chapter()
        chapter.txtid = newtxt.id
        chapter.content = getContent(c[1])
        chapter.title = c[0]
        db.session.add(chapter)
        db.session.commit()
        print(c[0], c[1], ' is done.')
    return redirect(url_for('getCatalog', txtid=newtxt.id))


@app.route('/setDay/<day>', endpoint='setDayStat')
@login_require
def setDayStat(day):
    res = make_response(day)
    res.set_cookie('isDay', day)
    return res


@app.route('/setfont/<int:size>', endpoint='setFontSize')
@login_require
def setFontSize(size):
    res = make_response(str(size))
    res.set_cookie('size', str(size))
    return res

@app.route('/setScroll/<isScroll>', endpoint='setScroll')
@login_require
def setScroll(isScroll):
    res = make_response('')
    outdate=datetime.datetime.today() + datetime.timedelta(days=300)
    res.set_cookie('play', isScroll)
    return res

@app.route('/favicon.ico')
def icon():
    return send_from_directory('static', 'favicon.ico')

if __name__ == "__main__":
    app.run('0.0.0.0', 8889, debug=True, threaded=True)
