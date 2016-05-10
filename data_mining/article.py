_known_sites = {'jetbrains.com': 'JetBrains',
                'microsoft.com': 'Microsoft',
                'apple.com': 'Apple',
                'apache.org': 'Apache',
                'mozilla.org': 'Mozilla',
                'djangoproject.com': 'Django'}

class Article:
    def __init__(self, raw_text="", header="", summary="", text="", site_name="", url="", author_name="",
                 publish_date=None):
        url_base = '.'.join(url.split('.')[-2:]).split('/')[0]

        self.raw_text = raw_text
        self.header = header
        self.summary = summary
        self.text = text
        self.site_name = url_base
        self.url = url
        self.author_name = author_name
        self.publish_date = publish_date
        self.site_owner = _known_sites.get(url_base)
