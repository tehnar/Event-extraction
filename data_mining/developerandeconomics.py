from dateutil import parser as date_parser
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from data_mining.article import Article


class DevAndEconomicsDownloader():
    SITE_ADDRESS = 'http://www.developereconomics.com'

    ARTICLES_PER_PAGE = 200
    HEADERS = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
       'User-Agent': 'runscope/0.1'
    }

    @staticmethod
    def get_articles():
        page = 1
        while True:
            r = requests.get(DevAndEconomicsDownloader.SITE_ADDRESS + '/news/page/' + str(page),
                             headers=DevAndEconomicsDownloader.HEADERS)
            soup = BeautifulSoup(r.content, 'html.parser')
            article_soups = soup.find_all('a', text='Read More')
            for article_soup in article_soups:
                link = article_soup.get('href')
                soup = BeautifulSoup(requests.get(link, headers=DevAndEconomicsDownloader.HEADERS).content, 'html.parser')
                date = ':'.join(soup.find('time').get('datetime').split(':')[:-1]) # TODO: use some regexp?
                date = ' '.join(date.split('BST'))
                summary = soup.find('div', {'itemtype': 'http://schema.org/Article'}).get_text()
                header = soup.find('h1', {'class': 'heading'}).get_text()
                yield Article(header=header, summary=summary, url=urljoin(DevAndEconomicsDownloader.SITE_ADDRESS, link),
                              site_name=DevAndEconomicsDownloader.SITE_ADDRESS,
                              publish_date=date_parser.parse(date))

            page += 1