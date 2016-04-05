from flask import redirect, url_for
from flask import render_template
from web_ui import app
from flask.ext.wtf import Form
from wtforms import IntegerField, DateField
from wtforms.validators import DataRequired
from flask_nav import Nav
from flask_nav.elements import Navbar, View
import datetime

nav = Nav()


@nav.navigation()
def main_navbar():
    return Navbar(
        'ExTractors',
        View('Events', 'events'),
        View('Articles', 'articles'),
    )

nav.init_app(app)


class GetArticlesForm(Form):
    article_count = IntegerField('Max articles per page', validators=[DataRequired()])
    start_date = DateField('Latest date of article', validators=[DataRequired()], format='%d.%m.%y')


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
    db_events = app.db_handler.get_events_starting_from(count, date)
    return render_template("index.html", form=form, events=db_events)


@app.route('/articles')
def articles():
    return "test"