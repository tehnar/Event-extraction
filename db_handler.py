import configparser
import psycopg2


class DatabaseHandler:

    def __init__(self):
        config = configparser.ConfigParser()
        config.read('config.cfg')
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
            self.cursor.execute("""INSERT INTO articles (plain_text, raw_text, publish_date, url, annotation, author,
            caption) VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                                (article.text, article.raw_text, article.publish_date, article.url, article.summary,
                                 article.author_name, article.header))
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
        self.cursor.execute("SELECT id FROM events WHERE entity1=(%s) and entity2=(%s) and action=(%s)",
                                       (entity1_id, entity2_id, action_id))
        event_id = self.cursor.fetchone()
        if event_id is None:
            self.cursor.execute("INSERT INTO events (entity1, entity2, action) VALUES (%s, %s, %s) RETURNING id",
                                (entity1_id, entity2_id, action_id))
            self.connection.commit()
            event_id = self.cursor.fetchone()[0]
            self.cursor.execute("INSERT INTO event_sources (source_id, event_id) VALUES (%s, %s)",
                                (self.add_article_or_get_id(article), event_id))
            self.connection.commit()
        else:
            event_id = event_id[0]
        return event_id
