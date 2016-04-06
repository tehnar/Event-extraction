import configparser
import psycopg2
from urllib.parse import urlparse

class DatabaseHandler:
    _CONFIG_NAME = 'config.cfg'

    def __init__(self):
        config = configparser.ConfigParser()
        config.read(DatabaseHandler._CONFIG_NAME)
        login = config['db']['login']
        password = config['db']['password']
        host = config['db']['host']
        self.connection = psycopg2.connect("dbname=event_database user={} password={} host={}"
                                           .format(login, password, host))
        self.cursor = self.connection.cursor()

    def add_article_or_get_id(self, article):
        self.cursor.execute("SELECT id FROM articles WHERE url=(%s)", (article.url,))
        article_id = self.cursor.fetchone()
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

    def add_event_or_get_id(self, event, article):
        entity1_id = self.add_entity_or_get_id(event[0])
        action_id = self.add_action_or_get_id(event[1])
        entity2_id = self.add_entity_or_get_id(event[2])
        sentence = event[3]
        self.cursor.execute("SELECT id FROM events WHERE entity1=(%s) and entity2=(%s) and action=(%s) and sentence=(%s)",
                                       (entity1_id, entity2_id, action_id, sentence))
        event_id = self.cursor.fetchone()
        if event_id is None:
            self.cursor.execute("INSERT INTO events (entity1, entity2, action, sentence) VALUES (%s, %s, %s, %s) RETURNING id",
                                (entity1_id, entity2_id, action_id, sentence))
            self.connection.commit()
            event_id = self.cursor.fetchone()[0]
            self.cursor.execute("INSERT INTO event_sources (source_id, event_id) VALUES (%s, %s)",
                                (self.add_article_or_get_id(article), event_id))
            self.connection.commit()
        else:
            event_id = event_id[0]
        return event_id

    def del_event_by_id(self, event_id):
        self.cursor.execute("""DELETE FROM event_sources WHERE event_id=(%s)""", (event_id,))
        self.cursor.execute("""DELETE FROM events WHERE id=(%s)""", (event_id,))
        # TODO: remove needless articles

    def get_events_starting_from(self, count, start_date):
        self.cursor.execute("""SELECT event.id, article.publish_date, entity1.entity_name, entity2.entity_name, action.action_name, event.sentence
        FROM events event
        INNER JOIN event_sources source ON source.event_id = event.id
        INNER JOIN articles article ON article.id = source.source_id
        INNER JOIN entities entity1 ON entity1.id = event.entity1
        INNER JOIN entities entity2 ON entity2.id = event.entity2
        INNER JOIN actions action ON action.id = event.action
        WHERE article.publish_date IS NOT NULL AND article.publish_date <= %s
        ORDER BY article.publish_date DESC LIMIT %s""", (start_date, count))

        return self.cursor.fetchall()  # TODO: need to deal with NULL publish_date

    def get_sites(self):
        self.cursor.execute("""SELECT article.site_name, MAX(article.publish_date) FROM articles article
        WHERE article.publish_date IS NOT NULL GROUP BY article.site_name""")
        return self.cursor.fetchall()