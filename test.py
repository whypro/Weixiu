# -*- coding: utf-8 -*-
from flask import Flask, g, render_template, request, flash, redirect, url_for, session
import MySQLdb

from validate_code import create_validate_code
import StringIO

# 数据库配置
DB_HOST = 'localhost'
DB_DATABASE = 'weixiu'
DB_USERNAME = 'root'
DB_PASSWORD = 'whypro'
DB_CHARSET = 'utf8'
DB_PORT = 3306
# 
DEBUG = True
SECRET_KEY = 'development key'

app = Flask(__name__)
app.config.from_object(__name__)

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
    messages = []
    if request.method == 'POST':
        if not request.form['name']:
            error = u'姓名不能为空'
        elif not request.form['content']:
            error = u'留言内容不能为空'
        elif request.form['vcode'].upper() != session['validate'].upper():
            error = u'验证码不正确'
        else:
            cur = g.db.cursor()
            cur.execute('insert into message(name, email, content, ip) values(%s, %s, %s, %s)', (request.form['name'], request.form['email'], request.form['content'], request.remote_addr))
            g.db.commit()
            flash(u'留言成功')
            return redirect(url_for('index'))
    else:
        if session.get('logged_in'):
            cur = g.db.cursor()
            cur.execute('select user_group from people where username=%s', session.get('username'))
            row = cur.fetchone()
            if row and row[0] == 'admin':
                cur = g.db.cursor()
                cur.execute('select name, email, content, datetime, ip from message order by id desc')
                messages = [dict(name=row[0], content=row[2], datetime=row[3], ip=row[4]) for row in cur.fetchall()]
            
    return render_template('guestbook.html', messages=messages, error=error)

@app.route('/login/', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = u'用户名为空'
        else:
            cur = g.db.cursor()
            cur.execute('select username from people where username=%s and password=%s', (request.form['username'], request.form['password']))
            if not cur.rowcount > 0:
                error = u'用户名或密码不正确'
            else:
                session['logged_in'] = True
                session['username'] = request.form['username']
                flash(u'登陆成功')
                return redirect(url_for('message'))
    return render_template('login.html', error=error)

@app.route('/logout/')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash('已注销')
    return redirect(url_for('message'))

@app.route('/register/', methods=['GET', 'POST'])
def register():
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = u'用户名为空'
        else:
            cur = g.db.cursor()
            cur.execute('select username from people where username=%s', request.form['username'])
            row = cur.fetchone()
            if not row:
                cur.execute('insert into people(username, password) values(%s, %s)', (request.form['username'], request.form['password']))
                g.db.commit()
                return redirect(url_for('login'))
            else:
                error = u'用户名已存在'
                
    return render_template('register.html', error=error)

@app.route('/code/')
def get_code():
    #把strs发给前端,或者在后台使用session保存
    code_img, strs = create_validate_code()
    buf = StringIO.StringIO()
    code_img.save(buf,'PNG')

    buf_str = buf.getvalue()
    session['validate'] = strs
    response = app.make_response(buf_str)
    response.headers['Content-Type'] = 'image/png'
    return response

if __name__ == "__main__":
    app.debug = True
    app.run()
