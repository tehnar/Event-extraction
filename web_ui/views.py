from flask import session, redirect, url_for, render_template, request, jsonify
from web_ui import app
from flask.ext.wtf import Form
from wtforms import SubmitField, TextAreaField
from db import DatabaseHandler
from event import Event
import datetime
import editdistance
import numpy
import threading


DEFAULT_ARTICLES_COUNT = 10
db_handler = DatabaseHandler()

MERGE_PROGRESS = 0

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

def get_extended_event(id):
    event = db_handler.get_event_by_id(id)
    event.pdate = db_handler.get_event_publish_date(id)
    event.url = db_handler.get_event_source(id).url
    return event

@app.route('/_load_events_merge', methods=['POST'])
def load_events_merge():
    event_pairs = db_handler.get_events_merge()

    events = []
    for pair in event_pairs:
        events.append((get_extended_event(pair[0]), get_extended_event(pair[1])))

    return jsonify(result=[(pair[0].json(), pair[1].json()) for pair in events])


@app.route('/_load_events', methods=['POST'])
def load_events():
    session["start_index"] = session["current_index"]
    session["current_index"] += DEFAULT_ARTICLES_COUNT
    events = db_handler.get_events_starting_from(session["current_index"], datetime.datetime.now())

    return jsonify(result=[get_extended_event(e.id).json() for e in events[session["start_index"]: session["current_index"]]])


@app.route('/_delete_event', methods=['POST'])
def delete_event_by_id():
    id = request.form.get('id', 0, type=int)
    db_handler.del_event_by_id(id)
    return jsonify(result=None)

def thread_full_auto_merge():
    auto_merge(db_handler.get_event_ids())

#TODO: remove
@app.route('/_full_auto_merge', methods=['POST'])
def full_auto_merge():
    t1 = threading.Thread(target=thread_full_auto_merge)
    t1.start()
    return jsonify(result=None)

@app.route('/_get_merge_progress', methods=['POST'])
def get_merge_progress():
    return jsonify(result=MERGE_PROGRESS)

@app.route('/_get_event', methods=['POST'])
def get_event_by_id():
    id = request.form.get('id', 0, type=int)
    return jsonify(result=get_extended_event(id).json())

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

    return jsonify(result=MERGE_PROGRESS)


def check_phrase(phrase, sentence):
    for word in phrase.split():
        if not word in sentence:
            return False
    return True

def are_same_sentences(text1, text2):
    return 100 * editdistance.eval(text1, text2) / numpy.average([len(text1), len(text2)])

def are_same(id1, id2):
    entity11_id, action1_id, entity12_id = db_handler.get_entity_core_id_by_event_id(id1)
    entity21_id, action2_id, entity22_id = db_handler.get_entity_core_id_by_event_id(id2)

    entity11_id = db_handler.get_entity_set_by_entity_id(entity11_id)
    entity21_id = db_handler.get_entity_set_by_entity_id(entity21_id)

    if entity11_id != entity21_id:
        return False


    action1_id = db_handler.get_action_set_by_action_id(action1_id)
    action2_id = db_handler.get_action_set_by_action_id(action2_id)

    if action1_id != action2_id:
        return False

    # cmp sentences
    text_delta = are_same_sentences(db_handler.get_entity_by_id(entity12_id), db_handler.get_entity_by_id(entity22_id))
    if text_delta > 50:
        return False

    print("Same events: " + str(id1) + " " + str(id2) + "(" + str(text_delta) + ")")
    print(db_handler.get_entity_by_id(entity11_id), db_handler.get_action_by_id(action1_id), db_handler.get_entity_by_id(entity12_id))
    print(db_handler.get_entity_by_id(entity21_id), db_handler.get_action_by_id(action2_id), db_handler.get_entity_by_id(entity22_id))

    return True

def auto_merge(event_ids):
    global MERGE_PROGRESS

    events_count = len(event_ids)

    MERGE_PROGRESS = 0
    total_count = (events_count * (events_count - 1)) / 2
    count = 0

    for i1 in range(0, events_count):
        for i2 in range(i1 + 1, events_count):
            if are_same(event_ids[i1], event_ids[i2]):
                #TODO: change handler
                db_handler.add_events_to_events_merge(event_ids[i1], event_ids[i2])

            count += 1
            MERGE_PROGRESS = 100 * count / total_count

@app.route('/_modify_event', methods=['POST'])
def modify_event_by_id():
    event_id = request.form.get('id', 0, type=int)
    entity1 = request.form.get('entity1', 0, type=str)
    action = request.form.get('action', 0, type=str)
    entity2 = request.form.get('entity2', 0, type=str)

    print("Modified event: " + str(event_id))

    entity1 = ' '.join(entity1.split())
    action = ' '.join(action.split())
    entity2 = ' '.join(entity2.split())

    sentence = db_handler.get_event_by_id(event_id).sentence

    if not check_phrase(entity1, sentence):
        return jsonify(result=None, error="Incorrect entity1!")
    if not check_phrase(action, sentence):
        return jsonify(result=None, error="Incorrect action!")
    if not check_phrase(entity2, sentence):
        return jsonify(result=None, error="Incorrect entity2!")

    db_handler.change_event(event_id, Event(entity1, entity2, action, sentence, None))

    return jsonify(result=get_extended_event(event_id).json(), error=None)


@app.route('/events', methods = ['GET', 'POST'])
def events():
    form = EventsForm()
    session["start_index"] = session["current_index"] = 0
    return render_template("events.html", form=form)


@app.route('/sources', methods = ['GET', 'POST'])
def articles():
    print(request.method)
    articles = db_handler.get_sites()
    articles_forms = [FetchArticleForm(prefix=article[0]) for article in articles]
    for form, article in zip(articles_forms, articles):
        pass  # Todo: actually fetch articles from given source

    return render_template("sources.html", articles=zip(articles, articles_forms))


@app.route('/merge', methods=['GET', 'POST'])
def statistics():
    return render_template("merge.html", form=Form())

