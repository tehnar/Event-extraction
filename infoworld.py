import requests
from bs4 import BeautifulSoup
import pickle
import os
import sys


class Article:
    def __init__(self, header, summary, text, tags, link, author_name):
        self.header = header
        self.summary = summary
        self.text = text
        self.tags = tags
        self.link = link
        self.author_name = author_name

SITE_ADDRESS = 'http://www.infoworld.com'
ARTICLES_PER_PAGE = 200


def get_articles(article_count, save_folder):
    start = 0
    processed_articles = 0
    while article_count > processed_articles:
        r = requests.get(SITE_ADDRESS + '/news?start=' + str(start))
        soup = BeautifulSoup(r.content, 'html.parser')
        article_soups = soup.find_all('div', {'class': 'river-well article'})

        for article_soup in article_soups:
            if processed_articles >= article_count:
                break

            link = article_soup.find('h3').find('a').get('href')
            header = article_soup.find('h3').get_text()
            summary = article_soup.find('h4').get_text()

            soup = BeautifulSoup(requests.get(SITE_ADDRESS + link, stream=False).content, 'html.parser')
            if soup.find('div', itemprop='articleBody') is None or soup.find('ul', itemprop='keywords') is None:
                continue

            text = soup.find('div', itemprop='articleBody').get_text()
            tags = soup.find('ul', itemprop='keywords').get_text()
            author_name = soup.find('span', itemprop='name').get_text()
            with open(os.path.join(save_folder, link.split('/')[-1] + '.pkl'), 'wb') as f:
                pickle.dump(Article(header, summary, text, tags, link, author_name), f)

            processed_articles += 1

            print('\rArticles got: %d/%d' % (processed_articles, article_count), end='', file=sys.stderr)
        start += ARTICLES_PER_PAGE

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print('Usage: python3 infoworld.py [number of articles] [destination folder]')
    else:
        get_articles(int(sys.argv[1]), sys.argv[2])