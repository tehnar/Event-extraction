import datetime
import threading

import editdistance
import numpy
import os.path

from flask import redirect, url_for, render_template, request, jsonify
from threading import Thread
from data_mining.downloaders import article_downloaders

from db import DatabaseHandler
from event import Event
from web_ui import app


class Settings:
    root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    FILE_NAME = os.path.join(root_dir, "settings.txt")

    def get_last_processed_event_id(self):
        f = open(self.FILE_NAME, "r")
        last_id = f.read()
        f.close()
        return int(last_id)

    def put_last_processed_event_id(self, last_id):
        f = open(self.FILE_NAME, "w")
        f.write(str(last_id))
        f.close()


DEFAULT_ARTICLES_COUNT = 10
db_handler = DatabaseHandler()
settings = Settings()
MERGE_PROGRESS = 0

@app.route('/')
def redirect_to_events():
    return redirect(url_for('events'))


def get_events_group(id):
    id = db_handler.get_event_set_for_event_by_id(id)
    events_ids = db_handler.get_events_set_by_id(id)

    events = [get_extended_event(id)]
    for event_id in events_ids:
        if event_id != id:
            events.append(get_extended_event(event_id))

    return events


def get_extended_event(id):
    event = db_handler.get_event_by_id(id)
    event.pdate = db_handler.get_event_publish_date(id)
    event.url = db_handler.get_event_source(id).url
    event.main_entity1, event.main_action, event.main_entity2 = db_handler.get_main_entity_core_by_event_id(id)
    return event


@app.route('/_get_events_merge_count', methods=['POST'])
def get_events_merge_count():
    return jsonify(result=len(db_handler.get_events_merge()))


@app.route('/_load_events_merge', methods=['POST'])
def load_events_merge():
    events_merge = db_handler.get_events_merge()

    events = []
    for entry in events_merge:
        events.append((entry[0], get_extended_event(entry[1]), get_extended_event(entry[2])))

    return jsonify(result=[(entry[0], entry[1].json(), entry[2].json()) for entry in events])


@app.route('/_load_events', methods=['POST'])
def load_events():
    event_cnt = request.form.get('event_cnt', 0, type=int)
    query = request.form.get('query', "", type=str)
    params = query.split('site:')
    site = ""
    pattern = params[0]
    if len(params) > 1:
        site = params[1]
    events = db_handler.get_events_starting_from(event_cnt + DEFAULT_ARTICLES_COUNT, datetime.datetime.now(),
                                                 pattern, site)

    return jsonify(result=[[x.json() for x in get_events_group(e.id)] for e in
                           events[event_cnt: event_cnt + DEFAULT_ARTICLES_COUNT]])


@app.route('/_delete_events_merge', methods=['POST'])
def delete_events_merge():
    id = request.form.get('id', 0, type=int)
    db_handler.del_event_merge_by_id(id)
    return jsonify(result=None)


@app.route('/_delete_event', methods=['POST'])
def delete_event_by_id():
    id = request.form.get('id', 0, type=int)
    db_handler.del_event_by_id(id)
    return jsonify(result=None)


@app.route('/_auto_merge', methods=['POST'])
def run_auto_merge():
    t1 = threading.Thread(target=auto_merge)
    t1.start()
    return jsonify(result=None)


@app.route('/_get_merge_progress', methods=['POST'])
def get_merge_progress():
    return jsonify(result=MERGE_PROGRESS)


@app.route('/_get_event', methods=['POST'])
def get_event_by_id():
    id = request.form.get('id', 0, type=int)
    return jsonify(result=get_extended_event(id).json())


@app.route('/_get_group', methods=['POST'])
def get_group_by_id():
    id = request.form.get('id', 0, type=int)
    return jsonify(result=[x.json() for x in get_events_group(id)])


@app.route('/_join_events_merge', methods=['POST'])
def join_events_merge():
    id = request.form.get('id', 0, type=int)
    join_entities1 = request.form.get('joinEntities1', "", type=str) == 'true'
    join_actions = request.form.get('joinActions', "", type=str) == 'true'
    join_entities2 = request.form.get('joinEntities2', "", type=str) == 'true'

    ids = db_handler.get_event_merge_by_id(id)
    db_handler.join_events(ids)

    if join_entities1:
        db_handler.join_entities_by_events(ids, "1")

    if join_actions:
        db_handler.join_actions_by_events(ids)

    if join_entities2:
        db_handler.join_entities_by_events(ids, "2")

    db_handler.del_event_merge_by_id(id)

    return jsonify()


