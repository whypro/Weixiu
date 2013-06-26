# -*- coding: utf-8 -*-

from weixiu import app

app.config.from_object('config')
app.debug = True

if __name__ == '__main__':
    try:
       import bae
    except:
        app.run(host='0.0.0.0')

    else:
        from bae.core.wsgi import WSGIApplication
        application = WSGIApplication(app)
