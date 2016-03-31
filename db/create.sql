CREATE DATABASE event_database;
\connect event_database;

CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    plain_text TEXT,
    raw_text TEXT,
    publish_date TIMESTAMP,
    url TEXT,
    annotation TEXT,
    author TEXT,
    caption TEXT
);

CREATE TABLE IF NOT EXISTS entities (
    id SERIAL PRIMARY KEY,
    entity_name TEXT
);

CREATE TABLE IF NOT EXISTS actions (
    id SERIAL PRIMARY KEY,
    action_name TEXT
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    entity1 INTEGER REFERENCES entities (id), 
    entity2 INTEGER REFERENCES entities (id),
    action INTEGER REFERENCES actions (id),
    sentence TEXT
);

CREATE TABLE IF NOT EXISTS event_sources (
    source_id INTEGER REFERENCES articles (id),
    event_id INTEGER REFERENCES events (id)
);
