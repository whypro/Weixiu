# -*- coding: utf-8 -*-
from __future__ import division
from math import ceil
from flask import g, render_template, request, flash, redirect, url_for, session
import MySQLdb, StringIO
from hashlib import md5
from urllib import urlencode
from captcha import create_captcha
from run import app

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
def show_os_detail(os):
    t_name = os + '.html'
    try:
        return render_template(t_name)
    except:
        abort(404)

# 家庭局域网页面
@app.route('/network/')
def show_home_network():
    return render_template('home-network.html')
        
# 查看留言页面
@app.route('/guestbook/', defaults={'page': 1}, methods=['GET'])
@app.route('/guestbook/page/<int:page>/', methods=['GET'])
def show_message(page):
    messages = []
    total_pages = 0
    # 分页
    messages_per_page = 5
    offset = (page - 1) * messages_per_page
    if session.get('logged_in'):
        cur = g.db.cursor()
        if is_admin(session.get('username')):
            cur.execute('select id from message order by id desc')
            total_messages = cur.rowcount
            total_pages = int(ceil(total_messages / messages_per_page))
            cur.execute('select id, name, email, content, datetime, ip from message order by id desc limit %s, %s', (offset, messages_per_page))
            if page != 1 and not cur.rowcount:
                abort(404)
            messages = [dict(id=row[0], name=row[1], content=row[3], datetime=row[4], ip=row[5]) for row in cur.fetchall()]
        else:
            cur.execute('select id from message where name=%s order by id desc', session.get('username'))
            total_messages = cur.rowcount
            total_pages = total_messages / messages_per_page
            cur.execute('select id, name, email, content, datetime, ip from message where name=%s order by id desc limit %s, %s', (session.get('username'), offset, messages_per_page))
            if page != 1 and not cur.rowcount:
                abort(404)
            messages = [dict(id=row[0], name=row[1], content=row[3], datetime=row[4], ip=row[5]) for row in cur.fetchall()]
    print messages
    return render_template('guestbook.html', messages=messages, cur_page=page, total_pages=total_pages)
    
    
    
# 联系我们页面 
@app.route('/contact/', methods=['GET', 'POST'])
def leave_message():
    error = None
    user = None
    id = None
    if session.get('logged_in'):
        cur = g.db.cursor()
        cur.execute('select username, email from people where username=%s', session.get('username'))
        row = cur.fetchone()
        user = dict(name=row[0], email=row[1])
        
    if request.method == 'POST':
        if not request.form['name']:
            error = u'姓名不能为空'
        elif not request.form['content']:
            error = u'留言内容不能为空'
        elif request.form['vcode'].upper() != session['validate'].upper():
            error = u'验证码不正确'
        else:
            # 前台验证通过
            if session.get('logged_in'):
                cur = g.db.cursor()
                cur.execute('select id from people where username=%s', session.get('username'))
                id = cur.fetchone()[0]
            cur = g.db.cursor()
            cur.execute('insert into message(people_id, name, email, content, ip) values(%s, %s, %s, %s, %s)', (id, request.form['name'], request.form['email'], request.form['content'], request.remote_addr))
            print 
            g.db.commit()
            flash(u'留言成功，3 秒钟内将返回首页……')
            return render_template('flash.html', target=url_for('index'))
    return render_template('contact.html', user=user, error=error)

def is_admin(username):
    cur = g.db.cursor()
    cur.execute('select user_group from people where username=%s and user_group=%s', (username, 'admin'))
    if cur.rowcount > 0:
        return True
    else:
        return False
    
@app.route('/guestbook/delete/<int:id>/', methods=['GET'])
def delete_message(id):
    if session.get('logged_in'):
        if is_admin(session.get('username')):
            cur = g.db.cursor()
            cur.execute('delete from message where id=%s', id)
            if cur.rowcount > 0:
                flash(u'删除成功，3 秒钟内将返回留言页面……')
                g.db.commit()
        else:
            flash(u'权限不足，3 秒钟内将返回留言页面……')
            # abort(404)
        return render_template('flash.html', target=url_for('leave_message'))
    else:
        # flash(u'请先登录，3 秒钟内将转到登录页面……')
        # return render_template('flash.html', target=url_for('login'))
        abort(404)
        
