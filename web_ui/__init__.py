from flask import Flask
from flask_bootstrap import Bootstrap
from web_ui import views

app = Flask(__name__)
Bootstrap(app)
app.config.from_object('ui_config')
