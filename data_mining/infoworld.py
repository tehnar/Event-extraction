import requests
from bs4 import BeautifulSoup
import pickle
import os
import sys
from .article import Article
from urllib.parse import urljoin

SITE_ADDRESS = 'http://www.infoworld.com'
ARTICLES_PER_PAGE = 200


def extract_tag(tag):
    if tag is not None:
        tag.extract()


def get_articles(article_count, save_folder, start=0):
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

            soup = BeautifulSoup(requests.get(SITE_ADDRESS + link).content, 'html.parser')
            if soup.find('div', itemprop='articleBody') is None or soup.find('ul', itemprop='keywords') is None:
                continue

            author_name = soup.find('span', itemprop='name').get_text()

            text = ''

            while True:
                extract_tag(soup.find('aside'))  # probably we don't need comments for an images
                extract_tag(soup.find('figure', {'class': 'fakesidebar'}))  # get rid of text ads

                text += ' '.join(soup.find('div', itemprop='articleBody').strings)
                next_page_link = soup.find('a', {'class': 'page-link next'})

                if next_page_link is None:
                    break

                soup = BeautifulSoup(requests.get(SITE_ADDRESS + next_page_link.get('href')).content, 'html.parser')

            with open(os.path.join(save_folder, link.split('/')[-1] + '.pkl'), 'wb') as f:
                pickle.dump(Article(header=header, summary=summary, text=text,
                                    url=urljoin(SITE_ADDRESS, link), author_name=author_name), f)

            processed_articles += 1

            print('\rArticles got: %d/%d' % (processed_articles, article_count), end='', file=sys.stderr)
        start += ARTICLES_PER_PAGE

if __name__ == '__main__':
    if len(sys.argv) not in [3, 4]:
        print('Usage: python3 infoworld.py {number of articles} {destination folder} [number of articles to skip]')
    else:
        start = int(sys.argv[3]) if len(sys.argv) == 4 else 0
        get_articles(int(sys.argv[1]), sys.argv[2], start)