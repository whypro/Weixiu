#-*- coding:utf-8 -*-
from flask import Flask, g, render_template, request, flash, redirect, url_for, session

import MySQLdb

from bae.core import const

DB_HOST = const.MYSQL_HOST
DB_DATABASE = 'RTBLqowGxNpCGjMISBLt'
DB_USERNAME = const.MYSQL_USER
DB_PASSWORD = const.MYSQL_PASS
DB_CHARSET = 'utf8'
DB_PORT = int(const.MYSQL_PORT)
DEBUG = True
SECRET_KEY = 'development key'

app = Flask(__name__)
app.config.from_object(__name__)
app.debug = True

def connect_db():
    return MySQLdb.connect(
        host=app.config['DB_HOST'],
        user=app.config['DB_USERNAME'], 
        passwd=app.config['DB_PASSWORD'], 
        db=app.config['DB_DATABASE'],
        charset=app.config['DB_CHARSET'],
        port=app.config['DB_PORT']
    )

@app.before_request
def before_request():
    g.db = connect_db()

@app.teardown_request
def teardown_request(exception):
    g.db.close()

#@app.after_request
#def after_request():
#    g.db.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/os/')
def show_os():
    return render_template('os.html')

@app.route('/os/<os>/')
def show_os_info(os):
    t_name = os + '.html'
    return render_template(t_name)


@app.route('/hello/')
def hello():
    return 'Hello World'

@app.route('/user/<username>/')
def profile(username):
    return '%s' % username

@app.route('/guestbook/', methods=['GET', 'POST'])
def message():
    error = None
    messages = None
    if request.method == 'POST':
        if not request.form['name'] or not request.form['content']:
            error = u'提交的信息不完整'
        else:
            cur = g.db.cursor()
            cur.execute('insert into message(name, email, content, ip) values(%s, %s, %s, %s)', (request.form['name'], request.form['email'], request.form['content'], request.remote_addr))
            g.db.commit()
            flash(u'留言成功')
            return redirect(url_for('index'))
    else:
        if session.get('logged_in'):
            cur = g.db.cursor()
            cur.execute('select name, email, content, datetime, ip from message order by id desc')
            messages = [dict(name=row[0], content=row[2], datetime=row[3], ip=row[4]) for row in cur.fetchall()]
            

    return render_template('guestbook.html', messages=messages, error=error)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if request.form['username'] != 'whypro' or request.form['password'] != 'whypro':
            error = u'用户名或密码不正确'
        else:
            session['logged_in'] = True
            flash(u'登陆成功')
            return redirect(url_for('message'))
    return render_template('login.html', error=error)

@app.route('/logout/')
def logout():
    session.pop('logged_in', None)
    flash('已注销')
    return redirect(url_for('message'))
    

from bae.core.wsgi import WSGIApplication
application = WSGIApplication(app)