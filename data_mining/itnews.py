import requests
from bs4 import BeautifulSoup
import pickle
import os
import sys
import time
from .article import Article


SITE_ADDRESS = 'http://www.itnews.com/'
ARTICLES_PER_PAGE = 200


def extract_tag(tag):
    if tag is not None:
        tag.extract()


def get_articles(article_count, save_folder, start=0):
    processed_articles = 0
    
    r = requests.get(SITE_ADDRESS + '/news')
    soup = BeautifulSoup(r.content, 'html.parser')
    article_soups = soup.find_all('div', {'class': 'river-well article'})

    for article_soup in article_soups:
        if processed_articles >= article_count:
            break

        link = SITE_ADDRESS + article_soup.find('h3').find('a').get('href')
        header = article_soup.find('h3').get_text()
        summary = article_soup.find('h4').get_text()
        tags = None
        
        soup = BeautifulSoup(requests.get(link).content, 'html.parser')
        if soup.find('div', itemprop='articleBody') is None:
            continue

        tags = soup.find('div', {'class': 'apart-alt tags'}).find('ul', itemprop='keywords').get_text()
        author_name = soup.find('span', itemprop='name').get_text()
        
        text = ''
        paragraphs = soup.find('div', itemprop='articleBody').find_all('p')
        for paragraph in paragraphs:
            text += ' '.join(paragraph.strings)
        
        with open(os.path.join(save_folder, link.split('/')[-1] + '.pkl'), 'wb') as f:
            pickle.dump(Article(header, summary, text, tags, link, author_name), f)

        processed_articles += 1

        print('\rArticles got: %d/%d' % (processed_articles, article_count), end='', file=sys.stderr)
 
if __name__ == '__main__':
    if len(sys.argv) not in [3, 4]:
        print('Usage: python3 infoworld.py {number of articles} {destination folder} [number of articles to skip]')
    else:
        start = int(sys.argv[3]) if len(sys.argv) == 4 else 0
        get_articles(int(sys.argv[1]), sys.argv[2], start)