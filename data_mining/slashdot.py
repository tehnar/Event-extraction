import datetime
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from data_mining.article import Article


class SlashdotDownloader():
    SITE_ADDRESS = 'http://slashdot.org/'
    ARTICLES_PER_PAGE = 15

    @staticmethod
    def extract_tag(tag):
        if tag is not None:
            tag.extract()

    @staticmethod
    def get_articles():
        cur_page = 1
        while True:
            r = requests.get(SlashdotDownloader.SITE_ADDRESS + '/?page=' + str(cur_page))
            soup = BeautifulSoup(r.content, 'html.parser')
            article_soups = soup.find_all('article', {'class': 'fhitem fhitem-story article usermode thumbs grid_24'})
            for article_soup in article_soups:
                link = article_soup.find('span', {'class': 'story-title'}).find('a').get('href')
                header = article_soup.find('span', {'class': 'story-title'}).find('a').get_text()
                summary = ''
                date = article_soup.find('time').get('datetime')

                text = ' '.join(article_soup.find('div', {'class': 'p'}).strings)
                author_name = article_soup.find('span', {'class': 'story-byline'}).get_text().replace('Posted', '').replace('by', '').split()[0]

                yield Article(header=header, summary=summary, text=text,
                              url=urljoin(SlashdotDownloader.SITE_ADDRESS, link),
                              site_name=SlashdotDownloader.SITE_ADDRESS, author_name=author_name,
                              publish_date=datetime.datetime.strptime(date, 'on %A %B %d, %Y @%I:%M%p'))

            cur_page += 1
