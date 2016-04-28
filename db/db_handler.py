import configparser
import psycopg2
from urllib.parse import urlparse
from event import Event

class DatabaseHandler:
    _CONFIG_NAME = 'config.cfg'
    _VERSION = 2

    def __init__(self):
        config = configparser.ConfigParser()
        config.read(DatabaseHandler._CONFIG_NAME)
        login = config['db']['login']
        password = config['db']['password']
        host = config['db']['host']
        self.connection = psycopg2.connect("dbname=event_database user={} password={} host={}"
                                           .format(login, password, host))
        self.cursor = self.connection.cursor()
        version = None
        try:
            self.cursor.execute("SELECT version FROM settings")
            version = self.cursor.fetchone()
        except:  #just an old version of db without settings table
            self.connection.rollback()
        if version is not None:
            version = version[0]

        if version is None or version != DatabaseHandler._VERSION:
            self.clear_db()

    def clear_db(self):
        for table_name in ['articles', 'entities', 'actions', 'events', 'event_sources', 'settings', 'dates']:
            self.cursor.execute("DROP TABLE IF EXISTS {0} CASCADE".format(table_name))
            self.connection.commit()

        self.connection.set_isolation_level(0)
        with open('db/create.sql') as create:
            self.cursor.execute(str(create.read()))
            self.connection.commit()
        self.connection.set_isolation_level(1)
        self.cursor.execute("INSERT INTO settings (version) VALUES (%s)", (DatabaseHandler._VERSION,))
        self.connection.commit()

    def get_article_id(self, article):
        self.cursor.execute("SELECT id FROM articles WHERE url=(%s)", (article.url,))
        return self.cursor.fetchone()

    def add_article_or_get_id(self, article):
        article_id = self.get_article_id(article)
        if article_id is None:
            self.cursor.execute("""INSERT INTO articles (plain_text, raw_text, publish_date, site_name, url, annotation,
            author, caption) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                                (article.text, article.raw_text, article.publish_date, article.site_name,
                                 article.url, article.summary, article.author_name, article.header))
            self.connection.commit()
            return self.cursor.fetchone()[0]
        else:
            return article_id[0]

    def add_entity_or_get_id(self, entity_name):
        self.cursor.execute("SELECT id FROM entities WHERE entity_name=(%s)", (entity_name,))
        entity_id = self.cursor.fetchone()
        if entity_id is None:
            self.cursor.execute("INSERT INTO entities (entity_name) VALUES (%s) RETURNING id", (entity_name,))
            self.connection.commit()
            return self.cursor.fetchone()[0]
        else:
            return entity_id[0]

    def add_action_or_get_id(self, action_name):
        self.cursor.execute("SELECT id FROM actions WHERE action_name=(%s)", (action_name,))
        action_id = self.cursor.fetchone()
        if action_id is None:
            self.cursor.execute("INSERT INTO actions (action_name) VALUES (%s) RETURNING id", (action_name,))
            self.connection.commit()
            return self.cursor.fetchone()[0]
        else:
            return action_id[0]

    def add_date_or_get_id(self, date):
        self.cursor.execute("SELECT id FROM dates WHERE date=(%s)", (date,))

        date_id = self.cursor.fetchone()
        if date_id is None:
            self.cursor.execute("INSERT INTO dates (date) VALUES (%s) RETURNING id", (date,))
            self.connection.commit()
            return self.cursor.fetchone()[0]
        else:
            return date_id[0]

    def add_event_or_get_id(self, event, article):
        entity1_id = self.add_entity_or_get_id(event.entity1)
        action_id = self.add_action_or_get_id(event.action)
        entity2_id = self.add_entity_or_get_id(event.entity2)
        sentence = event.sentence
        date = self.add_date_or_get_id(event.date)

        self.cursor.execute("""SELECT id FROM events WHERE entity1=(%s) AND entity2=(%s) AND action=(%s)
                            AND sentence=(%s) AND date=(%s)""",
                                       (entity1_id, entity2_id, action_id, sentence, date))
        event_id = self.cursor.fetchone()
        if event_id is None:
            self.cursor.execute("INSERT INTO events (entity1, entity2, action, sentence, date) "
                                "VALUES (%s, %s, %s, %s, %s) RETURNING id",
                                (entity1_id, entity2_id, action_id, sentence, date))
            self.connection.commit()
            event_id = self.cursor.fetchone()[0]
            self.cursor.execute("INSERT INTO event_sources (source_id, event_id) VALUES (%s, %s)",
                                (self.add_article_or_get_id(article), event_id))
            self.connection.commit()
        else:
            event_id = event_id[0]
        return event_id

    def del_event_by_id(self, event_id):
        #update sets
        self.del_event_from_set(event_id)

        self.cursor.execute("""DELETE FROM event_sources WHERE event_id=(%s)""", (event_id,))
        self.cursor.execute("""DELETE FROM events WHERE id=(%s)""", (event_id,))

        self.connection.commit()
        # TODO: remove needless articles

    def get_events_starting_from(self, count, start_date):
        self.cursor.execute("""SELECT event.id, entity1.entity_name, entity2.entity_name, action.action_name,
        event.sentence, date.date
        FROM events event
        INNER JOIN event_sources source ON source.event_id = event.id
        INNER JOIN articles article ON article.id = source.source_id
        INNER JOIN entities entity1 ON entity1.id = event.entity1
        INNER JOIN entities entity2 ON entity2.id = event.entity2
        INNER JOIN actions action ON action.id = event.action
        INNER JOIN dates date ON date.id = event.date
        WHERE article.publish_date <= %s
        ORDER BY article.publish_date DESC, event.id LIMIT %s""", (start_date, count))

        events = []
        for raw_event in self.cursor.fetchall():
            events.append(Event(raw_event[1], raw_event[2], raw_event[3], raw_event[4], raw_event[5], id=raw_event[0]))
        return events

    def get_sites(self):
        self.cursor.execute("""SELECT article.site_name, MAX(article.publish_date) FROM articles article
        WHERE article.publish_date IS NOT NULL GROUP BY article.site_name""")
        return self.cursor.fetchall()

    def get_event_by_id(self, event_id):
        self.cursor.execute("""SELECT event.id, entity1.entity_name, entity2.entity_name, action.action_name,
        event.sentence, date.date
        FROM events event
        INNER JOIN event_sources source ON source.event_id = event.id
        INNER JOIN articles article ON article.id = source.source_id
        INNER JOIN entities entity1 ON entity1.id = event.entity1
        INNER JOIN entities entity2 ON entity2.id = event.entity2
        INNER JOIN actions action ON action.id = event.action
        INNER JOIN dates date ON date.id = event.date
        WHERE event.id=%s""", (event_id,))
        raw_event = self.cursor.fetchone()
        return Event(raw_event[1], raw_event[2], raw_event[3], raw_event[4], raw_event[5], id=raw_event[0])

    def get_event_publish_date(self, event_id):
        self.cursor.execute("""SELECT article.publish_date FROM events event
        INNER JOIN event_sources source ON source.event_id = event.id
        INNER JOIN articles article ON article.id = source.source_id
        WHERE event.id = %s""", (event_id,))
        return self.cursor.fetchone()[0]

    def get_event_source(self, event_id):
        self.cursor.execute("""SELECT article.url FROM events event
        INNER JOIN event_sources source ON source.event_id = event.id
        INNER JOIN articles article ON article.id = source.source_id
        WHERE event.id = %s""", (event_id,))
        return self.cursor.fetchone()[0]

    def change_event(self, event_id, new_event):
        id1 = self.add_entity_or_get_id(new_event.entity1)
        id2 = self.add_entity_or_get_id(new_event.entity2)
        action_id = self.add_action_or_get_id(new_event.action)
        date_id = self.add_date_or_get_id(new_event.date)
        self.cursor.execute("""UPDATE events SET entity1=%s, entity2=%s, action=%s, sentence=%s, date=%s
        WHERE id=%s""", (id1, id2, action_id, new_event.sentence, date_id, event_id))
        self.connection.commit()

    #TODO: check 'del_action' and 'del_entity' (add set update)

    def get_set_for_event_by_id(self, table, event_id):
        self.cursor.execute("""SELECT parent_id FROM """ + table + """ WHERE child_id=%s""", (event_id,))
        result = self.cursor.fetchone()
        if result is None:
            return event_id
        return result[0]

    def join(self, table, ids):
        if len(ids) > 1:
            for id in ids:
                self.join_two(table, id, ids[0])

    def join_two(self, table, event1_id, event2_id):
        event1_id = self.get_set_for_event_by_id(table, event1_id)
        event2_id = self.get_set_for_event_by_id(table, event2_id)

        if event1_id != event2_id:
            self.cursor.execute("""INSERT INTO """ + table + """ (child_id, parent_id) VALUES (%s, %s) """, (event1_id, event2_id))
            self.cursor.execute("""UPDATE """ + table + """ SET parent_id=%s WHERE parent_id=%s""", (event2_id, event1_id))
            self.connection.commit()

    def del_from_set(self, table, event_id):
        self.cursor.execute("""SELECT child_id FROM """ + table + """ WHERE parent_id=%s""", (event_id,))
        result = self.cursor.fetchall()
        if len(result) > 0:
            self.cursor.execute("""DELETE FROM """ + table + """ WHERE parent_id=%s""", (event_id,))
            self.connection.commit()
            self.join(table, result)
        else:
            self.cursor.execute("""DELETE FROM """ + table + """ WHERE child_id=%s""", (event_id,))
            self.connection.commit()

    def get_event_set_for_event_by_id(self, event_id):
        return self.get_set_for_event_by_id("events_sets", event_id)

    def join_events(self, ids):
        self.join("events_sets", ids)

    def del_event_from_set(self, event_id):
        self.del_from_set("events_sets", event_id)

    def get_entity_set_for_event_by_id(self, event_id):
        return self.get_set_for_event_by_id("entities_sets", event_id)

    def join_entities_by_events(self, ids, mod):
        entities_ids = []
        for id in ids:
            self.cursor.execute("""SELECT entity""" + mod + """ FROM events WHERE id=%s""", (id,))
            entities_ids.append(self.cursor.fetchone()[0])
        self.join("entities_sets", entities_ids)

    def del_entity_from_set(self, event_id):
        self.del_from_set("entities_sets", event_id)

    def get_action_set_for_event_by_id(self, event_id):
        return self.get_set_for_event_by_id("actions_sets", event_id)

    def join_actions_by_events(self, ids):
        actions_ids = []
        for id in ids:
            self.cursor.execute("""SELECT action FROM events WHERE id=%s""", (id,))
            actions_ids.append(self.cursor.fetchone()[0])
        self.join("actions_sets", actions_ids)

    def del_action_from_set(self, event_id):
        self.del_from_set("actions_sets", event_id)