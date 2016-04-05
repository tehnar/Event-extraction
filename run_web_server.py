#!/usr/bin/env python3
import web_ui

from web_ui import app
from threading import Thread
import time
from data_mining import ArticleDownloader
from db import DatabaseHandler

from spacy_event_extractor import SpacyEventExtractor
def parse_articles_in_background():
    db_handler = DatabaseHandler()

    while True:
        for downloader in ArticleDownloader.downloaders:
            for article in downloader.get_articles():
                if db_handler.get_article_id(article) is not None:
                    break
                db_handler.add_article_or_get_id(article)
                events = SpacyEventExtractor.extract(article.summary)
                events += SpacyEventExtractor.extract(article.text)
                for event in events:
                    db_handler.add_event_or_get_id(event, article)
                    
        time.sleep(60)


Thread(target=parse_articles_in_background).start()
app.run(debug=True)
