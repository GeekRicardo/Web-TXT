#!/usr/bin/env python
# -*- encoding: utf-8 -*-
'''
@File     :  utils.py
@Time     :  2020/06/26 18:43:28
@Author   :  Ricardo
@Version  :  1.0
@Desc     :  小说爬取等相关
'''

# import lib here
import random
import requests
from bs4 import BeautifulSoup as Soup

baseURL = 'https://www.biquge5200.cc/'

proxies = [
    {'http': 'http://ali.sshug.cn:9587'},
    {'http': 'http://hu.sshug.cn:9587'},
    {'http': 'http://pangfoud.sshug.cn:9587'},
]

headers = [
    {'Accept': '*/*',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/81.0.4044.129 Safari/537.36',
    'Connection': 'keep-alive',
    'Referer': 'https://www.biquge.com.cn/'},
    {'Accept': '*/*',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1',
    'Connection': 'keep-alive',
    'Referer': 'https://www.biquge.com.cn/'},
    {'Accept': '*/*',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (iPad; CPU OS 11_0 like Mac OS X) AppleWebKit/604.1.34 (KHTML, like Gecko) Version/11.0 Mobile/15A5341f Safari/604.1',
    'Connection': 'keep-alive',
    'Referer': 'https://www.biquge.com.cn/'},
    {'Accept': '*/*',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36',
    'Connection': 'keep-alive',
    'Referer': 'https://www.biquge.com.cn/'},
]

cookie = None

def searcherTxt(txtTitle):
    path = 'modules/article/search.php?searchkey='
    res = requests.get(baseURL + path + txtTitle, proxies=random.choice(proxies), headers = random.choice(headers))
    if res.status_code == 200:
        results = []
        soup = Soup(res.text, 'html.parser')
        alldiv = soup.select('.grid tr')
        for div in alldiv:
            results.append({
                'title': div.find('h3').text.strip(),
                'author': div.find_all('p',attrs={'class':'result-game-item-info-tag'})[0].text.strip(),
                'type': div.find_all('p',attrs={'class':'result-game-item-info-tag'})[1].text.strip(),
                'updatetime': div.find_all('p',attrs={'class':'result-game-item-info-tag'})[2].text.strip(),
                'url': div.find('a', attrs={'class':'result-game-item-title-link'})['href']
            })
        return results
    else:
        print(res.status_code, res.text)
        return None

def getChapter(txtURL):
    uri = baseURL + txtURL.lstrip('/') + '/'
    print(uri)
    res = requests.get(uri, headers = random.choice(headers), proxies=random.choice(proxies))
    if res.status_code == 200:
        results = []
        global cookie
        cookie = res.cookies
        print(cookie, res.cookies.get_dict())
        soup = Soup(res.text, 'html.parser')
        links = soup.select('#list a')
        infodiv = soup.find('div', attrs={'id':'maininfo'})
        title = infodiv.find('h1').text
        author = infodiv.find('p').text.split('：')[1]
        for a in links:
            results.append((a.text, a['href']))
        return {'title':title, 'author':author, 'url': txtURL}, results
    else:
        print('getChapter - ', res.status_code, res.text)
        return None, None

def getContent(chapterURL):
    uri = baseURL + chapterURL.lstrip('/')
    print(uri)
    res = requests.get(baseURL + chapterURL)#, proxies=random.choice(proxies), headers = random.choice(headers), cookies=cookie)
    if res.status_code == 200:
        results = []
        soup = Soup(res.text, 'html.parser')
        content = soup.find('div', attrs={'id': 'content'}).text.replace('\xa0\xa0\xa0\xa0', '\n')
        return content
    else:
        print('getContent - ', res.status_code, res.text)
        return None

