from flask import redirect, url_for, render_template, request, jsonify
from web_ui import app
from flask.ext.wtf import Form
from wtforms import IntegerField, DateField, SubmitField, TextAreaField
from db import DatabaseHandler
from event import Event
import re
import datetime


class EventsWrapper:  # TODO: for each client there should be its own instance of this class.
    # TODO: also it should be resetted after page refresh
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
    return jsonify(result=[(db_handler.get_event_publish_date(e.id), e.json()) for e in events])

@app.route('/_delete_event')
def delete_event_by_id():
    id = request.args.get('id', 0, type=int)
    db_handler.del_event_by_id(id)
    return jsonify(result=None)

@app.route('/_get_event')
def get_event_by_id():
    id = request.args.get('id', 0, type=int)
    event = db_handler.get_event_by_id(id)
    return jsonify(result=(db_handler.get_event_publish_date(event.id), event.json()))

@app.route('/_modify_event')
def modify_event_by_id():
    event_id = request.args.get('id', 0, type=int)
    entity1 = request.args.get('entity1', 0, type=str)
    action = request.args.get('action', 0, type=str)
    entity2 = request.args.get('entity2', 0, type=str)
    sentence = request.args.get('sentence', 0, type=str)

    if not entity1 in sentence:
        return jsonify(result=None, error="Incorrect entity1!")
    if not action in sentence:
        return jsonify(result=None, error="Incorrect action!")
    if not entity2 in sentence:
        return jsonify(result=None, error="Incorrect entity2!")

    db_handler.change_event(event_id, Event(entity1, entity2, action, sentence, None))

    event = db_handler.get_event_by_id(event_id)
    return jsonify(result=(db_handler.get_event_publish_date(event.id), event.json()), error=None)

@app.route('/events', methods = ['GET', 'POST'])
def events():
    form = EventsForm()
    events_wrapper.load_events(DEFAULT_ARTICLES_COUNT)
    return render_template("events.html", form = form)


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

