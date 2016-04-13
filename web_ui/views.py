from flask import redirect, url_for, render_template, request
from web_ui import app
from flask.ext.wtf import Form
from wtforms import IntegerField, DateField, SubmitField, TextAreaField
from db import DatabaseHandler

import datetime

DEFAULT_ARTICLES_COUNT = 30
db_handler = DatabaseHandler()


class EventsForm(Form):
    selected_event_id = -1
    date = TextAreaField()
    entity1 = TextAreaField()
    action = TextAreaField()
    entity2 = TextAreaField()
    sentence = TextAreaField()


class FetchArticleForm(Form):
    fetch_articles = SubmitField('Fetch new articles')


@app.route('/')
def redirect_to_events():
    return redirect(url_for('events'))


@app.route('/events', methods = ['GET', 'POST'])
def events(count = DEFAULT_ARTICLES_COUNT, date = datetime.datetime.now()):
    form = EventsForm()
    if request.method == 'POST':
        actions = ['Save', 'Modify', 'Cancel', 'Delete']
        data = {}
        event_id = None
        action = None
        for x, y in request.form.items():
            data[x] = y
            if y in actions:
                action = y
                event_id = int(x)
        if action == "Delete":
            db_handler.del_event_by_id(event_id)
        elif action == "Modify":
            form.selected_event_id = int(event_id)
            event = db_handler.get_event_by_id(event_id)
            form.date.data = event[1]
            form.entity1.data = event[2]
            form.action.data = event[4]
            form.entity2.data = event[3]
            form.sentence.data = event[5]
        elif action == "Save":
            valid = True
            sentence = data['sentence']
            for key in ['entity1', 'entity2', 'action']:
                if not data[key] in sentence:
                    valid = False
            if valid:
                db_handler.change_event(data['entity1'], data['entity2'], data['action'], sentence, event_id)
            else:
                pass  # show some message about incorrect data
    db_events = db_handler.get_events_starting_from(count, date)
    return render_template("events.html", form = form, events = db_events)


@app.route('/sources', methods = ['GET', 'POST'])
def articles():
    print(request.method)
    articles = db_handler.get_sites()
    articles_forms = [FetchArticleForm(prefix=article[0]) for article in articles]
    for form, article in zip(articles_forms, articles):
        pass  # Todo: actually fetch articles from given source

    return render_template("sources.html", articles=zip(articles, articles_forms))


@app.route('/statistics', methods=['GET', 'POST'])
def statistics():
    return render_template("statistics.html", form=Form())