@app.route('/_join_events', methods=['POST'])
def join_events():
    ids = request.form.getlist('ids[]')
    join_entities1 = request.form.get('joinEntities1', "", type=str) == 'true'
    join_actions = request.form.get('joinActions', "", type=str) == 'true'
    join_entities2 = request.form.get('joinEntities2', "", type=str) == 'true'

    db_handler.join_events(ids)

    if join_entities1:
        db_handler.join_entities_by_events(ids, "1")

    if join_actions:
        db_handler.join_actions_by_events(ids)

    if join_entities2:
        db_handler.join_entities_by_events(ids, "2")

    return jsonify()


def check_phrase(phrase, sentence):
    for word in phrase.split():
        if word not in sentence:
            return False
    return True


def are_same_sentences(text1, text2):
    return 100 * editdistance.eval(text1, text2) / numpy.average([len(text1), len(text2)])


def are_same(id1, id2, db_handler):
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
    print(db_handler.get_entity_by_id(entity11_id), db_handler.get_action_by_id(action1_id),
          db_handler.get_entity_by_id(entity12_id))
    print(db_handler.get_entity_by_id(entity21_id), db_handler.get_action_by_id(action2_id),
          db_handler.get_entity_by_id(entity22_id))

    return True


def auto_merge():
    global MERGE_PROGRESS
    global settings
    db_new_handler = DatabaseHandler()

    last_id = settings.get_last_processed_event_id()

    old_ids = db_new_handler.get_event_ids_to(last_id)
    new_ids = db_new_handler.get_event_ids_from(last_id + 1)

    old_count = len(old_ids)
    new_count = len(new_ids)

    MERGE_PROGRESS = 0
    total_count = new_count * old_count + (new_count * (new_count - 1)) / 2
    count = 0

    for i1 in range(0, new_count):
        for i2 in range(0, old_count):
            if are_same(new_ids[i1], old_ids[i2], db_new_handler):
                db_new_handler.add_events_to_events_merge(new_ids[i1], old_ids[i2])

            count += 1
            MERGE_PROGRESS = 100 * count / total_count

        for i2 in range(i1 + 1, new_count):
            if are_same(new_ids[i1], new_ids[i2], db_new_handler):
                db_new_handler.add_events_to_events_merge(new_ids[i1], new_ids[i2])

            count += 1
            MERGE_PROGRESS = 100 * count / total_count

    MERGE_PROGRESS = 100
    if new_count > 0:
        settings.put_last_processed_event_id(new_ids[new_count - 1])


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


@app.route('/events', methods=['GET', 'POST'])
def events():
    return render_template("events.html")


@app.route('/sources', methods=['GET', 'POST'])
def articles():
    articles = db_handler.get_sites()

    return render_template("sources.html", articles=articles)


@app.route('/merge', methods=['GET', 'POST'])
def statistics():
    return render_template("merge.html")


@app.route('/_search_events', methods=['GET'])
def search_events():
    return redirect(url_for('events', query=request.args['query']))



fetch_progress = {}


@app.route('/_fetch_articles', methods=['POST'])
def fetch_articles():

    site_name = request.form.get('site_name', '', type=str)
    last_date = [t[1] for t in db_handler.get_sites() if t[0] == site_name][0]

    def fetch():
        db = DatabaseHandler()
        for downloader in article_downloaders:
            if site_name in downloader.site_names:
                for article in downloader.get_articles_by_site_name(site_name):
                    if article.publish_date >= last_date:
                        db.add_article_or_get_id(article)
                        fetch_progress[site_name] = article.publish_date
                    else:
                        break
        fetch_progress.pop(site_name)
    fetch_thread = Thread(target=fetch)
    fetch_thread.start()
    return jsonify(result=None, error=None)


@app.route('/_get_fetch_info', methods=['POST'])
def get_fetch_info():
    return jsonify(result=fetch_progress, error=None)