# 登录页面
@app.route('/login/', methods=['GET', 'POST'])
def login():
    if session.get('logged_in'):
        return redirect(url_for('index'))
    error = None
    if request.method == 'POST':
        if not request.form['username']:
            error = u'用户名不能为空'
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
            error = u'用户名不能为空'
        elif not request.form['password']:
            error = u'密码不能为空'
        elif request.form['vcode'].upper() != session['validate'].upper():
            error = u'验证码不正确'
        else:
            cur = g.db.cursor()
            cur.execute('select username from people where username=%s', request.form['username'])
            row = cur.fetchone()
            if not row:
                cur.execute('insert into people(username, password, email) values(%s, %s, %s)', (request.form['username'], request.form['password'], request.form['email']))
                g.db.commit()
                flash(u'注册成功，3 秒钟内将转到登陆页面……')
                return render_template('flash.html', target=url_for('login'))
            else:
                error = u'用户名已存在'
    return render_template('register.html', error=error)

# 获取验证码
@app.route('/captcha/')
def get_captcha():
    #把strs发给前端,或者在后台使用session保存
    code_img, strs = create_captcha(size=(100, 24), img_type="PNG")
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
@app.route('/profile/', methods=['GET', 'POST'])
def show_profile():
    if request.method == 'POST':
        if session.get('logged_in'):
            cur = g.db.cursor()
            cur.execute('update people set email=%s where username=%s', (request.form['email'], session.get('username')))
            g.db.commit()
            flash(u'更改成功，3 秒钟内将转到个人页面……')
            return render_template('flash.html', target=url_for('show_profile'))
        else:
            return redirect(url_for('login'))
    else:
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
@app.route('/join/')
def show_join():
    return render_template('join.html')

    
@app.route('/goods/', methods=['GET'])
def show_goods():
    goods = []
    cur = g.db.cursor()
    cur.execute('select goods.id, name, brand, url from goods left join goods_photo on goods.id = goods_photo.goods_id group by goods.id order by click desc')
    if cur.rowcount > 0:
        goods = [dict(id=row[0], name=row[1], brand=row[2], photo=row[3]) for row in cur.fetchall()]
    return render_template('goods.html', goods=goods, show_manage_btn=is_admin(session.get('username')))
        

@app.route('/goods/<int:id>/', methods=['GET'])
def show_goods_detail(id):
    cur = g.db.cursor()
    cur.execute('select name, price, detail, brand from goods where id=%s', id)
    if cur.rowcount > 0:
        row = cur.fetchone()
        goods = dict(id=id, name=row[0], price=row[1], detail=row[2], brand=row[3])
        cur.execute('select url from goods_photo where goods_id=%s', id)
        if cur.rowcount > 0:
            rows = cur.fetchall()
            goods['photos'] = [row[0] for row in rows]
        cur.execute('update goods set click=click+1 where id=%s', id)
        g.db.commit()
        return render_template('goods-detail.html', goods=goods)
    else:
        abort(404)
        
@app.route('/goods/add/', methods=['GET', 'POST'])
def add_goods():
    if session.get('logged_in'):
        if is_admin(session.get('username')):
            error = ''
            if request.method == 'POST':
                if not request.form['id']:
                    error = u'商品编号不能为空'
                elif not request.form['name']:
                    error = u'商品名称不能为空'
                elif request.form['vcode'].upper() != session['validate'].upper():
                    error = u'验证码不正确'
                else:
                    cur = g.db.cursor()
                    cur.execute('insert into goods(id, name, price, detail, brand) values(%s, %s, %s, %s, %s)', (request.form['id'], request.form['name'], request.form['price'], request.form['detail'], request.form['brand']))
                    g.db.commit()
                    flash(u'添加成功，3 秒钟内将转到商品页面……')
                    return render_template('flash.html', target=url_for('show_goods_detail', id=request.form['id']))
            return render_template('goods-add.html', error=error)
        else:
            flash(u'权限不足，3 秒钟内将转到首页……')
            return render_template('flash.html', target=url_for('index'))
    else:
        # flash(u'请先登录，3 秒钟内将转到登录页面……')
        # return render_template('flash.html', target=url_for('login'))
        abort(404)

