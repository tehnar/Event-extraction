from flask import render_template
from web_ui import app
from flask.ext.wtf import Form
from wtforms import IntegerField
from wtforms.fields.html5 import DateField
from wtforms.validators import DataRequired

import datetime


class GetArticlesForm(Form):
    article_count = IntegerField('Max articles per page', validators=[DataRequired()])
    start_date = DateField('Latest date of article', validators=[DataRequired()])


@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index(count=10, date=datetime.datetime.now(), can_submit=True):
    form = GetArticlesForm()
    if form.validate_on_submit() and can_submit:
        return index(form.article_count.data, form.start_date.data, False)
    events = app.db_handler.get_events_starting_from(count, date)
    return render_template("index.html", form=form, events=events)

