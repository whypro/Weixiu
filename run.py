# -*- coding: utf-8 -*-
import os
from flask import Flask
app = Flask(__name__)
app.config.from_object('config')
app.debug = True
from views import *


if 'SERVER_SOFTWARE' in os.environ:
    from bae.core.wsgi import WSGIApplication
    application = WSGIApplication(app)
elif __name__ == '__main__':
    app.run()
