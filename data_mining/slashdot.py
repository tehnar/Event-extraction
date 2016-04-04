import requests
from bs4 import BeautifulSoup
import pickle
import os
import sys
import math
from urllib.parse import urljoin
from .article import Article
from dateutil import parser as date_parser


SITE_ADDRESS = 'http://slashdot.org/'
ARTICLES_PER_PAGE = 15


def extract_tag(tag):
    if tag is not None:
        tag.extract()


def get_articles(article_count, save_folder, start=0):
    processed_articles = 0
    cur_page = math.ceil(start / ARTICLES_PER_PAGE)
    while article_count > processed_articles:
        r = requests.get(SITE_ADDRESS + '/?page=' + str(cur_page))
        soup = BeautifulSoup(r.content, 'html.parser')
        article_soups = soup.find_all('article', {'class': 'fhitem fhitem-story article usermode thumbs grid_24'})
        for article_soup in article_soups:
            if processed_articles >= article_count:
                break
            link = article_soup.find('span', {'class': 'story-title'}).find('a').get('href')
            header = article_soup.find('span', {'class': 'story-title'}).find('a').get_text()
            summary = ''
            date = article_soup.find('time').get('datetime')[3:-9]

            text = ' '.join(article_soup.find('div', {'class': 'p'}).strings)
            author_name = article_soup.find('span', {'class': 'story-byline'}).get_text().replace('Posted', '').replace('by', '').split()[0]

            with open(os.path.join(save_folder, link.split('/')[-1] + '.pkl'), 'wb') as f:
                pickle.dump(Article(header=header, summary=summary, text=text, url=urljoin(SITE_ADDRESS, link),
                                    author_name=author_name, publish_date=date_parser.parse(date)), f)

            processed_articles += 1

            print('\rArticles got: %d/%d' % (processed_articles, article_count), end='', file=sys.stderr)
        cur_page += 1


if __name__ == '__main__':
    if len(sys.argv) not in [3, 4]:
        print('Usage: python3 infoworld.py {number of articles} {destination folder} [number of articles to skip]')
    else:
        start = int(sys.argv[3]) if len(sys.argv) == 4 else 0
        get_articles(int(sys.argv[1]), sys.argv[2], start)