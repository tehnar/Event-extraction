from flask import redirect, url_for, render_template, request, jsonify
from web_ui import app
from flask.ext.wtf import Form
from wtforms import IntegerField, DateField, SubmitField, TextAreaField
from db import DatabaseHandler
from event import Event
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

        #TODO: del event_set
        for event in self.events:
            event.event_set = self.db_handler.get_event_set_for_event_by_id(event.id)

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

@app.route('/_load_events', methods=['POST'])
def load_events():
    events = events_wrapper.load_events(DEFAULT_ARTICLES_COUNT)
    return jsonify(result=[(db_handler.get_event_publish_date(e.id), e.json()) for e in events])

@app.route('/_delete_event', methods=['POST'])
def delete_event_by_id():
    id = request.form.get('id', 0, type=int)
    db_handler.del_event_by_id(id)
    return jsonify(result=None)

@app.route('/_get_event', methods=['POST'])
def get_event_by_id():
    id = request.form.get('id', 0, type=int)
    event = db_handler.get_event_by_id(id)
    return jsonify(result=(db_handler.get_event_publish_date(event.id), event.json()))

@app.route('/_join_events', methods=['POST'])
def join_events():
    ids = request.form.getlist('ids[]')
    join_entities1 = request.form.get('joinEntities1', 0, type=bool)
    join_actions = request.form.get('joinActions', 0, type=bool)
    join_entities2 = request.form.get('joinEntities2', 0, type=bool)

    db_handler.join_events(ids)

    if join_entities1:
        db_handler.join_entities_by_events(ids, "1")

    if join_actions:
        db_handler.join_actions_by_events(ids)

    if join_entities2:
        db_handler.join_entities_by_events(ids, "2")

    return jsonify(result=None)

def check_phrase(phrase, sentence):
    for word in phrase.split():
        if not word in sentence:
            return False
    return True

@app.route('/_modify_event', methods=['POST'])
def modify_event_by_id():
    event_id = request.form.get('id', 0, type=int)
    entity1 = request.form.get('entity1', 0, type=str)
    action = request.form.get('action', 0, type=str)
    entity2 = request.form.get('entity2', 0, type=str)

    entity1 = ' '.join(entity1.split())
    action = ' '.join(action.split())
    entity2 = ' '.join(entity2.split())

    #sentence = request.args.get('sentence', 0, type=str)
    sentence = db_handler.get_event_by_id(event_id).sentence

    if not check_phrase(entity1, sentence):
        return jsonify(result=None, error="Incorrect entity1!")
    if not check_phrase(action, sentence):
        return jsonify(result=None, error="Incorrect action!")
    if not check_phrase(entity2, sentence):
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

