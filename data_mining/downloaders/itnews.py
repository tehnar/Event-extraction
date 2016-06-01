from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from data_mining.article import Article
from .article_downloader import ArticleDownloader

class ItNewsDownloader(ArticleDownloader):
    site_names = ['itnews.com']
    SITE_ADDRESS = 'http://www.itnews.com/'
    ARTICLES_PER_PAGE = 200

    @staticmethod
    def extract_tag(tag):
        if tag is not None:
            tag.extract()

    @staticmethod
    def get_articles():
        r = requests.get(ItNewsDownloader.SITE_ADDRESS + '/news')
        soup = BeautifulSoup(r.content, 'html.parser')
        article_soups = soup.find_all('div', {'class': 'river-well article'})

        for article_soup in article_soups:
            link = ItNewsDownloader.SITE_ADDRESS + article_soup.find('h3').find('a').get('href')
            header = article_soup.find('h3').get_text()
            summary = article_soup.find('h4').get_text()

            soup = BeautifulSoup(requests.get(link).content, 'html.parser')
            if soup.find('div', itemprop='articleBody') is None:
                continue

            author_name = soup.find('span', itemprop='name').get_text()
            date = soup.find('span', itemprop='datePublished').get('content')
            text = ''
            paragraphs = soup.find('div', itemprop='articleBody').find_all('p')
            for paragraph in paragraphs:
                text += ' '.join(paragraph.strings)

            yield Article(header=header, summary=summary, text=text, url=urljoin(ItNewsDownloader.SITE_ADDRESS, link),
                          site_name=ItNewsDownloader.SITE_ADDRESS, author_name=author_name,
                          publish_date=date_parser.parse(date))