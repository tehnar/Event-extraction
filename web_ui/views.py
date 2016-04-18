from flask import redirect, url_for, render_template, request, jsonify
from web_ui import app
from flask.ext.wtf import Form
from wtforms import IntegerField, DateField, SubmitField, TextAreaField
from db import DatabaseHandler
from event import Event
import datetime

class EventsWrapper:
    def __init__(self, db_handler):
        self.db_handler = db_handler
        self.events = None
        self.events_count = 0
        self.current_index = 0

    def __load_events__(self, count):
        self.events = self.db_handler.get_events_starting_from(count, datetime.datetime.now())
        self.events_count = len(self.events)

    def load_events(self, count):
        if self.current_index + count >= self.events_count:
            self.__load_events__(self.current_index + count)

        start_index = self.current_index
        self.current_index = min(self.current_index + count, self.events_count)
        return self.events[start_index : self.current_index]

DEFAULT_ARTICLES_COUNT = 10
db_handler = DatabaseHandler()
events_wrapper = EventsWrapper(db_handler)


class EventsForm(Form):
    selected_event_id = -1
    publish_date = TextAreaField()
    entity1 = TextAreaField()
    action = TextAreaField()
    entity2 = TextAreaField()
    date = TextAreaField()
    sentence = TextAreaField()


class FetchArticleForm(Form):
    fetch_articles = SubmitField('Fetch new articles')


@app.route('/')
def redirect_to_events():
    return redirect(url_for('events'))

@app.route('/_load_events')
def load_events():
    events = events_wrapper.load_events(DEFAULT_ARTICLES_COUNT)
    return jsonify(result=events)

@app.route('/events', methods = ['GET', 'POST'])
def events():
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
            form.publish_date.data = db_handler.get_event_publish_date(event_id)
            form.entity1.data = event.entity1
            form.action.data = event.action
            form.entity2.data = event.entity2
            form.sentence.data = event.sentence
            form.date.data = event.date

        elif action == "Save":
            valid = True
            sentence = data['sentence']
            for key in ['entity1', 'entity2', 'action']:
                if not data[key] in sentence:
                    valid = False
            if valid:
                db_handler.change_event(event_id, Event(data['entity1'], data['entity2'], data['action'], sentence,
                                                        data['date']))
            else:
                pass  # show some message about incorrect data

    events_wrapper.load_events(DEFAULT_ARTICLES_COUNT)
    db_events = db_handler.get_events_starting_from(events_wrapper.current_index, datetime.datetime.now())
    db_events = zip(db_events, [db_handler.get_event_publish_date(event.id) for event in db_events])
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

