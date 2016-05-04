from data_mining.article import Article as DataMiningArticle
import os
import newspaper
import newspaper.settings


class BlogsDownloader:
    @staticmethod
    def get_articles():
        for url in open('blogs.txt', 'r').readlines():
            url = url.strip()
            for file in os.listdir(newspaper.settings.ANCHOR_DIRECTORY):  # clearing newspaper categories cache
                os.unlink(os.path.join(newspaper.settings.ANCHOR_DIRECTORY, file))
            articles = newspaper.build(url)
            for article in articles.articles:
                article.download()
                if not article.is_downloaded:
                    print("Failed to download article:", article.url)
                    continue
                article.parse()
                yield DataMiningArticle(article.html, article.title, article.summary, article.text,
                                        "", article.canonical_link, "", article.publish_date)
