from flask import redirect, url_for, render_template, request
from web_ui import app
from flask.ext.wtf import Form
from wtforms import IntegerField, DateField, SubmitField
from wtforms.validators import DataRequired
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from db import DatabaseHandler

import datetime

db_handler = DatabaseHandler()
nav = Nav()

@nav.navigation()
def main_navbar():
    return Navbar(
        'ExTractors',
        View('Events', 'events'),
    )

nav.init_app(app)


class GetArticlesForm(Form):
    article_count = IntegerField('Max articles per page', validators=[DataRequired()])
    start_date = DateField('Latest date of article', validators=[DataRequired()], format='%d.%m.%y')


class FetchArticleForm(Form):
    fetch_articles = SubmitField('Fetch new articles')


@app.route('/')
def redirect_to_events():
    return redirect(url_for('events'))


@app.route('/events', methods=['GET', 'POST'])
def events(count=10, date=datetime.datetime.now(), can_submit=True):
    form = GetArticlesForm()
    print(form.validate_on_submit(), form.errors)
    if form.validate_on_submit() and can_submit:
        print(123)
        return events(form.article_count.data, form.start_date.data, False)
    db_events = db_handler.get_events_starting_from(count, date)
    return render_template("events.html", form=form, events=db_events)