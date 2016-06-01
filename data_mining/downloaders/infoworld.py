from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup
from dateutil import parser as date_parser

from data_mining.article import Article
from .article_downloader import ArticleDownloader


class InfoworldDownloader(ArticleDownloader):
    site_name = ['infoworld.com']
    SITE_ADDRESS = 'http://www.infoworld.com'
    ARTICLES_PER_PAGE = 200

    @staticmethod
    def extract_tag(tag):
        if tag is not None:
            tag.extract()

    @staticmethod
    def get_articles():
        start = 0
        while True:
            r = requests.get(InfoworldDownloader.SITE_ADDRESS + '/news?start=' + str(start))
            soup = BeautifulSoup(r.content, 'html.parser')
            article_soups = soup.find_all('div', {'class': 'river-well article'})

            for article_soup in article_soups:
                link = article_soup.find('h3').find('a').get('href')
                header = article_soup.find('h3').get_text()
                summary = article_soup.find('h4').get_text()
                soup = BeautifulSoup(requests.get(InfoworldDownloader.SITE_ADDRESS + link).content, 'html.parser')
                if soup.find('div', itemprop='articleBody') is None or soup.find('ul', itemprop='keywords') is None:
                    continue

                author_name = soup.find('span', itemprop='name').get_text()
                date = soup.find('span', itemprop='datePublished').get('content')
                text = ''

                while True:
                    InfoworldDownloader.extract_tag(soup.find('aside'))  # probably we don't need comments for an images
                    InfoworldDownloader.extract_tag(soup.find('figure', {'class': 'fakesidebar'}))
                    # get rid of text ads

                    text += ' '.join(soup.find('div', itemprop='articleBody').strings)
                    next_page_link = soup.find('a', {'class': 'page-link next'})

                    if next_page_link is None:
                        break

                    soup = BeautifulSoup(requests.get(InfoworldDownloader.SITE_ADDRESS +
                                                      next_page_link.get('href')).content, 'html.parser')
                yield Article(header=header, summary=summary, text=text,
                              publish_date=date_parser.parse(date),
                              site_name=InfoworldDownloader.SITE_ADDRESS,
                              url=urljoin(InfoworldDownloader.SITE_ADDRESS, link), author_name=author_name)

            start += InfoworldDownloader.ARTICLES_PER_PAGE
