from flask import Flask

app = Flask(__name__)
app.config.from_object('ui_config')
from web_ui import views
