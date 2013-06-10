# -*- coding: utf-8 -*-
from flask import Flask, g, render_template, request, flash, redirect, url_for, session
import MySQLdb, StringIO
from hashlib import md5
from urllib import urlencode

from validate_code import create_validate_code

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

# 首页
@app.route('/')
def index():
    return render_template('index.html')

# 重装系统页面
@app.route('/os/')
def show_os():
    return render_template('os.html')

# 各系统介绍页面
from flask import abort
@app.route('/os/<os>/')
def show_os_info(os):
    t_name = os + '.html'
    try:
        return render_template(t_name)
    except:
        abort(404)

# 留言页面
@app.route('/guestbook/', methods=['GET', 'POST'])
def leave_message():
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
            # 前台验证通过
            cur = g.db.cursor()
            cur.execute('insert into message(name, email, content, ip) values(%s, %s, %s, %s)', (request.form['name'], request.form['email'], request.form['content'], request.remote_addr))
            g.db.commit()
            flash(u'留言成功，3 秒钟内将返回首页……')
            return render_template('flash.html', target='index')
    else:
        # 分页
        #print request.args.get('page')
        if session.get('logged_in'):
            cur = g.db.cursor()
            cur.execute('select user_group from people where username=%s and user_group=%s', (session.get('username'), 'admin'))
            if cur.rowcount > 0:
                cur = g.db.cursor()
                cur.execute('select id, name, email, content, datetime, ip from message order by id desc')
                messages = [dict(id=row[0], name=row[1], content=row[3], datetime=row[4], ip=row[5]) for row in cur.fetchall()]
    return render_template('guestbook.html', messages=messages, error=error)

@app.route('/guestbook/delete/<int:id>/', methods=['GET'])
def delete_message(id):
    if request.method == 'GET':
        if session.get('logged_in'):
            cur = g.db.cursor()
            cur.execute('select user_group from people where username=%s and user_group=%s', (session.get('username'), 'admin'))
            if cur.rowcount > 0:
                cur.execute('delete from message where id=%s', id)
                if cur.rowcount > 0:
                    flash(u'删除成功，3 秒钟内将返回……')
                    g.db.commit()
                    return render_template('flash.html', target=url_for('leave_message'))
    return redirect(url_for('leave_message'))




# 登录页面
@app.route('/login/', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('index'))
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
                session['username'] = cur.fetchone()[0]
                flash(u'登陆成功，3 秒钟内将返回首页……')
                return render_template('flash.html', target=url_for('index'))

    return render_template('login.html', error=error)

# 注销
@app.route('/logout/')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    flash(u'已注销，3 秒钟内将返回首页……')
    return render_template('flash.html', target=url_for('index'))


# 注册页面
@app.route('/register/', methods=['GET', 'POST'])
def register():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = u'用户名为空'
        else:
            cur = g.db.cursor()
            cur.execute('select username from people where username=%s', request.form['username'])
            row = cur.fetchone()
            if not row:
                cur.execute('insert into people(username, password, email) values(%s, %s, %s)', (request.form['username'], request.form['password'], request.form['email']))
                g.db.commit()
                flash(u'注册成功，3 秒钟内将返回……')
                return render_template('flash.html', target=url_for('login'))
            else:
                error = u'用户名已存在'
    return render_template('register.html', error=error)

# 获取验证码
@app.route('/code/')
def get_code():
    #把strs发给前端,或者在后台使用session保存
    code_img, strs = create_validate_code(size=(100, 24), img_type="PNG")
    buf = StringIO.StringIO()
    code_img.save(buf,'PNG')

    buf_str = buf.getvalue()
    session['validate'] = strs
    response = app.make_response(buf_str)
    response.headers['Content-Type'] = 'image/png'
    return response

# 获取头像
def get_avatar(email, size):
    default = 'http://www.gravatar.com/avatar/00000000000000000000000000000000/?size=210'
    gravatar_url = 'http://www.gravatar.com/avatar/' + md5(email.lower()).hexdigest() + "?"
    gravatar_url += urlencode({'d': default, 's': str(size)})
    return gravatar_url

# 个人信息页面
@app.route('/profile/')
def show_profile():
    if session.get('logged_in'):
        avatar_url = ''
        username = session.get('username')
        cur = g.db.cursor()
        cur.execute('select email, reg_time from people where username=%s', username)
        if cur.rowcount > 0:
            row = cur.fetchone()
            email = row[0]
            if not email:
                email = ''
            reg_time = row[1].strftime('%Y-%m-%d')
            user = dict(username = username, email=email, reg_time=reg_time)
            avatar_url = get_avatar(email, 210)
            return render_template('profile.html', user=user, avatar_url=avatar_url)
    else:
        return redirect(url_for('login'))

# 加入我们页面        
@app.route('/join_us/')
def join_us():
    return render_template('join-us.html')
    
if __name__ == "__main__":
    app.debug = True
    app.run()