@app.route('/goods/modify/<int:id>/', methods=['GET', 'POST'])
def modify_goods(id):
    if session.get('logged_in'):
        if is_admin(session.get('username')):
            error = ''
            cur = g.db.cursor()
            cur.execute('select name, price, detail, brand from goods where id=%s', id)
            row = cur.fetchone()
            goods = dict(id=id, name=row[0], price=row[1], detail=row[2], brand=row[3]) 
            if request.method == 'POST':
                if not request.form['name']:
                    error = u'商品名称不能为空'
                elif request.form['vcode'].upper() != session['validate'].upper():
                    error = u'验证码不正确'
                else:
                    cur = g.db.cursor()
                    cur.execute('update goods set name=%s, price=%s, detail=%s, brand=%s where id=%s', (request.form['name'], request.form['price'], request.form['detail'], request.form['brand'], id))
                    g.db.commit()
                    flash(u'更新成功，3 秒钟内将转到商品页面……')
                    return render_template('flash.html', target=url_for('show_goods_detail', id=id))
            
            return render_template('goods-modify.html', goods=goods, error=error)
        else:
            flash(u'权限不足，3 秒钟内将转到首页……')
            return render_template('flash.html', target=url_for('index'))
    else:
        # flash(u'请先登录，3 秒钟内将转到登录页面……')
        # return render_template('flash.html', target=url_for('login'))
        abort(404)
    
@app.route('/goods/delete/<int:id>/', methods=['GET'])
def delete_goods(id):
    if session.get('logged_in'):
        if is_admin(session.get('username')):
            cur = g.db.cursor()
            cur.execute('delete from goods where id=%s', id)
            if cur.rowcount > 0:
                flash(u'删除成功，3 秒钟内将返回商品页面……')
                g.db.commit()
        else:
            flash(u'权限不足，3 秒钟内将返回商品页面……')
        return render_template('flash.html', target=url_for('show_goods'))
    else:
        # flash(u'请先登录，3 秒钟内将转到登录页面……')
        # return render_template('flash.html', target=url_for('login'))
        abort(404)

        
@app.route('/goods/<int:id>/photo/add/', methods=['GET', 'POST'])
def add_goods_photo(id):
    if session.get('logged_in'):
        if is_admin(session.get('username')):
            error = ''
            if request.method == 'POST':
                if not request.form['photo-1'] and not request.form['photo-2'] and not request.form['photo-3']:                
                    error = u'图片地址不能为空'
                elif request.form['vcode'].upper() != session['validate'].upper():
                    error = u'验证码不正确'
                else:
                    cur = g.db.cursor()
                    photos = [request.form['photo-1'], request.form['photo-2'], request.form['photo-3']]
                    for photo in photos:
                        if photo:
                            cur.execute('insert into goods_photo(goods_id, url) values(%s, %s)', (id, photo))
                    g.db.commit()
                    flash(u'添加成功，3 秒钟内将转到商品页面……')
                    return render_template('flash.html', target=url_for('show_goods'))
            return render_template('goods-photo-add.html', error=error)
        else:
            flash(u'权限不足，3 秒钟内将转到首页……')
            return render_template('flash.html', target=url_for('index'))
    else:
        # flash(u'请先登录，3 秒钟内将转到登录页面……')
        # return render_template('flash.html', target=url_for('login'))
        abort(404)

@app.route('/service/', methods=['GET'])        
def show_service():
    return render_template('service.html')

# 错误处理   
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/404/')
def test_404():
    abort(404)

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('500.html'), 500

@app.route('/500/')
def test_500():
    abort(500)

@app.errorhandler(403)
def forbidden(e):
    return render_template('403.html'), 403

@app.route('/403/')
def test_403():
    abort(403)