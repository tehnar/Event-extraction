article_downloaders = []


class ArticleDownloaderMeta(type):
    def __new__(mcs, classname, bases, classdict):
        downloader = super(ArticleDownloaderMeta, mcs).__new__(mcs, classname, bases, classdict)
        if classname != "ArticleDownloader":
            article_downloaders.append(downloader)
        return downloader


class ArticleDownloader(metaclass=ArticleDownloaderMeta):
    @staticmethod
    def get_articles():
        raise NotImplementedError
