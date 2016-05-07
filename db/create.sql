CREATE TABLE IF NOT EXISTS articles (
    id SERIAL PRIMARY KEY,
    plain_text TEXT,
    raw_text TEXT,
    publish_date TIMESTAMP,
    site_name TEXT,
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

CREATE TABLE IF NOT EXISTS dates (
    id SERIAL PRIMARY KEY,
    date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    entity1 INTEGER REFERENCES entities (id), 
    entity2 INTEGER REFERENCES entities (id),
    action INTEGER REFERENCES actions (id),
    date INTEGER REFERENCES dates(id),
    sentence TEXT
);

CREATE TABLE IF NOT EXISTS event_sources (
    source_id INTEGER REFERENCES articles (id),
    event_id INTEGER REFERENCES events (id)
);

CREATE TABLE IF NOT EXISTS settings (
    version INTEGER
);

CREATE TABLE IF NOT EXISTS events_sets (
    child_id INTEGER REFERENCES events (id),
    parent_id INTEGER REFERENCES events (id)
);


CREATE TABLE IF NOT EXISTS entities_sets (
    child_id INTEGER REFERENCES entities (id),
    parent_id INTEGER REFERENCES entities (id)
);

CREATE TABLE IF NOT EXISTS actions_sets (
    child_id INTEGER REFERENCES actions (id),
    parent_id INTEGER REFERENCES actions (id)
);

CREATE TABLE IF NOT EXISTS events_merge (
    id1 INTEGER REFERENCES events (id),
    id2 INTEGER REFERENCES events (id)
);