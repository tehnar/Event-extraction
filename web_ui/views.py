from flask import redirect, url_for, render_template, request
from web_ui import app
from flask.ext.wtf import Form
from wtforms import IntegerField, DateField, SubmitField
from wtforms.validators import DataRequired
from flask_nav import Nav
from flask_nav.elements import Navbar, View
import datetime

DEFAULT_ARTICLES_COUNT = 30

class EventsForm(Form):
    selected_event_id = -1

class FetchArticleForm(Form):
    fetch_articles = SubmitField('Fetch new articles')

@app.route('/')
def redirect_to_events():
    return redirect(url_for('events'))

@app.route('/events', methods = ['GET', 'POST'])
def events(count = DEFAULT_ARTICLES_COUNT, date = datetime.datetime.now()):
    form = EventsForm()
    print(form.selected_event_id)
    if request.method == 'POST':
        for event_id, action in request.form.items():
            if action == "Delete":
                app.db_handler.del_event_by_id(event_id)
            elif action == "Modify":
                form.selected_event_id = int(event_id)

    db_events = app.db_handler.get_events_starting_from(count, date)
    return render_template("events.html", form = form, events = db_events)

@app.route('/sources', methods = ['GET', 'POST'])
def articles():
    print(request.method)
    articles = app.db_handler.get_sites()
    articles_forms = [FetchArticleForm(prefix=article[0]) for article in articles]
    for form, article in zip(articles_forms, articles):
        pass  # Todo: actually fetch articles from given source

    return render_template("sources.html", articles=zip(articles, articles_forms))

@app.route('/statistics', methods=['GET', 'POST'])
def statistics():
    return render_template("statistics.html", form=Form())
