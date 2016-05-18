import requests
from data_mining.article import Article as DataMiningArticle
from newspaper import Article as NewspaperArticle
import os
import newspaper
import newspaper.settings
from bs4 import BeautifulSoup


class BlogsDownloader:
    @staticmethod
    def get_articles():
        for url in open('blogs.txt', 'r').readlines():
            url = url.strip()
            for file in os.listdir(newspaper.settings.ANCHOR_DIRECTORY):  # clearing newspaper categories cache
                os.unlink(os.path.join(newspaper.settings.ANCHOR_DIRECTORY, file))
            articles = newspaper.build(url).articles
            if url.split('.')[1] == 'jetbrains':  # at least for now. Newspaper is a bit buggy on JetBrains site
                articles = []
                for page in range(10):
                    soup = BeautifulSoup(requests.get(url + '/page/' + str(page)).content, 'html.parser')
                    for title in soup.find_all('h2', {'class': 'entry-title'}):
                        articles.append(NewspaperArticle(title.find('a').get('href')))
            for article in articles:
                article.download()
                if not article.is_downloaded:
                    print("Failed to download article:", article.url)
                    continue
                article.parse()
                article.nlp()
                publish_date = article.publish_date
                if publish_date is None and url.split('.')[1] == 'jetbrains':
                    soup = BeautifulSoup(requests.get(article.url).content, 'html.parser')
                    publish_date = soup.find('span', {'class': 'entry-date'}).getText()
                    # actually, newspaper is very buggy on JetBrains blog and often cannot parse publish date
                print(publish_date)
                yield DataMiningArticle(article.html, article.title, article.summary, article.text,
                                        "", article.canonical_link, "", publish_date)
