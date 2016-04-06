from data_mining.developerandeconomics import DevAndEconomicsDownloader
from data_mining.infoworld import InfoworldDownloader
from data_mining.slashdot import SlashdotDownloader
from data_mining.itnews import ItNewsDownloader


class ArticleDownloader:
    _known_sites = {'http://www.developereconomics.com': DevAndEconomicsDownloader,
                    'http://www.infoworld.com': InfoworldDownloader,
                    'http://slashdot.org/': SlashdotDownloader,
                    'http://www.itnews.com/': ItNewsDownloader}

    downloaders = [DevAndEconomicsDownloader, InfoworldDownloader, SlashdotDownloader, ItNewsDownloader]

    # generator for articles
    @staticmethod
    def get_articles():
        pass

    @staticmethod
    def get_downloader_by_site(url):
        return ArticleDownloader._known_sites[url]()
