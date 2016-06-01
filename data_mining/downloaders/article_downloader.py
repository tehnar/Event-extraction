article_downloaders = []


class ArticleDownloaderMeta(type):
    def __new__(mcs, classname, bases, classdict):
        downloader = super(ArticleDownloaderMeta, mcs).__new__(mcs, classname, bases, classdict)
        if classname != "ArticleDownloader":
            article_downloaders.append(downloader)
        return downloader


class ArticleDownloader(metaclass=ArticleDownloaderMeta):
    site_names = []  # to be overwritten in subclasses

    @staticmethod
    def get_articles():
        raise NotImplementedError

    # some downloaders may support more that one site
    @classmethod
    def get_articles_by_site_name(cls, site_name: str):
        return cls.get_articles()