import os
import pickle
import sys
from .article import Article
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dateutil import parser as date_parser

SITE_ADDRESS = 'http://www.developereconomics.com'
ARTICLES_PER_PAGE = 200
HEADERS = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate',
   'User-Agent': 'runscope/0.1'
}


def get_articles(article_count, save_folder, start=0):
    page = start // ARTICLES_PER_PAGE + 1
    processed_articles = 0
    while article_count > processed_articles:
        r = requests.get(SITE_ADDRESS + '/news/page/' + str(page), headers=HEADERS)
        soup = BeautifulSoup(r.content, 'html.parser')
        article_soups = soup.find_all('a', text='Read More')
        for article_soup in article_soups:
            if processed_articles == article_count:
                break
            processed_articles += 1
            link = article_soup.get('href')
            soup = BeautifulSoup(requests.get(link, headers=HEADERS).content, 'html.parser')
            date = soup.find('time').get_text()
            summary = soup.find('div', {'itemtype': 'http://schema.org/Article'}).get_text()
            header = soup.find('h1', {'class': 'heading'}).get_text()
            with open(os.path.join(save_folder, link.split('/')[-2] + '.pkl'), 'wb') as f:
                pickle.dump(Article(header=header, summary=summary, url=urljoin(SITE_ADDRESS, link),
                                    publish_date=date_parser.parse(date)), f)

            print('\rArticles got: %d/%d' % (processed_articles, article_count), end='', file=sys.stderr)

        page += 1



if __name__ == '__main__':
    if len(sys.argv) not in [3, 4]:
        print('Usage: python3 infoworld.py {number of articles} {destination folder} [number of articles to skip]')
    else:
        start = int(sys.argv[3]) if len(sys.argv) == 4 else 0
        get_articles(int(sys.argv[1]), sys.argv[2], start)