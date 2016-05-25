import tweepy
from newspaper import Article as NewspaperArticle
from data_mining.article import Article as DataMiningArticle
import re
import configparser
from .article_downloader import ArticleDownloader


class TwitterDownloader(ArticleDownloader):
    _CONFIG_NAME = 'config.cfg'

    @staticmethod
    def get_articles():
        config = configparser.ConfigParser()
        config.read(TwitterDownloader._CONFIG_NAME)
        key = config['twitter']['consumer_key']
        secret = config['twitter']['consumer_secret']

        auth = tweepy.OAuthHandler(key, secret)
        api = tweepy.API(auth)
        start_id = None
        while True:
            statuses = []
            if start_id is None:
                statuses = api.list_timeline('Scobleizer', 'tech-news-brands')
            else:
                statuses = api.list_timeline('Scobleizer', 'tech-news-brands', max_id=start_id)
            for status in statuses:
                text = re.sub(r'https?://([\da-z\.-]+)\.([a-z\.]{2,6})([/\w\.-]*)*/?', '', status.text).strip()
                # possible hashtags?
                if len(text) > 10:
                    yield DataMiningArticle(text, text=text, publish_date=status.created_at)
                start_id = status.id
                urls = status.entities['urls']
                if len(urls) == 0:
                    continue
                article = NewspaperArticle(url=status.entities['urls'][0]['expanded_url'], fetch_images=False)
                article.download()
                if not article.is_downloaded:
                    print("Failed to download article:", article.url)
                    continue
                article.parse()
                author = ""
                if len(article.authors) > 0:
                    author = article.authors[0]
                publish_date = status.created_at if article.publish_date is None else article.publish_date
                #  most likely, tweet was made right after the article was published
                yield DataMiningArticle(article.html, article.title, article.summary, article.text,
                                        "", article.canonical_link, author, publish_date)
