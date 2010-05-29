#!/usr/bin/env python

"""Simple CGI script for tiny urls

Requires sqlite. The working directory must be writable by
the webserver user.

"""

import cgi
import cgitb; cgitb.enable()  # for troubleshooting
import sqlite3
import os
import random
import re
import urllib
import urlparse

urls = {
    r'^/$': 'view',
    r'^/list$': 'list_urls',
    r'^/(.{6})$': 'load',
    }

def dispatch(urls, s):
    for k in urls.keys():
        match = re.match(k, s)
        if match:
            page = globals()[urls[k]](match.groups())
            return

def get_db_path():
    return os.path.join(os.path.dirname(os.environ['SCRIPT_FILENAME']), 'db.sqlite')

class page:
    def __init__(self, groups=None):
        getattr(self, os.environ['REQUEST_METHOD'], self.error404)(groups)
    def error404(self, groups):
        print '404'

class output_page(page):
    def __init__(self, groups=None):
        print 'Content-type: text/html'
        print
        page.__init__(self, groups)

class view(output_page):
    chars = "1234567890abcdefghijklmnopqrstuvwxyz"
    def make_id(self, length=6):
        return ''.join(random.sample(self.chars, length))
    def GET(self, groups):
        print """<html><head><title>Tinyificate it</title></head>
            <body><form method="POST"><label for="url">URL:</label>
            <input name="url" id="url" />
            <input name="submit" id="submit" type="submit" value="Tinification Commencement" />
            </form></body></html>
            """
    def POST(self, groups):
        form = cgi.FieldStorage()
        if form['url'].value:
            print """<html><head><title>Tinyificate it</title></head><body>"""
            tiny = False
            url = urlparse.urlparse(form['url'].value).geturl()
            conn = sqlite3.connect(get_db_path())
            conn.row_factory = sqlite3.Row
            c = conn.cursor()
            c.execute("CREATE TABLE IF NOT EXISTS urls (id TEXT PRIMARY KEY, url TEXT)")
            c.execute("SELECT id FROM urls WHERE url=?", (url,))
            row = c.fetchone()
            if row:
                tiny = row['id']
            else:
                tiny = False
                while tiny == False:
                    id = self.make_id()
                    c.execute("SELECT id FROM urls WHERE id=?", (id,))
                    if not c.fetchone():
                        tiny = id
                c.execute("INSERT INTO urls (id, url) VALUES (?, ?)", (tiny, url))
                conn.commit()
            full = urlparse.urljoin(urlparse.urlunparse(('http', os.environ['HTTP_HOST'], os.environ['REQUEST_URI'], '', '', '')), tiny)
            print """<a href="%s">%s</a> == %s""" % (full, full, url)
            print """</body></html>"""
        else:
            self.GET(groups)

class load(page):
    def GET(self, groups):
        conn = sqlite3.connect(get_db_path())
        c = conn.cursor()
        c.execute("SELECT url FROM urls WHERE id=?", (groups[0],))
        row = c.fetchone()
        if row:
            url = row[0]
        else:
            url = './'
        print 'Status: 301 moved permanently'
        print 'Location: ', url
        print

class list_urls(output_page):
    def GET(self, groups):
        print """<html><head><title>Tinyification list</title></head><body><ul>"""
        conn = sqlite3.connect(get_db_path())
        c = conn.cursor()
        c.execute("SELECT id, url FROM urls")
        for row in c.fetchall():
            full = urlparse.urljoin(urlparse.urlunparse(('http', os.environ['HTTP_HOST'], os.environ['REQUEST_URI'], '', '', '')), row[0])
            print """<li><a href="%s">%s</a> == <a href="%s">%s</a></li>""" % (full, full, row[1], row[1])
        print """</ul></body></html>"""

if __name__ == '__main__':
    dispatch(urls, os.environ['PATH_INFO'])
