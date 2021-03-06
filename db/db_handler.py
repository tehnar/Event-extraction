import configparser
import os
import re
from datetime import datetime

import psycopg2

from data_mining.article import Article
from event import Event
from data_mining.downloaders import article_downloaders


class DatabaseHandler:
    _CONFIG_NAME = 'config.cfg'
    _VERSION = 2

    def __init__(self):
        root_dir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
        config_filename = os.path.join(root_dir, DatabaseHandler._CONFIG_NAME)
        config = configparser.ConfigParser()
        config.read(config_filename)
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
        except:  # just an old version of db without settings table
            self.connection.rollback()
        if version is not None:
            version = version[0]

        if version is None or version != DatabaseHandler._VERSION:
            self.clear_db()

    def clear_db(self):
        for table_name in ['articles', 'entities', 'actions', 'events', 'event_sources', 'settings', 'dates',
                           'entities_sets', 'actions_sets', 'events_merge', 'events_sets']:
            self.cursor.execute("DROP TABLE IF EXISTS {0} CASCADE".format(table_name))
            self.connection.commit()

        self.connection.set_isolation_level(0)
        with open('db/create.sql') as create:
            self.cursor.execute(str(create.read()))
            self.connection.commit()
        self.connection.set_isolation_level(1)
        self.cursor.execute("INSERT INTO settings (version) VALUES (%s)", (DatabaseHandler._VERSION,))
        self.connection.commit()

    def get_article_id(self, article) -> (int,):
        self.cursor.execute("SELECT id FROM articles WHERE url=(%s)", (article.url,))
        return self.cursor.fetchone()

    def add_article_or_get_id(self, article: Article) -> int:
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

    def add_entity_or_get_id(self, entity_name: str) -> int:
        self.cursor.execute("SELECT id FROM entities WHERE entity_name=(%s)", (entity_name,))
        entity_id = self.cursor.fetchone()
        if entity_id is None:
            self.cursor.execute("INSERT INTO entities (entity_name) VALUES (%s) RETURNING id", (entity_name,))
            self.connection.commit()
            return self.cursor.fetchone()[0]
        else:
            return entity_id[0]

    def add_action_or_get_id(self, action_name: str) -> int:
        self.cursor.execute("SELECT id FROM actions WHERE action_name=(%s)", (action_name,))
        action_id = self.cursor.fetchone()
        if action_id is None:
            self.cursor.execute("INSERT INTO actions (action_name) VALUES (%s) RETURNING id", (action_name,))
            self.connection.commit()
            return self.cursor.fetchone()[0]
        else:
            return action_id[0]

    def add_date_or_get_id(self, date: str or datetime) -> int:
        self.cursor.execute("SELECT id FROM dates WHERE date=(%s)", (date,))

        date_id = self.cursor.fetchone()
        if date_id is None:
            self.cursor.execute("INSERT INTO dates (date) VALUES (%s) RETURNING id", (date,))
            self.connection.commit()
            return self.cursor.fetchone()[0]
        else:
            return date_id[0]

    def add_event_or_get_id(self, event: Event, article: Article) -> int:
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

    def del_event_by_id(self, event_id: int) -> int:
        # update sets
        self.del_event_from_set(event_id)

        self.cursor.execute("""DELETE FROM event_sources WHERE event_id=(%s)""", (event_id,))
        self.cursor.execute("""DELETE FROM events_merge WHERE event1_id=(%s) OR event2_id=(%s)""", (event_id,event_id))
        self.cursor.execute("""DELETE FROM events WHERE id=(%s)""", (event_id,))

        self.connection.commit()
        # TODO: remove needless articles

    def get_events_starting_from(self, count: int, start_date: str or datetime,
                                 pattern: str, site_name: str) -> [Event]:
        tokens = [p[0] if p[0] else p[1] for p in re.findall(r'"([^ ][^"]+[^ ])"|([^ "]+)', pattern.replace('+', ' '))]
        pattern = '%' + '%'.join(tokens) + '%'
        self.cursor.execute("""SELECT event.id, entity1.entity_name, entity2.entity_name, action.action_name,
        event.sentence, date.date
        FROM events event
        INNER JOIN event_sources source ON source.event_id = event.id
        INNER JOIN articles article ON article.id = source.source_id
        INNER JOIN entities entity1 ON entity1.id = event.entity1
        INNER JOIN entities entity2 ON entity2.id = event.entity2
        INNER JOIN actions action ON action.id = event.action
        INNER JOIN dates date ON date.id = event.date
        WHERE article.publish_date <= %s AND article.url ILIKE %s AND event.sentence ILIKE %s
        ORDER BY article.publish_date DESC, event.id LIMIT %s""",
                            (start_date, '%' + site_name + '%', pattern, count))

        events = []
        for raw_event in self.cursor.fetchall():
            events.append(Event(self.process_string(raw_event[1]),
                                self.process_string(raw_event[2]),
                                self.process_string(raw_event[3]),
                                self.process_string(raw_event[4]),
                                raw_event[5],
                                id=raw_event[0]))
        return events

    def get_sites(self) -> [(str, datetime, datetime)]:
        articles = []
        for downloader in article_downloaders:
            for site_name in downloader.site_names:
                self.cursor.execute("""SELECT MAX(article.publish_date) FROM articles article
                WHERE article.publish_date IS NOT NULL AND article.site_name = %s""", (site_name,))

                articles.append((site_name, self.cursor.fetchone()[0]))
        return articles

    def get_event_by_id(self, event_id: int) -> Event:
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
        return Event(self.process_string(raw_event[1]),
                     self.process_string(raw_event[2]),
                     self.process_string(raw_event[3]),
                     self.process_string(raw_event[4]),
                     raw_event[5],
                     id=raw_event[0])

    def get_event_publish_date(self, event_id: int) -> datetime:
        self.cursor.execute("""SELECT article.publish_date FROM events event
        INNER JOIN event_sources source ON source.event_id = event.id
        INNER JOIN articles article ON article.id = source.source_id
        WHERE event.id = %s""", (event_id,))
        return self.cursor.fetchone()[0]

    def get_event_source(self, event_id: int) -> Article:
        self.cursor.execute("""SELECT article.raw_text, article.caption, article.annotation, article.plain_text,
        article.url, article.author, article.publish_date
        FROM events event
        INNER JOIN event_sources source ON source.event_id = event.id
        INNER JOIN articles article ON article.id = source.source_id
        WHERE event.id = %s""", (event_id,))
        article = self.cursor.fetchone()
        return Article(article[0], article[1], article[2], article[3], "", article[4], article[5], article[6])

    def change_event(self, event_id: int, new_event: Event):
        id1 = self.add_entity_or_get_id(new_event.entity1)
        id2 = self.add_entity_or_get_id(new_event.entity2)
        action_id = self.add_action_or_get_id(new_event.action)
        date_id = self.add_date_or_get_id(new_event.date)
        self.cursor.execute("""UPDATE events SET entity1=%s, entity2=%s, action=%s, sentence=%s, date=%s
        WHERE id=%s""", (id1, id2, action_id, new_event.sentence, date_id, event_id))
        self.connection.commit()

    # TODO: check 'del_action' and 'del_entity' (add set update)

    def get_set_by_id(self, table: str, id: int) -> int:
        self.cursor.execute("SELECT parent_id FROM " + table + " WHERE child_id=%s", (id,))
        result = self.cursor.fetchone()
        if result is None:
            return id
        return result[0]

    def get_set_ids_by_parent_id(self, table: str, id: int) -> [int]:
        self.cursor.execute("SELECT child_id FROM " + table + " WHERE parent_id=%s", (id,))
        result = self.cursor.fetchall()
        if len(result) == 0:
            return [id]

        ids = []
        for entry in result:
            ids.append(entry[0])
        return ids

    def get_set_ids_by_id(self, table: str, id: int) -> [int]:
        id = self.get_set_by_id(table, id)
        return self.get_set_ids_by_parent_id(table, id)

    def get_events_set_by_id(self, id: int) -> [int]:
        return self.get_set_ids_by_id("events_sets", id)

    def join(self, table: str, root_id: int, ids: [int]):
        if len(ids) > 1:
            for id in ids:
                self.join_two(table, id, root_id)

    def get_entity_len(self, id: int) -> int:
        self.cursor.execute("SELECT entity_name FROM entities WHERE id = %s", (id,))
        return len(self.cursor.fetchone()[0])

    def join_two(self, table: str, event1_id: int, event2_id: int):
        event1_id = self.get_set_by_id(table, event1_id)
        event2_id = self.get_set_by_id(table, event2_id)

        if table == "entities_sets":
            if self.get_entity_len(event1_id) < self.get_entity_len(event2_id):
                event1_id, event2_id = event2_id, event1_id

        if event1_id != event2_id:
            self.cursor.execute("INSERT INTO " + table + " (child_id, parent_id) VALUES (%s, %s) ",
                                (event1_id, event2_id))
            self.cursor.execute("UPDATE " + table + " SET parent_id=%s WHERE parent_id=%s", (event2_id, event1_id))
            self.connection.commit()

    def del_from_set(self, table: str, event_id: int):
        self.cursor.execute("SELECT child_id FROM " + table + " WHERE parent_id=%s", (event_id,))
        result = self.cursor.fetchall()
        if len(result) > 0:
            self.cursor.execute("DELETE FROM  " + table + " WHERE parent_id=%s", (event_id,))
            self.connection.commit()

            if table == "entities_sets":
                result = [(id, self.get_entity_by_id(id)) for id in result]
            elif table == "actions_sets":
                result = [(id, self.get_action_by_id(id)) for id in result]
            else:
                result = [(id, "") for id in result]

            self.join(table, min(result, key=lambda pair: len(pair[1]))[0], list(map(lambda pair: pair[0], result)))
        else:
            self.cursor.execute("DELETE FROM " + table + " WHERE child_id=%s", (event_id,))
            self.connection.commit()

    def get_event_set_for_event_by_id(self, event_id: int) -> int:
        return self.get_set_by_id("events_sets", event_id)

    def join_events(self, ids: [int]) -> int:
        self.join("events_sets", ids[0], ids)

    def del_event_from_set(self, event_id: int):
        self.del_from_set("events_sets", event_id)

    def get_entity_set_by_entity_id(self, entity_id: int) -> int:
        return self.get_set_by_id("entities_sets", entity_id)

    def join_entities_by_events(self, ids: [int], mod: str):
        entities = []
        for id in ids:
            self.cursor.execute("""SELECT entity""" + mod + """ FROM events WHERE id=%s""", (id,))
            entity_id = self.cursor.fetchone()[0]
            entity = self.get_entity_by_id(entity_id)
            entities.append((entity_id, entity))

        self.join("entities_sets", min(entities, key=lambda pair: len(pair[1]))[0],
                  list(map(lambda pair: pair[0], entities)))

    def del_entity_from_set(self, event_id: int) -> int:
        self.del_from_set("entities_sets", event_id)

    def get_action_set_by_action_id(self, action_id: int) -> int:
        return self.get_set_by_id("actions_sets", action_id)

    def join_actions_by_events(self, ids: [int]):
        actions = []
        for id in ids:
            self.cursor.execute("""SELECT action FROM events WHERE id=%s""", (id,))
            action_id = self.cursor.fetchone()[0]
            action = self.get_action_by_id(action_id)
            actions.append((action_id, action))

        self.join("actions_sets", min(actions, key=lambda pair: len(pair[1]))[0],
                  list(map(lambda pair: pair[0], actions)))

    def del_action_from_set(self, event_id: int):
        self.del_from_set("actions_sets", event_id)

    # TODO: fix it
    @staticmethod
    def process_string(text: str) -> str:
        text = ' '.join(text.split())
        text = text.replace(" ’s", "’s")
        text = text.replace("'ll", "will")
        text = text.replace("'ve", "have")
        return text

    def get_entity_by_id(self, id: int) -> str:
        self.cursor.execute("SELECT entity_name FROM entities WHERE id=%s", (id,))
        return self.cursor.fetchone()[0]

    def get_action_by_id(self, id: int) -> str:
        self.cursor.execute("SELECT action_name FROM actions WHERE id=%s", (id,))
        return self.cursor.fetchone()[0]

    def get_entity_core_id_by_event_id(self, id: int) -> (int, int, int):
        self.cursor.execute("SELECT entity1, action, entity2 FROM events WHERE id=%s", (id,))
        event_data = self.cursor.fetchone()
        return event_data[0], event_data[1], event_data[2]

    def get_event_ids_from(self, from_id: int = 0) -> [int]:
        self.cursor.execute("SELECT id FROM events WHERE id>=%s ORDER BY id", (from_id,))
        ids = []

        if self.cursor.rowcount > 1:
            for id in self.cursor.fetchall():
                ids.append(id[0])
        return ids

    def get_event_ids_to(self, to_id: int = 0) -> [int]:
        self.cursor.execute("SELECT id FROM events WHERE id<=%s ORDER BY id", (to_id,))
        ids = []
        if self.cursor.rowcount > 1:
            for id in self.cursor.fetchall():
                ids.append(id[0])
        return ids

    def add_events_to_events_merge(self, id1: int, id2: int):
        self.cursor.execute("INSERT INTO events_merge (event1_id, event2_id) VALUES (%s, %s)", (id1, id2))
        self.connection.commit()

    def get_events_merge(self) -> [(int, int, int)]:
        self.cursor.execute("SELECT id, event1_id, event2_id FROM events_merge")
        data = []

        if self.cursor.rowcount > 1:
            for entry in self.cursor.fetchall():
                data.append((entry[0], entry[1], entry[2]))
        return data

    def get_event_merge_by_id(self, id: int) -> (int, int):
        self.cursor.execute("SELECT event1_id, event2_id FROM events_merge WHERE id=%s", (id,))
        data = self.cursor.fetchone()
        return data[0], data[1]

    def del_event_merge_by_id(self, id: int):
        self.cursor.execute("DELETE FROM events_merge WHERE id=%s", (id,))
        self.connection.commit()

    def get_articles(self) -> [Article]:
        self.cursor.execute("SELECT * FROM articles")
        return list(map(lambda t: Article(t[2], t[8], t[6], t[1], "blog.jetbrains.com", t[5], t[7], t[3]),
                        self.cursor.fetchall()))

    def get_main_entity_core_by_event_id(self, id: int) -> (int, int, int):
        entity1, action, entity2 = self.get_entity_core_id_by_event_id(id)
        entity1 = self.get_entity_set_by_entity_id(entity1)
        action = self.get_action_set_by_action_id(action)
        entity2 = self.get_entity_set_by_entity_id(entity2)
        return self.get_entity_by_id(entity1), self.get_action_by_id(action), self.get_entity_by_id(entity2)
